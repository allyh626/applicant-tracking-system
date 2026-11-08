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
    path("candidates/<int:pk>/archive/", views.candidate_archive, name="candidate_archive"),
    path("candidates/<int:pk>/restore/", views.candidate_restore, name="candidate_restore"),
    path("openings/", views.opening_list, name="opening_list"),
    path("openings/new/", views.opening_create, name="opening_create"),
    path("openings/<int:pk>/", views.opening_detail, name="opening_detail"),
    path("openings/<int:pk>/edit/", views.opening_edit, name="opening_edit"),
    path("openings/<int:pk>/close/", views.opening_close, name="opening_close"),
    path("openings/<int:pk>/reopen/", views.opening_reopen, name="opening_reopen"),
    path("openings/<int:pk>/pipeline/", views.opening_pipeline, name="opening_pipeline"),
    path("applications/new/", views.application_create, name="application_create"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("applications/<int:pk>/move/", views.application_move, name="application_move"),
]
