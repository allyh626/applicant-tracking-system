from django.urls import path

from . import views

app_name = "hiring"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("skills/", views.skill_list, name="skill_list"),
    path("candidates/", views.candidate_list, name="candidate_list"),
    path("candidates/new/", views.candidate_create, name="candidate_create"),
    path("candidates/<int:pk>/", views.candidate_detail, name="candidate_detail"),
    path("candidates/<int:pk>/edit/", views.candidate_edit, name="candidate_edit"),
]
