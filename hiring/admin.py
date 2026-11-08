from django import forms
from django.contrib import admin

from .models import Application, Candidate, JobOpening, Skill, StageChange


class CandidateAdminForm(forms.ModelForm):
    """Lets the admin restore a candidate, but not archive one with active applications.

    No Meta: the admin fills in the model and fields when it builds the form.
    """

    def clean_archived(self):
        archived = self.cleaned_data["archived"]
        candidate = self.instance
        # Only newly ticking the box is checked; unticking (restore) is always fine.
        if archived and not candidate.archived and candidate.pk:
            active = candidate.active_application_count()
            if active:
                raise forms.ValidationError(candidate.archive_refusal_message(active))
        return archived


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
    form = CandidateAdminForm


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "location", "is_open"]
    list_filter = ["is_open", "department"]
    search_fields = ["title", "department", "location"]
    # A searchable two-box picker instead of a plain multi-select.
    filter_horizontal = ["required_skills"]


class StageChangeInline(admin.TabularInline):
    """An application's stage history, shown read-only on its admin page.

    History is append-only, so it can't be added, edited or deleted here. It is
    an inline rather than its own admin page on purpose: deleting a candidate
    in the admin must still be able to cascade to their history.
    """

    model = StageChange
    fields = ["changed_at", "from_stage", "to_stage", "changed_by"]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["candidate", "opening", "stage", "stage_changed_at", "created_at"]
    list_filter = ["stage", "opening"]
    search_fields = ["candidate__first_name", "candidate__last_name", "candidate__email"]
    # Read-only: a stage change must go through the pipeline, which checks the
    # rules and records who made it. Editing it here would skip both.
    readonly_fields = ["stage", "stage_changed_at"]
    inlines = [StageChangeInline]
