from django.urls import path

from . import views

app_name = "hiring"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("skills/", views.skill_list, name="skill_list"),
]
