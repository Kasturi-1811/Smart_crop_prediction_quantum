from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import FarmerProfile


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            FarmerProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, "Your account was created successfully.")
            return redirect("dashboard")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form})


from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"form": None})
