# /// script
# requires-python = ">=3.12"
# dependencies = ["django>=5.1"]
# ///
"""THROWAWAY PROTOTYPE - the dashboard (home page after login).

Not the real app: no database, no login, in-memory sample data that resets on
restart. It only shows data from the agreed design (openings, skills,
candidates + source, applications, stage history). Tries out:

  * Stat tiles, pipeline-by-stage counts, source breakdown, recent activity.
  * Openings table with an Open/Closed/All GET filter.
  * HTMX Open/Close toggle: swaps only that row and updates the
    "Open openings" tile (out-of-band swap). Closing doesn't touch applications.

Run:  uv run prototypes/dashboard.py   then open http://127.0.0.1:8000
"""

import sys
from datetime import datetime, timedelta

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
from django.template import engines
from django.urls import path
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

# ---------------------------------------------------------------------------
# Stage + source vocab (same as the agreed design)
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
SOURCES = {
    "website": "Company website",
    "job_board": "Job board",
    "referral": "Referral",
    "other": "Other",
}

# ---------------------------------------------------------------------------
# In-memory sample data
# ---------------------------------------------------------------------------

NOW = datetime.now()

OPENINGS = {
    1: {
        "id": 1,
        "title": "Software Engineer",
        "department": "Engineering",
        "location": "Remote",
        "is_open": True,
        "skills": ["Python", "Django", "SQL"],
    },
    2: {
        "id": 2,
        "title": "Data Analyst",
        "department": "Finance",
        "location": "Amarillo, TX",
        "is_open": True,
        "skills": ["SQL", "Excel", "Communication"],
    },
    3: {
        "id": 3,
        "title": "IT Support Specialist",
        "department": "IT",
        "location": "Canyon, TX",
        "is_open": True,
        "skills": ["Troubleshooting", "Communication"],
    },
    4: {
        "id": 4,
        "title": "Marketing Coordinator",
        "department": "Marketing",
        "location": "Hybrid",
        "is_open": False,
        "skills": ["Writing", "Communication"],
    },
}

# (name, source, archived)
CANDIDATES = {
    1: ("Maria Lopez", "referral", False),
    2: ("James Chen", "job_board", False),
    3: ("Aisha Patel", "website", False),
    4: ("Tom Becker", "job_board", False),
    5: ("Sara Kim", "referral", False),
    6: ("Leo Grant", "website", False),
    7: ("Nina Ford", "other", False),
    8: ("Omar Haddad", "job_board", False),
    9: ("Grace Liu", "website", False),
    10: ("Ben Ortiz", "job_board", True),
}

# (candidate_id, opening_id, stage)
APPLICATIONS = [
    (1, 1, "interview"),
    (2, 1, "screening"),
    (3, 1, "applied"),
    (4, 1, "final_review"),
    (5, 2, "offer"),
    (6, 2, "hired"),
    (7, 2, "rejected"),
    (8, 3, "applied"),
    (9, 3, "screening"),
    (1, 2, "applied"),
    (10, 4, "withdrawn"),
    (3, 4, "interview"),
]

# (minutes ago, candidate, opening, from, to, by)
HISTORY = [
    (12, "Maria Lopez", "Software Engineer", "screening", "interview", "jdoe"),
    (45, "Sara Kim", "Data Analyst", "final_review", "offer", "asmith"),
    (90, "James Chen", "Software Engineer", "applied", "screening", "jdoe"),
    (180, "Nina Ford", "Data Analyst", "screening", "rejected", "asmith"),
    (300, "Leo Grant", "Data Analyst", "offer", "hired", "asmith"),
    (1500, "Tom Becker", "Software Engineer", "interview", "final_review", "jdoe"),
    (2900, "Grace Liu", "IT Support Specialist", "applied", "screening", "mlee"),
]

# ---------------------------------------------------------------------------
# Queries (in the real app these are ORM queries / annotate(Count(...)))
# ---------------------------------------------------------------------------


def active_count(opening_id):
    return sum(1 for _, o, s in APPLICATIONS if o == opening_id and s not in TERMINAL)


def stats():
    return {
        "open_openings": sum(o["is_open"] for o in OPENINGS.values()),
        "total_openings": len(OPENINGS),
        "active_apps": sum(1 for *_, s in APPLICATIONS if s not in TERMINAL),
        "hired": sum(1 for *_, s in APPLICATIONS if s == "hired"),
        "candidates": sum(1 for *_, archived in CANDIDATES.values() if not archived),
        "archived": sum(1 for *_, archived in CANDIDATES.values() if archived),
    }


