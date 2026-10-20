from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import CustomCreationForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("jobs:job_list")

    form = CustomCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("jobs:job_list")

    return render(request, "signup.html", {"form": form})
