"""The dashboard overview (user stories 6-11, 16, 17)."""

import re
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from hiring.models import Application, Candidate, JobOpening, StageChange
from hiring.views import DASHBOARD_RECENT_CHANGES_LIMIT

pytestmark = pytest.mark.django_db

Stage = Application.Stage
Source = Candidate.Source


def make_opening(title, is_open=True):
    return JobOpening.objects.create(
        title=title, department="Finance", location="Remote", description="...", is_open=is_open
    )


def make_candidate(first_name, source=Source.REFERRAL, archived=False):
    return Candidate.objects.create(
        first_name=first_name,
        last_name="Test",
        email=f"{first_name.lower()}@example.com",
        source=source,
        archived=archived,
    )


@pytest.fixture
def hiring_data():
    """A known set: 3 openings (2 open), 4 candidates (1 archived), 6 applications.

    Stages are set directly only to arrange the test; the app moves them with move_to().
    """
    analyst = make_opening("Data Analyst")
    engineer = make_opening("Software Engineer")
    designer = make_opening("Designer", is_open=False)
    ana = make_candidate("Ana", Source.REFERRAL)
    ben = make_candidate("Ben", Source.JOB_BOARD)
    cy = make_candidate("Cy", Source.JOB_BOARD)
    dee = make_candidate("Dee", Source.COMPANY_WEBSITE, archived=True)
    for candidate, opening, stage in [
        (ana, analyst, Stage.INTERVIEW),
        (ana, engineer, Stage.HIRED),
        (ben, analyst, Stage.APPLIED),
        (ben, designer, Stage.INTERVIEW),  # still active under a closed opening
        (cy, analyst, Stage.REJECTED),
        (dee, engineer, Stage.WITHDRAWN),
    ]:
        Application.objects.create(candidate=candidate, opening=opening, stage=stage)


def test_totals_match_the_database(staff_client, hiring_data):
    response = staff_client.get(reverse("hiring:dashboard"))

    assert response.context["totals"] == {
        "open_openings": 2,
        "total_openings": 3,
        "active_applications": 3,  # Interview, Applied, Interview
        "hired": 1,
        "active_candidates": 3,
        "archived_candidates": 1,
    }


def test_stage_counts_cover_all_eight_stages_in_order_including_zeros(staff_client, hiring_data):
    response = staff_client.get(reverse("hiring:dashboard"))

    counts = [
        (row["stage"], row["count"], row["final"]) for row in response.context["stage_counts"]
    ]
    assert counts == [
        (Stage.APPLIED, 1, False),
        (Stage.SCREENING, 0, False),
        (Stage.INTERVIEW, 2, False),
        (Stage.FINAL_REVIEW, 0, False),
        (Stage.OFFER, 0, False),
        (Stage.HIRED, 1, True),
        (Stage.REJECTED, 1, True),
        (Stage.WITHDRAWN, 1, True),
    ]


def test_source_counts_include_only_active_candidates_and_every_source(staff_client, hiring_data):
    response = staff_client.get(reverse("hiring:dashboard"))

    counts = [(row["source"], row["count"]) for row in response.context["source_counts"]]
    assert counts == [
        (Source.COMPANY_WEBSITE, 0),  # Dee came from the website, but is archived
        (Source.JOB_BOARD, 2),
        (Source.REFERRAL, 1),
        (Source.OTHER, 0),
    ]


def test_the_page_shows_the_totals(staff_client, hiring_data):
    content = staff_client.get(reverse("hiring:dashboard")).content.decode()

    # Each stat tile: its title, its big number, and its small description.
    tiles = {
        title: (value, desc)
        for title, value, desc in re.findall(
            r'stat-title">([^<]+)<.*?stat-value[^"]*">(\d+)<.*?stat-desc">([^<]+)<',
            content,
            re.DOTALL,
        )
    }
    assert tiles == {
        "Open openings": ("2", "of 3 total"),
        "Active applications": ("3", "not Hired, Rejected or Withdrawn"),
        "Hired": ("1", "all time"),
        "Active candidates": ("3", "1 archived"),
    }


def test_only_the_final_stages_are_styled_as_final(staff_client, hiring_data):
    content = staff_client.get(reverse("hiring:dashboard")).content.decode()

    final_boxes = re.findall(
        r'class="[^"]*stage-final[^"]*">\s*<div[^>]*>\d+</div>\s*<div[^>]*>([^<]+)</div>', content
    )
    assert final_boxes == ["Hired", "Rejected", "Withdrawn"]


def test_recent_stage_changes_are_newest_first_up_to_the_limit(staff_client, staff_user):
    application = Application.objects.create(
        candidate=make_candidate("Ana"), opening=make_opening("Data Analyst")
    )
    # Twelve real moves would need a longer pipeline, so write the log rows directly.
    start = timezone.now() - timedelta(hours=1)
    changes = [
        StageChange.objects.create(
            application=application,
            from_stage=Stage.APPLIED,
            to_stage=Stage.SCREENING,
            changed_by=staff_user,
            changed_at=start + timedelta(minutes=minute),
        )
        for minute in range(DASHBOARD_RECENT_CHANGES_LIMIT + 2)
    ]

    response = staff_client.get(reverse("hiring:dashboard"))

    expected = list(reversed(changes))[:DASHBOARD_RECENT_CHANGES_LIMIT]
    assert list(response.context["recent_changes"]) == expected


def test_a_recent_change_shows_candidate_opening_stages_user_and_time(staff_client, staff_user):
    application = Application.objects.create(
        candidate=make_candidate("Ana"), opening=make_opening("Data Analyst")
    )
    application.move_to(Stage.SCREENING, staff_user)

    content = staff_client.get(reverse("hiring:dashboard")).content.decode()

    assert "Ana Test" in content
    assert "(Data Analyst)" in content
    assert "Applied &rarr; Screening" in content
    assert "by staff" in content
    assert "ago" in content


def test_an_empty_database_shows_zeros_and_no_changes(staff_client):
    response = staff_client.get(reverse("hiring:dashboard"))

    assert set(response.context["totals"].values()) == {0}
    assert [row["count"] for row in response.context["stage_counts"]] == [0] * 8
    assert b"No stage changes yet." in response.content
