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
    path("openings/", views.opening_list, name="opening_list"),
    path("openings/new/", views.opening_create, name="opening_create"),
    path("openings/<int:pk>/", views.opening_detail, name="opening_detail"),
    path("openings/<int:pk>/edit/", views.opening_edit, name="opening_edit"),
]
