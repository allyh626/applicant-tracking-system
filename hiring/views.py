from django.shortcuts import redirect, render

from .forms import SkillForm
from .models import Skill


def dashboard(request):
    """Home page after login. A placeholder until Phase 10 builds the real dashboard."""
    return render(request, "hiring/dashboard.html")


def skill_list(request):
    """List every skill alphabetically, with a form to add one."""
    if request.method == "POST":
        # is_valid() also checks the case-insensitive unique constraint, so a
        # duplicate becomes a form error instead of a database crash.
        form = SkillForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("hiring:skill_list")
    else:
        form = SkillForm()
    return render(
        request,
        "hiring/skill_list.html",
        {"skills": Skill.objects.all(), "form": form},
    )
