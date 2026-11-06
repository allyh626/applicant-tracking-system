"""Visiting a POST-only URL in the browser shows a friendly 405 page, not a blank one."""

import pytest
from django.urls import reverse

from hiring.models import JobOpening

pytestmark = pytest.mark.django_db


@pytest.fixture
def opening():
    return JobOpening.objects.create(
        title="Data Analyst", department="Finance", location="Remote", description="..."
    )


def test_a_get_to_close_shows_a_friendly_page_and_changes_nothing(staff_client, opening):
    response = staff_client.get(reverse("hiring:opening_close", args=[opening.pk]))

    assert response.status_code == 405  # still refused
    assert response["Allow"] == "POST"
    html = response.content.decode()
    assert "can only be done with a button" in html
    assert 'class="navbar' in html  # the normal layout, with navigation
    assert f'href="{reverse("hiring:dashboard")}"' in html
    opening.refresh_from_db()
    assert opening.is_open is True


def test_a_get_to_logout_shows_the_friendly_page_and_keeps_you_logged_in(staff_client):
    response = staff_client.get(reverse("logout"))

    assert response.status_code == 405
    assert b"can only be done with a button" in response.content
    assert staff_client.get("/").status_code == 200


def test_logged_out_visitors_still_go_to_login_first(client, opening):
    # The login gate runs before the view, so they never reach the 405 page.
    url = reverse("hiring:opening_close", args=[opening.pk])

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"


def test_htmx_requests_keep_the_plain_405(staff_client, opening):
    # An HTMX request wants a fragment, never a whole page, so it's left alone.
    response = staff_client.get(
        reverse("hiring:opening_close", args=[opening.pk]), HTTP_HX_REQUEST="true"
    )

    assert response.status_code == 405
    assert response.content == b""
