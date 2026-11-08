"""The application detail page and its stage history (user story 56)."""

from datetime import UTC, datetime

import pytest
from django.urls import reverse

from hiring.models import Application, StageChange

from .test_pipeline import make_application

pytestmark = pytest.mark.django_db

Stage = Application.Stage


def test_the_detail_page_lists_every_stage_change_in_time_order(
    staff_client, staff_user, django_user_model
):
    recruiter = django_user_model.objects.create_user(username="recruiter", password="x")
    application = make_application()
    first = application.move_to(Stage.SCREENING, staff_user)
    second = application.move_to(Stage.INTERVIEW, recruiter)
    third = application.move_to(Stage.REJECTED, staff_user)
    # Fixed times, so the page's timestamps can be checked exactly.
    for change, when in [
        (first, datetime(2026, 11, 2, 9, 30, tzinfo=UTC)),
        (second, datetime(2026, 11, 3, 14, 5, tzinfo=UTC)),
        (third, datetime(2026, 11, 4, 16, 45, tzinfo=UTC)),
    ]:
        StageChange.objects.filter(pk=change.pk).update(changed_at=when)

    response = staff_client.get(reverse("hiring:application_detail", args=[application.pk]))

    assert response.status_code == 200
    html = response.content.decode()
    entries = [
        ("Applied &rarr; Screening", "by staff", "Nov 2, 2026, 9:30 a.m."),
        ("Screening &rarr; Interview", "by recruiter", "Nov 3, 2026, 2:05 p.m."),
        ("Interview &rarr; Rejected", "by staff", "Nov 4, 2026, 4:45 p.m."),
    ]
    positions = []
    for stages, user, when in entries:
        # Each entry's stages, user and time appear together, in that order.
        assert stages in html
        start = html.index(stages)
        entry = html[start : html.index("</li>", start)]
        assert user in entry
        assert when in entry
        positions.append(start)
    assert positions == sorted(positions)  # oldest first


# --- Covered the normal way (not TDD) ---


def detail_url(application):
    return reverse("hiring:application_detail", args=[application.pk])


def test_an_application_without_moves_says_so(staff_client):
    application = make_application()

    html = staff_client.get(detail_url(application)).content.decode()

    assert "No stage changes yet." in html
    assert "Ana Lopez: Data Analyst" in html
    assert reverse("hiring:opening_pipeline", args=[application.opening.pk]) in html
    assert reverse("hiring:candidate_detail", args=[application.candidate.pk]) in html


def test_the_detail_page_shows_only_this_applications_history(staff_client, staff_user):
    ana = make_application(first_name="Ana")
    ben = make_application(first_name="Ben", opening=ana.opening)
    ana.move_to(Stage.SCREENING, staff_user)
    ben.move_to(Stage.WITHDRAWN, staff_user)

    html = staff_client.get(detail_url(ana)).content.decode()

    assert "Applied &rarr; Screening" in html
    assert "Withdrawn" not in html


def test_pipeline_rows_link_to_the_application_detail_page(staff_client):
    application = make_application()

    pipeline = reverse("hiring:opening_pipeline", args=[application.opening.pk])
    html = staff_client.get(pipeline).content.decode()

    assert detail_url(application) in html


def test_the_moved_row_still_links_to_the_application_detail_page(staff_client):
    application = make_application()

    response = staff_client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"to": "screening"},
        HTTP_HX_REQUEST="true",
    )

    assert detail_url(application) in response.content.decode()


def test_the_candidate_page_links_to_each_application(staff_client):
    application = make_application()

    candidate_page = reverse("hiring:candidate_detail", args=[application.candidate.pk])
    html = staff_client.get(candidate_page).content.decode()

    assert detail_url(application) in html


def test_an_unknown_application_is_a_404(staff_client):
    response = staff_client.get(reverse("hiring:application_detail", args=[999]))

    assert response.status_code == 404


def test_the_detail_page_requires_login(client):
    url = detail_url(make_application())

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"
