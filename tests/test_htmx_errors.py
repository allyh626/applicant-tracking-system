"""HTMX buttons when the session has expired, or the request fails."""

import pytest
from django.urls import reverse

from hiring.models import Application, Candidate, JobOpening

pytestmark = pytest.mark.django_db


@pytest.fixture
def application():
    opening = JobOpening.objects.create(
        title="Data Analyst", department="Finance", location="Remote", description="..."
    )
    candidate = Candidate.objects.create(
        first_name="Ana", last_name="Test", email="ana@example.com", source="referral"
    )
    return Application.objects.create(candidate=candidate, opening=opening)


def htmx_headers(current_url=None):
    headers = {"HX-Request": "true"}
    if current_url:
        headers["HX-Current-URL"] = current_url
    return headers


def test_a_logged_out_stage_move_sends_htmx_to_login_and_back_to_the_page(client, application):
    pipeline = reverse("hiring:opening_pipeline", args=[application.opening.pk])

    response = client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"to": "screening"},
        headers=htmx_headers(f"http://testserver{pipeline}?stage=applied"),
    )

    # Not a redirect HTMX would follow and swap into the row: an HX-Redirect,
    # which makes HTMX load the login page as a whole page.
    assert response.status_code == 200
    assert response.content == b""
    assert response["HX-Redirect"] == f"{reverse('login')}?next={pipeline}%3Fstage%3Dapplied"
    application.refresh_from_db()
    assert application.stage == Application.Stage.APPLIED  # nothing moved


def test_a_logged_out_dashboard_close_sends_htmx_to_login(client, application):
    opening = application.opening

    response = client.post(
        reverse("hiring:opening_close", args=[opening.pk]),
        headers=htmx_headers("http://testserver/"),
    )

    assert response["HX-Redirect"] == f"{reverse('login')}?next=/"
    opening.refresh_from_db()
    assert opening.is_open is True  # nothing closed


def test_without_the_current_page_htmx_goes_to_plain_login(client, application):
    response = client.post(
        reverse("hiring:opening_close", args=[application.opening.pk]), headers=htmx_headers()
    )

    assert response["HX-Redirect"] == reverse("login")


def test_a_logged_out_normal_request_still_gets_a_normal_redirect(client):
    response = client.get(reverse("hiring:dashboard"))

    assert response.status_code == 302
    assert "HX-Redirect" not in response


def test_a_logged_in_htmx_request_is_unchanged(staff_client, application):
    response = staff_client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"to": "screening"},
        headers=htmx_headers("http://testserver/"),
    )

    assert response.status_code == 200
    assert "HX-Redirect" not in response
    assert b'<tr id="application-' in response.content


def test_every_page_has_the_htmx_error_message_box(staff_client):
    html = staff_client.get(reverse("hiring:dashboard")).content.decode()

    # Hidden until an HTMX request fails; then the script fills it in and shows it.
    assert '<div id="htmx-error" class="toast toast-end z-50" hidden>' in html
    assert 'addEventListener("htmx:responseError"' in html
    assert 'addEventListener("htmx:sendError"' in html
