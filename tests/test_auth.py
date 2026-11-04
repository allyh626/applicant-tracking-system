"""Login gate and accounts (user stories 1-5)."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_anonymous_request_to_home_redirects_to_login_and_remembers_the_page(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next=/"


def test_logout_post_ends_the_session_and_returns_to_login(staff_client):
    response = staff_client.post(reverse("logout"))

    assert response.status_code == 302
    assert response["Location"] == reverse("login")
    # The session is gone: the home page now sends the user to login again.
    assert staff_client.get("/")["Location"] == f"{reverse('login')}?next=/"


def test_logout_by_get_is_refused(staff_client):
    response = staff_client.get(reverse("logout"))

    assert response.status_code == 405
    assert staff_client.get("/").status_code == 200  # still logged in


def test_login_page_is_open_to_anonymous_users(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b"Log in" in response.content


def test_logging_in_returns_the_user_to_the_page_they_asked_for(client, staff_user):
    response = client.post(
        f"{reverse('login')}?next=/",
        {"username": "staff", "password": "test-pass-123", "next": "/"},
    )

    assert response.status_code == 302
    assert response["Location"] == "/"


def test_logging_in_without_next_lands_on_the_dashboard(client, staff_user):
    response = client.post(reverse("login"), {"username": "staff", "password": "test-pass-123"})

    assert response["Location"] == reverse("hiring:dashboard")


def test_wrong_password_shows_an_error_on_the_login_page(client, staff_user):
    response = client.post(reverse("login"), {"username": "staff", "password": "wrong"})

    assert response.status_code == 200
    assert b"alert-error" in response.content


def test_logged_in_user_sees_the_dashboard_with_a_logout_button(staff_client):
    response = staff_client.get("/")

    assert response.status_code == 200
    assert b"Dashboard" in response.content
    assert f'action="{reverse("logout")}"'.encode() in response.content


def test_admin_can_create_a_staff_account_that_can_log_in(admin_client, client):
    response = admin_client.post(
        reverse("admin:auth_user_add"),
        {
            "username": "newstaff",
            "password1": "a-Strong-pass-42",
            "password2": "a-Strong-pass-42",
            "usable_password": "true",
        },
    )
    assert response.status_code == 302  # saved, redirected to the change page

    assert client.login(username="newstaff", password="a-Strong-pass-42")
    assert client.get("/").status_code == 200