def stage_counts():
    counts = {s: 0 for s in FORWARD + EXITS}
    for *_, s in APPLICATIONS:
        counts[s] += 1
    return [
        {"value": s, "label": LABELS[s], "count": counts[s], "final": s in TERMINAL}
        for s in FORWARD + EXITS
    ]


def source_counts():
    active = [src for _, src, archived in CANDIDATES.values() if not archived]
    total = len(active) or 1
    return [
        {
            "label": label,
            "count": active.count(key),
            "pct": round(100 * active.count(key) / total),
        }
        for key, label in SOURCES.items()
    ]


def opening_rows(filter_):
    rows = []
    for o in OPENINGS.values():
        if filter_ == "open" and not o["is_open"]:
            continue
        if filter_ == "closed" and o["is_open"]:
            continue
        rows.append({**o, "active": active_count(o["id"])})
    return rows


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

OPEN_TILE = """
<div id="open-tile" class="stat" {% if oob %}hx-swap-oob="true"{% endif %}>
  <div class="stat-title">Open openings</div>
  <div class="stat-value text-primary">{{ s.open_openings }}</div>
  <div class="stat-desc">of {{ s.total_openings }} total</div>
</div>
"""

OPENING_ROW = """
<tr id="opening-{{ o.id }}">
  <td>
    <div class="font-semibold">{{ o.title }}</div>
    <div class="text-sm opacity-60">{{ o.department }} &middot; {{ o.location }}</div>
  </td>
  <td>
    <div class="flex flex-wrap gap-1">
      {% for skill in o.skills %}<span class="badge badge-outline badge-sm">{{ skill }}</span>{% endfor %}
    </div>
  </td>
  <td class="text-center">{{ o.active }}</td>
  <td>
    {% if o.is_open %}<span class="badge badge-success">Open</span>
    {% else %}<span class="badge badge-ghost">Closed</span>{% endif %}
  </td>
  <td>
    <div class="flex gap-2 justify-end">
      <a class="btn btn-sm btn-primary btn-outline" href="#"
         title="Pipeline page &mdash; see prototypes/stage_pipeline.py">Pipeline</a>
      {% if o.is_open %}
        <button class="btn btn-sm btn-ghost"
                hx-post="/openings/{{ o.id }}/toggle/" hx-target="closest tr" hx-swap="outerHTML"
                hx-confirm="Close {{ o.title }}? No new applications can be added. Existing ones ({{ o.active }} active) continue as normal.">
          Close</button>
      {% else %}
        <button class="btn btn-sm btn-ghost"
                hx-post="/openings/{{ o.id }}/toggle/" hx-target="closest tr" hx-swap="outerHTML">
          Reopen</button>
      {% endif %}
    </div>
  </td>
</tr>
"""

