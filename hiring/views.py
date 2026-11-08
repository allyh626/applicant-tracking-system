from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ApplicationForm, CandidateForm, JobOpeningForm, SkillForm
from .models import Application, Candidate, JobOpening, Skill, StageChange, StageMoveError
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
    # select_related loads each application's opening in the same query.
    applications = candidate.applications.select_related("opening")
    return render(
        request,
        "hiring/candidate_detail.html",
        {"candidate": candidate, "applications": applications},
    )


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


OPENING_STATUS_CHOICES = [("all", "All"), ("open", "Open"), ("closed", "Closed")]


def opening_list(request):
    """List openings, filtered by ?status=open|closed|all (default all)."""
    status = request.GET.get("status", "all")
    if status not in dict(OPENING_STATUS_CHOICES):
        status = "all"  # an unknown value (old bookmark, typo) means "all"
    # prefetch_related loads every opening's skills in one extra query, instead
    # of one query per row.
    openings = JobOpening.objects.prefetch_related("required_skills")
    if status != "all":
        openings = openings.filter(is_open=(status == "open"))
    return render(
        request,
        "hiring/opening_list.html",
        {"openings": openings, "status": status, "status_choices": OPENING_STATUS_CHOICES},
    )


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


def _set_opening_status(request, pk, is_open):
    """Flip only the open/closed flag. Applications under the opening are untouched."""
    opening = get_object_or_404(JobOpening, pk=pk)
    opening.is_open = is_open
    # update_fields saves just this flag (and the updated time), nothing else.
    opening.save(update_fields=["is_open", "updated_at"])
    return redirect("hiring:opening_detail", pk=opening.pk)


# POST only: a GET (a visited link, a browser prefetch) gets 405 and changes nothing.
@require_POST
def opening_close(request, pk):
    return _set_opening_status(request, pk, is_open=False)


@require_POST
def opening_reopen(request, pk):
    return _set_opening_status(request, pk, is_open=True)


def application_create(request):
    # ?candidate=<pk> and ?opening=<pk> pre-select a choice, so the "Add
    # application" buttons on candidate and opening pages fill one in. Anything
    # that isn't a number is ignored.
    initial = {
        name: int(request.GET[name])
        for name in ("candidate", "opening")
        # isdecimal, not isdigit: "²" is a digit but int() can't read it.
        if request.GET.get(name, "").isdecimal()
    }
    form = ApplicationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        application = form.save()
        # Back to the candidate, whose page lists their applications.
        return redirect("hiring:candidate_detail", pk=application.candidate_id)
    return render(request, "hiring/application_form.html", {"form": form})


def application_detail(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("candidate", "opening"), pk=pk
    )
    # Oldest first: StageChange's default ordering is by time.
    history = application.stage_changes.select_related("changed_by")
    return render(
        request,
        "hiring/application_detail.html",
        {"application": application, "history": history},
    )


RECENT_CHANGES_LIMIT = 20


def opening_pipeline(request, pk):
    """One opening's applications, each with buttons for the moves it allows.

    ?stage=<stage> shows only the applications at that stage.
    """
    opening = get_object_or_404(JobOpening, pk=pk)
    stage = request.GET.get("stage", "")
    if stage not in Application.Stage.values:
        stage = ""  # an unknown value (old bookmark, typo) means "all stages"
    applications = opening.applications.select_related("candidate")
    if stage:
        applications = applications.filter(stage=stage)
    recent_changes = (
        StageChange.objects.filter(application__opening=opening)
        .select_related("application__candidate", "changed_by")
        .order_by("-changed_at", "-pk")[:RECENT_CHANGES_LIMIT]
    )
    return render(
        request,
        "hiring/pipeline.html",
        {
            "opening": opening,
            "applications": applications,
            "recent_changes": recent_changes,
            "stage": stage,
            "stage_choices": Application.Stage.choices,
        },
    )


@require_POST
def application_move(request, pk):
    """HTMX endpoint: move one application, and return only its re-rendered row."""
    application = get_object_or_404(Application.objects.select_related("candidate"), pk=pk)
    context = {"application": application}
    try:
        # Never set the stage here: move_to() checks the rules on the server,
        # whatever the browser sent.
        # The new history entry goes back too, out-of-band (see the row template).
        context["change"] = application.move_to(request.POST.get("to", ""), request.user)
    except StageMoveError as error:
        # Still 200, so HTMX swaps the row in and the message shows inside it.
        context["error"] = str(error)
    return render(request, "hiring/partials/pipeline_row.html", context)


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
