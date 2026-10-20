from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ApplicationForm, Jobform
from .models import Application, Job


class EmployerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == "employer"


class JobListView(ListView):
    model = Job
    template_name = "job_list.html"
    context_object_name = "all_jobs"
    paginate_by = 12

    def get_queryset(self):
        queryset = Job.objects.select_related("posted_by")
        query = self.request.GET.get("q", "").strip()
        location = self.request.GET.get("location", "").strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(company_name__icontains=query)
                | Q(description__icontains=query)
            )
        if location:
            queryset = queryset.filter(location__iexact=location)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["selected_location"] = self.request.GET.get("location", "").strip()
        context["locations"] = (
            Job.objects.order_by("location")
            .values_list("location", flat=True)
            .distinct()
        )
        context["result_count"] = context["paginator"].count
        return context


class JobDetailView(DetailView):
    model = Job
    template_name = "job_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["already_applied"] = (
            self.request.user.is_authenticated
            and Application.objects.filter(
                job=self.object, applicant=self.request.user
            ).exists()
        )
        context["resume_form"] = ApplicationForm()
        return context


class JobCreateView(EmployerRequiredMixin, CreateView):
    model = Job
    form_class = Jobform
    template_name = "job_form.html"
    success_url = reverse_lazy("jobs:job_list")

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        return super().form_valid(form)


class JobUpdateView(EmployerRequiredMixin, UpdateView):
    model = Job
    form_class = Jobform
    template_name = "job_form.html"
    success_url = reverse_lazy("jobs:job_list")

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


class JobDeleteView(EmployerRequiredMixin, DeleteView):
    model = Job
    template_name = "job_confirm_delete.html"
    success_url = reverse_lazy("jobs:job_list")

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


class MyJobsListView(EmployerRequiredMixin, ListView):
    model = Job
    template_name = "my_jobs.html"
    context_object_name = "my_jobs"

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


@login_required
@require_POST
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.user.role != "seeker" or job.posted_by_id == request.user.pk:
        return HttpResponseForbidden("Only job seekers may apply to another user's job.")
    if Application.objects.filter(job=job, applicant=request.user).exists():
        return redirect(reverse("jobs:job_detail", kwargs={"pk": job.pk}))

    form = ApplicationForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(
            request,
            "job_detail.html",
            {
                "object": job,
                "already_applied": False,
                "resume_form": form,
            },
            status=400,
        )

    Application.objects.create(
        job=job,
        applicant=request.user,
        resume=form.cleaned_data["resume"],
    )
    return redirect(reverse("jobs:job_detail", kwargs={"pk": job.pk}))


class JobApplicantsListView(EmployerRequiredMixin, ListView):
    template_name = "job_applicants.html"
    context_object_name = "applications"

    def get_queryset(self):
        self.job = get_object_or_404(
            Job, pk=self.kwargs["pk"], posted_by=self.request.user
        )
        return Application.objects.filter(job=self.job).select_related("applicant")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["job"] = self.job
        return context


@login_required
def resume_download(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("job"), pk=pk
    )
    is_applicant = application.applicant_id == request.user.pk
    is_job_owner = (
        request.user.role == "employer"
        and application.job.posted_by_id == request.user.pk
    )
    if not (is_applicant or is_job_owner):
        return HttpResponseForbidden("You are not allowed to access this resume.")
    if not application.resume:
        raise Http404("This application does not have a resume attached.")

    return FileResponse(
        application.resume.open("rb"),
        as_attachment=True,
        filename="resume.pdf",
        content_type="application/pdf",
    )


class MyApplicationListsView(LoginRequiredMixin, ListView):
    model = Application
    template_name = "my_applications.html"
    context_object_name = "my_applications"

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).select_related(
            "job"
        )
