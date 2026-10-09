
from django.urls import path
from . import views

urlpatterns = [
    path("", views.yield_prediction, name="yield_prediction"),
    path("history/", views.prediction_history, name="prediction_history"),
]
