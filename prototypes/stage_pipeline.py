# /// script
# requires-python = ">=3.12"
# dependencies = ["django>=5.1"]
# ///
"""THROWAWAY PROTOTYPE - stage moves through the hiring pipeline.

Not the real app: no database, no models, no login. Data lives in memory and
resets when the server restarts. It exists to try out two design decisions:

  1. Stage rules: forward one step at a time; Reject/Withdraw from any active
     stage; Hired/Rejected/Withdrawn are final. Every move writes a history entry.
  2. HTMX: clicking a stage button swaps only that table row (no page reload).

Run the server:   uv run prototypes/stage_pipeline.py
Check the rules:  uv run prototypes/stage_pipeline.py test
"""

import sys
from datetime import datetime

from django.conf import settings

settings.configure(
    DEBUG=True,
    SECRET_KEY="prototype-only-not-secret",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["127.0.0.1", "localhost"],
    MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
    TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates"}],
)

import django

django.setup()

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template import engines
from django.urls import path
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

# ---------------------------------------------------------------------------
# The rules (this part becomes Application.move_to() in the real app)
# ---------------------------------------------------------------------------

FORWARD = ["applied", "screening", "interview", "final_review", "offer", "hired"]
EXITS = ["rejected", "withdrawn"]
TERMINAL = {"hired", "rejected", "withdrawn"}
LABELS = {
    "applied": "Applied",
    "screening": "Screening",
    "interview": "Interview",
    "final_review": "Final Review",
    "offer": "Offer",
    "hired": "Hired",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
}
ALL_STAGES = FORWARD + EXITS


class InvalidTransition(Exception):
    pass


def allowed_moves(stage):
    """Stages an application in `stage` may move to next."""
    if stage in TERMINAL:
        return []
    next_stage = FORWARD[FORWARD.index(stage) + 1]
    return [next_stage, *EXITS]


def move_to(app, new_stage, user):
    """The single entry point for stage changes: check, update, log."""
    if new_stage not in allowed_moves(app["stage"]):
        raise InvalidTransition(
            f"Can't move from {LABELS[app['stage']]} to "
            f"{LABELS.get(new_stage, new_stage)}."
        )
    change = {
        "app_id": app["id"],
        "candidate": app["candidate"],
        "from_stage": app["stage"],
        "to_stage": new_stage,
        "changed_by": user,
        "changed_at": datetime.now(),
    }
    app["stage"] = new_stage
    app["updated_at"] = change["changed_at"]
    HISTORY.append(change)
    return change


# ---------------------------------------------------------------------------
# In-memory sample data for one job opening
# ---------------------------------------------------------------------------

SEED = [
    ("Maria Lopez", "maria@example.com", "applied"),
    ("James Chen", "james@example.com", "screening"),
    ("Aisha Patel", "aisha@example.com", "interview"),
    ("Tom Becker", "tom@example.com", "final_review"),
    ("Sara Kim", "sara@example.com", "offer"),
    ("Leo Grant", "leo@example.com", "hired"),
    ("Nina Ford", "nina@example.com", "rejected"),
]
APPLICATIONS = {}
HISTORY = []


def reset_data():
    APPLICATIONS.clear()
    HISTORY.clear()
    for i, (name, email, stage) in enumerate(SEED, start=1):
        APPLICATIONS[i] = {
            "id": i,
            "candidate": name,
            "email": email,
            "stage": stage,
            "updated_at": datetime.now(),
        }


reset_data()

# ---------------------------------------------------------------------------
# Templates (in the real app these are hiring/templates/... files)
# ---------------------------------------------------------------------------

