from django.shortcuts import get_object_or_404, redirect, render

from .forms import CandidateForm, JobOpeningForm, SkillForm
from .models import Candidate, JobOpening, Skill
from .search import fold


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


def candidate_list(request):
    """List candidates, filtered by the GET query string so views can be bookmarked."""
    q = request.GET.get("q", "").strip()
    source = request.GET.get("source", "")
    if source not in Candidate.Source.values:
        source = ""  # an unknown value (old bookmark, typo) means "all sources"
    candidates = Candidate.objects.all()
    # Each word must appear somewhere in the name or email, so "ana lopez" finds
    # Ana López. search_text is already lowercased with accents removed, so
    # folding the word the same way ignores capitals and accents.
    for word in q.split():
        candidates = candidates.filter(search_text__contains=fold(word))
    if source:
        # Chained after the search, so a candidate must match both.
        candidates = candidates.filter(source=source)
    return render(
        request,
        "hiring/candidate_list.html",
        {
            "candidates": candidates,
            "q": q,
            "source": source,
            "source_choices": Candidate.Source.choices,
        },
    )


def candidate_create(request):
    form = CandidateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        candidate = form.save()
        return redirect("hiring:candidate_detail", pk=candidate.pk)
    return render(request, "hiring/candidate_form.html", {"form": form})


def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(request, "hiring/candidate_detail.html", {"candidate": candidate})


def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    # Remember the saved name: is_valid() copies the submitted values onto
    # `candidate`, so after a failed edit it would show the unsaved name.
    saved_name = candidate.full_name
    form = CandidateForm(request.POST or None, instance=candidate)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("hiring:candidate_detail", pk=candidate.pk)
    return render(
        request,
        "hiring/candidate_form.html",
        {"form": form, "candidate": candidate, "saved_name": saved_name},
    )


def opening_list(request):
    # prefetch_related loads every opening's skills in one extra query, instead
    # of one query per row.
    openings = JobOpening.objects.prefetch_related("required_skills")
    return render(request, "hiring/opening_list.html", {"openings": openings})


def opening_create(request):
    form = JobOpeningForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # A ModelForm's save() also saves the many-to-many skills.
        opening = form.save()
        return redirect("hiring:opening_detail", pk=opening.pk)
    return render(request, "hiring/opening_form.html", {"form": form})


def opening_detail(request, pk):
    opening = get_object_or_404(JobOpening, pk=pk)
    return render(request, "hiring/opening_detail.html", {"opening": opening})


def opening_edit(request, pk):
    opening = get_object_or_404(JobOpening, pk=pk)
    # Remember the saved title: is_valid() copies the submitted values onto
    # `opening`, so after a failed edit the heading would show the unsaved one.
    saved_title = opening.title
    form = JobOpeningForm(request.POST or None, instance=opening)
    if request.method == "POST" and form.is_valid():
        # save() replaces the skill set with exactly the ones selected.
        form.save()
        return redirect("hiring:opening_detail", pk=opening.pk)
    return render(
        request,
        "hiring/opening_form.html",
        {"form": form, "opening": opening, "saved_title": saved_title},
    )
