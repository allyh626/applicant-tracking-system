from django.contrib import admin

from .models import Application, Candidate, JobOpening, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


# The admin is the only place a candidate can be deleted (the app's own pages
# have no delete action).
@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "email", "source", "archived"]
    list_filter = ["source", "archived"]
    search_fields = ["first_name", "last_name", "email"]


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "location", "is_open"]
    list_filter = ["is_open", "department"]
    search_fields = ["title", "department", "location"]
    # A searchable two-box picker instead of a plain multi-select.
    filter_horizontal = ["required_skills"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["candidate", "opening", "stage", "created_at"]
    list_filter = ["stage", "opening"]
    search_fields = ["candidate__first_name", "candidate__last_name", "candidate__email"]
    # Read-only: a stage change must go through the pipeline (Phase 7), which
    # checks the rules and records who made it. Editing it here would skip both.
    readonly_fields = ["stage"]