ROW = """
<tr id="app-{{ app.id }}" class="{% if error %}bg-error/10{% endif %}">
  <td>
    <div class="font-semibold">{{ app.candidate }}</div>
    <div class="text-sm opacity-60">{{ app.email }}</div>
  </td>
  <td><span class="badge {{ badge }}">{{ label }}</span></td>
  <td class="text-sm opacity-70">{{ app.updated_at|time:"H:i:s" }}</td>
  <td>
    <div class="flex flex-wrap gap-2">
      {% for move in moves %}
        <button class="btn btn-sm {{ move.css }}"
                hx-post="/move/{{ app.id }}/"
                hx-vals='{"to": "{{ move.value }}"}'
                hx-target="closest tr" hx-swap="outerHTML"
                {% if move.confirm %}hx-confirm="{{ move.confirm }}"{% endif %}>
          {{ move.text }}
        </button>
      {% empty %}
        <span class="text-sm opacity-60">Final stage &mdash; no moves</span>
      {% endfor %}
    </div>
    {% if error %}<div class="text-error text-sm mt-1">{{ error }}</div>{% endif %}
  </td>
  <td>
    <form class="flex gap-1" hx-post="/move/{{ app.id }}/"
          hx-target="closest tr" hx-swap="outerHTML">
      <select name="to" class="select select-bordered select-xs">
        {% for value, text in all_stages %}<option value="{{ value }}">{{ text }}</option>{% endfor %}
      </select>
      <button class="btn btn-xs btn-ghost">Force</button>
    </form>
  </td>
</tr>
{% if change %}
<div hx-swap-oob="afterbegin:#log">
  <li class="py-1"><span class="opacity-60">{{ change.changed_at|time:"H:i:s" }}</span>
    &middot; <b>{{ change.candidate }}</b>: {{ from_label }} &rarr; {{ to_label }}
    <span class="opacity-60">by {{ change.changed_by }}</span></li>
</div>
{% endif %}
"""

PAGE = """<!doctype html>
<html lang="en" data-theme="corporate">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pipeline prototype</title>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com/3.4.10"></script>
  <script src="https://unpkg.com/htmx.org@2.0.3"></script>
</head>
<body class="bg-base-200 min-h-screen p-6"
      hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
  <div class="max-w-6xl mx-auto space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Software Engineer &mdash; pipeline</h1>
        <p class="opacity-70">Prototype. Page loaded at
          <span class="font-mono font-semibold">{% now "H:i:s" %}</span></p>
        <p class="text-sm opacity-60">This time should <b>not</b> change when you click a
          stage button &mdash; only the row updates, not the whole page.
          (The &ldquo;Stage changed at&rdquo; column <i>should</i> change.)</p>
      </div>
      <form method="post" action="/reset/">{% csrf_token %}
        <button class="btn btn-outline btn-sm">Reset data</button></form>
    </div>

    <form method="get" class="flex gap-2 items-center">
      <select name="stage" class="select select-bordered select-sm">
        <option value="">All stages</option>
        {% for value, text in all_stages %}
          <option value="{{ value }}" {% if value == stage_filter %}selected{% endif %}>{{ text }}</option>
        {% endfor %}
      </select>
      <button class="btn btn-sm">Filter</button>
    </form>

    <div class="card bg-base-100 shadow">
      <div class="overflow-x-auto">
        <table class="table">
          <thead><tr><th>Candidate</th><th>Stage</th><th>Stage changed at</th><th>Actions</th>
            <th title="Sends any stage to the server to prove the server enforces the rules">Server-rule test</th></tr></thead>
          <tbody>{{ rows }}</tbody>
        </table>
      </div>
    </div>

    <div class="card bg-base-100 shadow"><div class="card-body">
      <h2 class="card-title text-base">Stage history (StageChange log)</h2>
      <ul id="log" class="text-sm divide-y divide-base-200">
        {% for c in history %}
          <li class="py-1"><span class="opacity-60">{{ c.changed_at|time:"H:i:s" }}</span>
            &middot; <b>{{ c.candidate }}</b>: {{ c.from_label }} &rarr; {{ c.to_label }}
            <span class="opacity-60">by {{ c.changed_by }}</span></li>
        {% endfor %}
      </ul>
    </div></div>
  </div>
</body>
</html>
"""

engine = engines["django"]
ROW_T = engine.from_string(ROW)
PAGE_T = engine.from_string(PAGE)

BADGES = {
    "hired": "badge-success",
    "rejected": "badge-error",
    "withdrawn": "badge-ghost",
    "offer": "badge-accent",
}