PAGE = """<!doctype html>
<html lang="en" data-theme="corporate">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard prototype</title>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com/3.4.10"></script>
  <script src="https://unpkg.com/htmx.org@2.0.3"></script>
</head>
<body class="bg-base-200 min-h-screen" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

  <div class="navbar bg-base-100 shadow px-4">
    <div class="flex-1"><span class="text-xl font-bold">Hiring</span></div>
    <ul class="menu menu-horizontal gap-1">
      <li><a class="active">Dashboard</a></li>
      <li><a class="opacity-50" title="Not in this prototype">Candidates</a></li>
      <li><a class="opacity-50" title="Not in this prototype">Job Openings</a></li>
      <li><a class="opacity-50" title="Not in this prototype">Skills</a></li>
    </ul>
    <div class="ml-4 text-sm opacity-70">demo-staff &middot; <a class="link">Log out</a></div>
  </div>

  <main class="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h1 class="text-2xl font-bold">Dashboard</h1>
      <div class="flex gap-2">
        <a class="btn btn-sm btn-primary" title="Not in this prototype">+ New candidate</a>
        <a class="btn btn-sm" title="Not in this prototype">+ New opening</a>
      </div>
    </div>

    <!-- Stat tiles -->
    <div class="stats stats-vertical md:stats-horizontal shadow w-full bg-base-100">
      {{ open_tile }}
      <div class="stat">
        <div class="stat-title">Active applications</div>
        <div class="stat-value">{{ s.active_apps }}</div>
        <div class="stat-desc">not Hired / Rejected / Withdrawn</div>
      </div>
      <div class="stat">
        <div class="stat-title">Hired</div>
        <div class="stat-value text-success">{{ s.hired }}</div>
        <div class="stat-desc">all time</div>
      </div>
      <div class="stat">
        <div class="stat-title">Candidates</div>
        <div class="stat-value">{{ s.candidates }}</div>
        <div class="stat-desc">+ {{ s.archived }} archived</div>
      </div>
    </div>

    <!-- Pipeline by stage -->
    <div class="card bg-base-100 shadow"><div class="card-body">
      <h2 class="card-title text-base">Applications by stage</h2>
      <div class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        {% for st in stages %}
          <div class="rounded-box border border-base-300 p-3 text-center {% if st.final %}bg-base-200{% endif %}">
            <div class="text-2xl font-bold {% if st.final %}opacity-60{% endif %}">{{ st.count }}</div>
            <div class="text-xs {% if st.final %}opacity-60{% endif %}">{{ st.label }}</div>
          </div>
        {% endfor %}
      </div>
      <p class="text-xs opacity-60">Shaded = final stages. In the real app each box links to a filtered pipeline.</p>
    </div></div>

    <div class="grid lg:grid-cols-3 gap-6">
      <!-- Openings table -->
      <div class="card bg-base-100 shadow lg:col-span-2"><div class="card-body">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h2 class="card-title text-base">Job openings</h2>
          <div role="tablist" class="tabs tabs-boxed tabs-sm">
            {% for key, text in filters %}
              <a role="tab" href="?openings={{ key }}" class="tab {% if key == filter %}tab-active{% endif %}">{{ text }}</a>
            {% endfor %}
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="table">
            <thead><tr><th>Opening</th><th>Required skills</th><th class="text-center">Active apps</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {% for row in opening_rows %}{{ row }}{% empty %}
                <tr><td colspan="5" class="text-center opacity-60">No openings match this filter.</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div></div>

      <div class="space-y-6">
        <!-- Source breakdown -->
        <div class="card bg-base-100 shadow"><div class="card-body">
          <h2 class="card-title text-base">Where candidates come from</h2>
          {% for src in sources %}
            <div>
              <div class="flex justify-between text-sm"><span>{{ src.label }}</span><span class="opacity-70">{{ src.count }}</span></div>
              <progress class="progress progress-primary w-full" value="{{ src.pct }}" max="100"></progress>
            </div>
          {% endfor %}
          <p class="text-xs opacity-60">Active (non-archived) candidates.</p>
        </div></div>

        <!-- Recent activity -->
        <div class="card bg-base-100 shadow"><div class="card-body">
          <h2 class="card-title text-base">Recent stage changes</h2>
          <ul class="text-sm divide-y divide-base-200">
            {% for h in history %}
              <li class="py-2">
                <b>{{ h.candidate }}</b> &rarr; {{ h.to }}
                <div class="text-xs opacity-60">{{ h.opening }} &middot; from {{ h.frm }} &middot; {{ h.by }} &middot; {{ h.at|timesince }} ago</div>
              </li>
            {% endfor %}
          </ul>
        </div></div>
      </div>
    </div>
  </main>
</body>
</html>
"""

engine = engines["django"]
OPEN_TILE_T = engine.from_string(OPEN_TILE)
OPENING_ROW_T = engine.from_string(OPENING_ROW)
PAGE_T = engine.from_string(PAGE)

FILTERS = [("open", "Open"), ("closed", "Closed"), ("all", "All")]

# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def dashboard(request):
    filter_ = request.GET.get("openings", "open")
    if filter_ not in dict(FILTERS):
        filter_ = "open"
    history = [
        {
            "candidate": c,
            "opening": o,
            "frm": LABELS[f],
            "to": LABELS[t],
            "by": by,
            "at": NOW - timedelta(minutes=mins),
        }
        for mins, c, o, f, t, by in HISTORY
    ]
    return HttpResponse(
        PAGE_T.render(
            {
                "s": stats(),
                "open_tile": mark_safe(OPEN_TILE_T.render({"s": stats()})),
                "stages": stage_counts(),
                "sources": source_counts(),
                "history": history,
                "filters": FILTERS,
                "filter": filter_,
                "opening_rows": [
                    mark_safe(OPENING_ROW_T.render({"o": o}))
                    for o in opening_rows(filter_)
                ],
            },
            request,
        )
    )


@require_POST
def toggle_opening(request, opening_id):
    opening = OPENINGS.get(opening_id)
    if opening is None:
        return HttpResponseBadRequest("No such opening")
    # Only the flag changes; applications under it are untouched (design Q7).
    opening["is_open"] = not opening["is_open"]
    row = OPENING_ROW_T.render({"o": {**opening, "active": active_count(opening_id)}})
    tile = OPEN_TILE_T.render({"s": stats(), "oob": True})
    return HttpResponse(row + tile)


urlpatterns = [
    path("", dashboard),
    path("openings/<int:opening_id>/toggle/", toggle_opening),
]

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line([sys.argv[0], *(sys.argv[1:] or ["runserver"])])
