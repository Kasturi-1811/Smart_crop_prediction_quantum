from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.farms.models import Farm
from django.contrib.auth.decorators import login_required
from apps.farms.models import Farm
from apps.predictions.models import YieldPrediction

def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    farms = Farm.objects.filter(owner=request.user)

    recent_predictions = YieldPrediction.objects.filter(
        farmer=request.user
    )[:5]

    return render(request, "core/dashboard.html", {
        "farms": farms,
        "recent_predictions": recent_predictions,
    })