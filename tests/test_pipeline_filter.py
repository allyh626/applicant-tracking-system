"""The pipeline page's stage filter (user story 47)."""

import pytest
from django.urls import reverse

from hiring.models import Application

from .test_pipeline import make_application, make_opening

pytestmark = pytest.mark.django_db

Stage = Application.Stage


def test_the_stage_filter_shows_only_applications_at_that_stage(staff_client):
    opening = make_opening()
    make_application(first_name="Ana", opening=opening, stage=Stage.INTERVIEW)
    make_application(first_name="Ben", opening=opening, stage=Stage.INTERVIEW)
    make_application(first_name="Cara", opening=opening, stage=Stage.APPLIED)
    url = reverse("hiring:opening_pipeline", args=[opening.pk])

    def listed(query):
        response = staff_client.get(url, query)
        return sorted(a.candidate.first_name for a in response.context["applications"])

    assert listed({"stage": "interview"}) == ["Ana", "Ben"]
    assert listed({"stage": "applied"}) == ["Cara"]
    assert listed({}) == ["Ana", "Ben", "Cara"]  # no filter: everyone
    assert listed({"stage": "nonsense"}) == ["Ana", "Ben", "Cara"]  # unknown: everyone


# --- Covered the normal way (not TDD) ---


def pipeline_url(opening):
    return reverse("hiring:opening_pipeline", args=[opening.pk])


def test_the_filter_dropdown_keeps_the_chosen_stage_and_offers_a_clear_link(staff_client):
    opening = make_opening()

    filtered = staff_client.get(pipeline_url(opening), {"stage": "interview"}).content.decode()
    unfiltered = staff_client.get(pipeline_url(opening)).content.decode()

    def stage_dropdown(html):
        return html.split('<select id="stage"', 1)[1].split("</select>", 1)[0]

    assert '<option value="interview" selected>Interview</option>' in stage_dropdown(filtered)
    assert "Clear</a>" in filtered
    assert "selected" not in stage_dropdown(unfiltered)  # "All stages" is the default
    assert "Clear</a>" not in unfiltered


def test_a_filter_with_no_matches_says_so(staff_client):
    application = make_application(Stage.APPLIED)

    html = staff_client.get(pipeline_url(application.opening), {"stage": "offer"}).content.decode()

    assert "No applications at this stage." in html
    assert "No applications for this opening yet." not in html


def test_a_row_moved_out_of_the_filtered_stage_stays_until_refresh(staff_client):
    # Filtered to Applied, Ana is moved to Screening.
    application = make_application(Stage.APPLIED)
    page = pipeline_url(application.opening)
    filtered = staff_client.get(page, {"stage": "applied"}).content.decode()

    # Her buttons replace only her own row with the response: nothing reloads
    # the list, so the filter isn't applied again until the page is refreshed.
    assert 'hx-target="closest tr" hx-swap="outerHTML"' in filtered
    response = staff_client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"to": "screening"},
        HTTP_HX_REQUEST="true",
    )
    # The response is her row at its new stage (not an empty one that would
    # remove her).
    row = response.content.decode().partition("</tr>")[0]
    assert f'<tr id="application-{application.pk}"' in row
    assert "Screening" in row

    # A refresh applies the filter again, and she's gone.
    refreshed = staff_client.get(page, {"stage": "applied"})
    assert list(refreshed.context["applications"]) == []
