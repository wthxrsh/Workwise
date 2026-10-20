import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Application, Job


class JobViewTests(TestCase):
    def setUp(self):
        media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        user_model = get_user_model()
        self.employer = user_model.objects.create_user(
            username="employer",
            password="test-password",
            role="employer",
            email="employer@example.com",
        )
        self.other_user = user_model.objects.create_user(
            username="other",
            password="test-password",
            role="seeker",
            email="seeker@example.com",
        )
        self.job = Job.objects.create(
            title="Developer",
            company_name="Example",
            description="Build things",
            location="Remote",
            salary="75000.00",
            posted_by=self.employer,
        )

    def test_homepage_redirects_to_job_list(self):
        response = self.client.get("/")

        self.assertRedirects(response, reverse("jobs:job_list"))

    def test_job_search_filters_by_keyword_and_location(self):
        response = self.client.get(
            reverse("jobs:job_list"),
            {"q": "developer", "location": "remote"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["all_jobs"]), [self.job])

        response = self.client.get(
            reverse("jobs:job_list"),
            {"q": "designer", "location": "remote"},
        )
        self.assertEqual(response.context["result_count"], 0)

    def test_job_creation_assigns_current_user_as_poster(self):
        self.client.force_login(self.employer)

        response = self.client.post(
            reverse("jobs:job_create"),
            {
                "title": "Designer",
                "company_name": "Example",
                "description": "Design things",
                "location": "Remote",
                "salary": "65000.00",
            },
        )

        self.assertRedirects(response, reverse("jobs:job_list"))
        self.assertTrue(
            Job.objects.filter(title="Designer", posted_by=self.employer).exists()
        )

    def test_job_update_and_delete_are_limited_to_poster(self):
        another_employer = get_user_model().objects.create_user(
            username="another-employer",
            password="test-password",
            role="employer",
            email="another@example.com",
        )
        self.client.force_login(another_employer)

        update_response = self.client.get(
            reverse("jobs:job_update", kwargs={"pk": self.job.pk})
        )
        delete_response = self.client.get(
            reverse("jobs:job_delete", kwargs={"pk": self.job.pk})
        )

        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists())

    def test_poster_can_update_and_delete_job(self):
        self.client.force_login(self.employer)

        update_page = self.client.get(
            reverse("jobs:job_update", kwargs={"pk": self.job.pk})
        )
        delete_page = self.client.get(
            reverse("jobs:job_delete", kwargs={"pk": self.job.pk})
        )

        self.assertEqual(update_page.status_code, 200)
        self.assertEqual(delete_page.status_code, 200)
        response = self.client.post(
            reverse("jobs:job_update", kwargs={"pk": self.job.pk}),
            {
                "title": "Senior Developer",
                "company_name": "Example",
                "description": "Build more things",
                "location": "Remote",
                "salary": "85000.00",
            },
        )

        self.assertRedirects(response, reverse("jobs:job_list"))
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Senior Developer")

        response = self.client.post(
            reverse("jobs:job_delete", kwargs={"pk": self.job.pk})
        )

        self.assertRedirects(response, reverse("jobs:job_list"))
        self.assertFalse(Job.objects.filter(pk=self.job.pk).exists())

    def test_applying_twice_creates_only_one_application(self):
        self.client.force_login(self.other_user)

        for _ in range(2):
            response = self.client.post(
                reverse("jobs:apply_to_job", kwargs={"pk": self.job.pk}),
                {
                    "resume": SimpleUploadedFile(
                        "resume.pdf",
                        b"%PDF-1.4\nValid test resume",
                        content_type="application/pdf",
                    )
                },
            )
            self.assertRedirects(
                response, reverse("jobs:job_detail", kwargs={"pk": self.job.pk})
            )

        self.assertEqual(
            Application.objects.filter(job=self.job, applicant=self.other_user).count(),
            1,
        )
        application = Application.objects.get(
            job=self.job, applicant=self.other_user
        )
        self.assertTrue(application.resume.name.endswith(".pdf"))

    def test_application_requires_a_valid_pdf_resume(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("jobs:apply_to_job", kwargs={"pk": self.job.pk}),
            {
                "resume": SimpleUploadedFile(
                    "resume.txt", b"not a pdf", content_type="text/plain"
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            Application.objects.filter(job=self.job, applicant=self.other_user).exists()
        )

        response = self.client.post(
            reverse("jobs:apply_to_job", kwargs={"pk": self.job.pk})
        )
        self.assertEqual(response.status_code, 400)

    def test_job_owner_can_review_applicants_and_download_their_resume(self):
        application = Application.objects.create(
            job=self.job,
            applicant=self.other_user,
            resume=SimpleUploadedFile(
                "resume.pdf",
                b"%PDF-1.4\nCandidate resume",
                content_type="application/pdf",
            ),
        )
        self.client.force_login(self.employer)

        applicants_response = self.client.get(
            reverse("jobs:job_applicants", kwargs={"pk": self.job.pk})
        )
        download_response = self.client.get(
            reverse("jobs:resume_download", kwargs={"pk": application.pk})
        )

        self.assertEqual(applicants_response.status_code, 200)
        self.assertContains(applicants_response, self.other_user.username)
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response["Content-Type"], "application/pdf")
        self.assertIn("attachment", download_response["Content-Disposition"])

        another_employer = get_user_model().objects.create_user(
            username="another-employer",
            password="test-password",
            role="employer",
            email="another@example.com",
        )
        self.client.force_login(another_employer)
        self.assertEqual(
            self.client.get(
                reverse("jobs:resume_download", kwargs={"pk": application.pk})
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("jobs:job_applicants", kwargs={"pk": self.job.pk})
            ).status_code,
            404,
        )

    def test_my_jobs_and_applications_are_scoped_to_current_user(self):
        Application.objects.create(job=self.job, applicant=self.other_user)

        self.client.force_login(self.employer)
        jobs_response = self.client.get(reverse("jobs:my_jobs"))
        self.client.force_login(self.other_user)
        applications_response = self.client.get(reverse("jobs:my_applications"))

        self.assertEqual(jobs_response.status_code, 200)
        self.assertEqual(
            list(jobs_response.context["my_jobs"]), [self.job]
        )
        self.assertEqual(applications_response.status_code, 200)
        self.assertEqual(
            list(applications_response.context["my_applications"]),
            list(Application.objects.filter(applicant=self.other_user)),
        )

    def test_private_views_redirect_anonymous_users_to_login(self):
        response = self.client.get(reverse("jobs:my_jobs"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('jobs:my_jobs')}",
            fetch_redirect_response=False,
        )

        login_response = self.client.get(reverse("login"))
        self.assertEqual(login_response.status_code, 200)

    def test_seeker_cannot_create_a_job_and_employer_cannot_apply(self):
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(reverse("jobs:job_create")).status_code, 403)

        self.client.force_login(self.employer)
        response = self.client.post(
            reverse("jobs:apply_to_job", kwargs={"pk": self.job.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Application.objects.filter(job=self.job, applicant=self.employer).exists()
        )

    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new-seeker",
                "email": "new-seeker@example.com",
                "role": "seeker",
                "password1": "Strong-password-482!",
                "password2": "Strong-password-482!",
            },
        )

        self.assertRedirects(response, reverse("jobs:job_list"))
        new_user = get_user_model().objects.get(username="new-seeker")
        self.assertTrue(new_user.is_authenticated)
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            new_user.pk,
        )

    def test_signup_shows_validation_errors(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "invalid-user",
                "email": "not-an-email",
                "role": "seeker",
                "password1": "bad",
                "password2": "does-not-match",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(username="invalid-user").exists()
        )

    def test_signup_rejects_duplicate_email_case_insensitively(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "duplicate-email-user",
                "email": "EMPLOYER@EXAMPLE.COM",
                "role": "seeker",
                "password1": "Strong-password-482!",
                "password2": "Strong-password-482!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email address already exists.")
        self.assertFalse(
            get_user_model().objects.filter(username="duplicate-email-user").exists()
        )
