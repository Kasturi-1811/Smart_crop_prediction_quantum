
from django.urls import path
from . import views

urlpatterns = [
    path("soil-analysis/", views.soil_analysis, name="soil_analysis"),
    path("crop-recommendation/", views.crop_recommendation, name="crop_recommendation"),
    path("disease-detection/", views.disease_detection, name="disease_detection"),
    path("weather/", views.weather_advisory, name="weather_advisory"),
    path("farm-economics/", views.farm_economics, name="farm_economics"),
    path(
    "soil-photo-analysis/",
    views.soil_photo_analysis,
    name="soil_photo_analysis",
),
path(
    "disease-detection/",
    views.disease_detection,
    name="disease_detection",
),
]
