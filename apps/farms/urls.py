from django.urls import path
from . import views

urlpatterns = [
    path("", views.farm_list, name="farm_list"),
    path("add/", views.farm_create, name="farm_create"),
    path("edit/<int:pk>/", views.farm_edit, name="farm_edit"),
    path("delete/<int:pk>/", views.farm_delete, name="farm_delete"),
    path("economics/", views.farm_economics, name="farm_economics"),
    path(
        "economics/history/",
        views.farm_economics_history,
        name="farm_economics_history",
    ),
]