def button_for(stage):
    if stage == "rejected":
        return {
            "value": stage,
            "text": "Reject",
            "css": "btn-error btn-outline",
            "confirm": "Reject this application? This is final.",
        }
    if stage == "withdrawn":
        return {
            "value": stage,
            "text": "Withdraw",
            "css": "btn-ghost",
            "confirm": "Mark as withdrawn? This is final.",
        }
    return {"value": stage, "text": f"Advance to {LABELS[stage]}", "css": "btn-primary"}


def render_row(request, app, error=None, change=None):
    ctx = {
        "app": app,
        "label": LABELS[app["stage"]],
        "badge": BADGES.get(app["stage"], "badge-info"),
        "moves": [button_for(s) for s in allowed_moves(app["stage"])],
        "all_stages": [(s, LABELS[s]) for s in ALL_STAGES],
        "error": error,
        "change": change,
    }
    if change:
        ctx["from_label"] = LABELS[change["from_stage"]]
        ctx["to_label"] = LABELS[change["to_stage"]]
    return ROW_T.render(ctx, request)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def pipeline(request):
    stage_filter = request.GET.get("stage", "")
    apps = [
        a
        for a in APPLICATIONS.values()
        if not stage_filter or a["stage"] == stage_filter
    ]
    rows = "".join(render_row(request, a) for a in apps)
    history = [
        {**c, "from_label": LABELS[c["from_stage"]], "to_label": LABELS[c["to_stage"]]}
        for c in reversed(HISTORY)
    ]
    return HttpResponse(
        PAGE_T.render(
            {
                "rows": mark_safe(rows),
                "history": history,
                "stage_filter": stage_filter,
                "all_stages": [(s, LABELS[s]) for s in ALL_STAGES],
            },
            request,
        )
    )


@require_POST
def move(request, app_id):
    app = APPLICATIONS.get(app_id)
    if app is None:
        return HttpResponseBadRequest("No such application")
    try:
        change = move_to(app, request.POST.get("to", ""), user="demo-staff")
    except InvalidTransition as exc:
        # 200 so HTMX swaps the row in and shows the error inline.
        return HttpResponse(render_row(request, app, error=str(exc)))
    return HttpResponse(render_row(request, app, change=change))


@require_POST
def reset(request):
    reset_data()
    return redirect("/")


urlpatterns = [
    path("", pipeline),
    path("move/<int:app_id>/", move),
    path("reset/", reset),
]

# ---------------------------------------------------------------------------
# Quick rule checks (become real pytest tests later)
# ---------------------------------------------------------------------------


def run_rule_checks():
    def app(stage):
        return {"id": 0, "candidate": "T", "stage": stage, "updated_at": None}

    # Forward one step works, and is logged.
    a = app("applied")
    move_to(a, "screening", "u")
    assert a["stage"] == "screening" and HISTORY[-1]["to_stage"] == "screening"
    # Skipping ahead is blocked.
    for bad in ["interview", "offer", "hired"]:
        try:
            move_to(app("applied"), bad, "u")
            raise AssertionError(f"applied -> {bad} should fail")
        except InvalidTransition:
            pass
    # Moving backward is blocked.
    try:
        move_to(app("interview"), "screening", "u")
        raise AssertionError("backward move should fail")
    except InvalidTransition:
        pass
    # Reject/Withdraw allowed from every active stage.
    for s in FORWARD[:-1]:
        assert set(EXITS) <= set(allowed_moves(s)), s
    # Offer -> Hired is the last forward step.
    assert allowed_moves("offer")[0] == "hired"
    # Final stages allow nothing.
    for s in TERMINAL:
        assert allowed_moves(s) == [], s
    # Failed moves don't write history.
    before = len(HISTORY)
    try:
        move_to(app("hired"), "rejected", "u")
    except InvalidTransition:
        pass
    assert len(HISTORY) == before
    print("All stage-rule checks passed.")


if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        run_rule_checks()
    else:
        from django.core.management import execute_from_command_line

        execute_from_command_line([sys.argv[0], *(sys.argv[1:] or ["runserver"])])
