from django.urls import path

from .views import (
    JobCreateView,
    JobDeleteView,
    JobDetailView,
    JobApplicantsListView,
    JobListView,
    JobUpdateView,
    MyApplicationListsView,
    MyJobsListView,
    apply_to_job,
    resume_download,
)

app_name = "jobs"

urlpatterns = [
    path("", JobListView.as_view(), name="job_list"),
    path("create/", JobCreateView.as_view(), name="job_create"),
    path("mine/", MyJobsListView.as_view(), name="my_jobs"),
    path("applications/", MyApplicationListsView.as_view(), name="my_applications"),
    path("applications/<int:pk>/resume/", resume_download, name="resume_download"),
    path("<int:pk>/", JobDetailView.as_view(), name="job_detail"),
    path("<int:pk>/update/", JobUpdateView.as_view(), name="job_update"),
    path("<int:pk>/delete/", JobDeleteView.as_view(), name="job_delete"),
    path("<int:pk>/applicants/", JobApplicantsListView.as_view(), name="job_applicants"),
    path("<int:pk>/apply/", apply_to_job, name="apply_to_job"),
]
