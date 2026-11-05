from django.contrib import admin

from .models import Candidate, Skill


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
