"""The login page says why when someone's session ended without them logging out."""

import pytest
from django.urls import reverse

from config.middleware import SESSION_ENDED_MESSAGE, SESSION_MARKER_COOKIE
from hiring.models import JobOpening

pytestmark = pytest.mark.django_db

MESSAGE = SESSION_ENDED_MESSAGE.encode()


def end_session(client):
    """What an expired or removed session looks like: the login is gone, the marker isn't."""
    client.session.flush()
    client.cookies.pop("sessionid", None)


def test_logging_in_sets_the_marker_cookie(client, staff_user):
    client.post(reverse("login"), {"username": "staff", "password": "test-pass-123"})

    assert client.cookies[SESSION_MARKER_COOKIE].value == "1"


def test_an_ended_session_shows_the_message_on_the_login_page(staff_client):
    staff_client.get(reverse("hiring:dashboard"))  # sets the marker
    end_session(staff_client)

    response = staff_client.get(reverse("hiring:candidate_list"), follow=True)

    assert response.redirect_chain[-1][0].startswith(reverse("login"))
    assert MESSAGE in response.content
    # Shown once: the marker is removed, so the next visit has no message.
    assert staff_client.cookies[SESSION_MARKER_COOKIE].value == ""
    assert MESSAGE not in staff_client.get(reverse("login")).content


def test_an_ended_session_shows_the_message_after_an_htmx_click(staff_client):
    opening = JobOpening.objects.create(
        title="Data Analyst", department="Finance", location="Remote", description="..."
    )
    staff_client.get(reverse("hiring:dashboard"))
    end_session(staff_client)

    response = staff_client.post(
        reverse("hiring:opening_close", args=[opening.pk]),
        headers={"HX-Request": "true", "HX-Current-URL": "http://testserver/"},
    )
    # HTMX then loads the login page it was sent to.
    login_page = staff_client.get(response["HX-Redirect"])

    assert MESSAGE in login_page.content


def test_logging_out_shows_no_message(staff_client):
    staff_client.get(reverse("hiring:dashboard"))

    response = staff_client.post(reverse("logout"), follow=True)

    assert MESSAGE not in response.content
    assert staff_client.cookies[SESSION_MARKER_COOKIE].value == ""
    # Visiting a page afterwards is the normal "please log in", with no message.
    assert MESSAGE not in staff_client.get(reverse("hiring:dashboard"), follow=True).content


def test_someone_who_never_logged_in_sees_no_message(client):
    response = client.get(reverse("hiring:dashboard"), follow=True)

    assert MESSAGE not in response.content
