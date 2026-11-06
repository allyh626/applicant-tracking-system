"""Closing, reopening and filtering job openings (user stories 35, 36, 37, 38)."""

import pytest
from django.urls import reverse

from hiring.models import JobOpening

pytestmark = pytest.mark.django_db


def make_opening(title="Data Analyst", is_open=True):
    return JobOpening.objects.create(
        title=title, department="Finance", location="Remote", description="...", is_open=is_open
    )


def test_closing_and_reopening_flip_the_open_flag(staff_client):
    opening = make_opening()
    detail_url = reverse("hiring:opening_detail", args=[opening.pk])

    closed = staff_client.post(reverse("hiring:opening_close", args=[opening.pk]))
    opening.refresh_from_db()
    assert closed.status_code == 302
    assert closed["Location"] == detail_url
    assert opening.is_open is False

    reopened = staff_client.post(reverse("hiring:opening_reopen", args=[opening.pk]))
    opening.refresh_from_db()
    assert reopened.status_code == 302
    assert reopened["Location"] == detail_url
    assert opening.is_open is True


@pytest.mark.parametrize(
    "name, starts_open",
    [("hiring:opening_close", True), ("hiring:opening_reopen", False)],
)
def test_close_and_reopen_refuse_a_get(staff_client, name, starts_open):
    opening = make_opening(is_open=starts_open)

    response = staff_client.get(reverse(name, args=[opening.pk]))

    assert response.status_code == 405
    opening.refresh_from_db()
    assert opening.is_open is starts_open


@pytest.mark.parametrize(
    "query, expected",
    [
        ("?status=open", ["Backend Engineer", "Data Analyst"]),
        ("?status=closed", ["UX Designer"]),
        ("?status=all", ["Backend Engineer", "Data Analyst", "UX Designer"]),
        ("", ["Backend Engineer", "Data Analyst", "UX Designer"]),  # default is All
        ("?status=bogus", ["Backend Engineer", "Data Analyst", "UX Designer"]),
    ],
)
def test_the_status_filter_limits_the_openings_list(staff_client, query, expected):
    make_opening("Data Analyst")
    make_opening("Backend Engineer")
    make_opening("UX Designer", is_open=False)

    response = staff_client.get(reverse("hiring:opening_list") + query)

    assert [o.title for o in response.context["openings"]] == expected


def test_closing_changes_nothing_but_the_flag(staff_client):
    opening = make_opening()
    before = JobOpening.objects.filter(pk=opening.pk).values(
        "title", "department", "location", "description"
    )[0]

    staff_client.post(reverse("hiring:opening_close", args=[opening.pk]))

    after = JobOpening.objects.filter(pk=opening.pk).values(
        "title", "department", "location", "description"
    )[0]
    assert after == before


def test_closing_an_already_closed_opening_keeps_it_closed(staff_client):
    opening = make_opening(is_open=False)

    staff_client.post(reverse("hiring:opening_close", args=[opening.pk]))

    opening.refresh_from_db()
    assert opening.is_open is False


def test_an_open_opening_offers_close_with_a_reassuring_confirmation(staff_client):
    opening = make_opening()

    html = staff_client.get(reverse("hiring:opening_detail", args=[opening.pk])).content.decode()

    assert reverse("hiring:opening_close", args=[opening.pk]) in html
    assert "<dialog" in html  # the close form sits inside a confirmation dialog
    assert "Existing applications will continue as normal" in html
    assert reverse("hiring:opening_reopen", args=[opening.pk]) not in html


def test_a_closed_opening_offers_reopen_without_a_confirmation(staff_client):
    opening = make_opening(is_open=False)

    html = staff_client.get(reverse("hiring:opening_detail", args=[opening.pk])).content.decode()

    assert reverse("hiring:opening_reopen", args=[opening.pk]) in html
    assert reverse("hiring:opening_close", args=[opening.pk]) not in html
    assert "<dialog" not in html


def test_the_status_is_shown_on_the_list_and_detail_pages(staff_client):
    open_one = make_opening("Data Analyst")
    closed_one = make_opening("UX Designer", is_open=False)

    listing = staff_client.get(reverse("hiring:opening_list")).content.decode()
    open_detail = staff_client.get(reverse("hiring:opening_detail", args=[open_one.pk]))
    closed_detail = staff_client.get(reverse("hiring:opening_detail", args=[closed_one.pk]))

    analyst_row = next(r for r in listing.split("<tr")[1:] if "Data Analyst" in r)
    designer_row = next(r for r in listing.split("<tr")[1:] if "UX Designer" in r)
    assert ">Open</span>" in analyst_row and ">Closed</span>" not in analyst_row
    assert ">Closed</span>" in designer_row and ">Open</span>" not in designer_row
    assert b">Open</span>" in open_detail.content
    assert b">Closed</span>" in closed_detail.content


@pytest.mark.parametrize(
    "query, selected", [("", "all"), ("?status=closed", "closed"), ("?status=bogus", "all")]
)
def test_the_filter_form_shows_the_current_choice(staff_client, query, selected):
    response = staff_client.get(reverse("hiring:opening_list") + query)

    assert f'<option value="{selected}" selected>'.encode() in response.content


def test_an_empty_filtered_list_says_so_and_links_to_all(staff_client):
    make_opening("Data Analyst")

    response = staff_client.get(reverse("hiring:opening_list") + "?status=closed")

    assert b"No closed job openings" in response.content
    assert b"No job openings yet" not in response.content


@pytest.mark.parametrize("name", ["hiring:opening_close", "hiring:opening_reopen"])
def test_close_and_reopen_of_an_unknown_opening_is_a_404(staff_client, name):
    assert staff_client.post(reverse(name, args=[999])).status_code == 404


@pytest.mark.parametrize("name", ["hiring:opening_close", "hiring:opening_reopen"])
def test_close_and_reopen_require_login(client, name):
    opening = make_opening(is_open=(name == "hiring:opening_close"))
    url = reverse(name, args=[opening.pk])

    response = client.post(url)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"
    opening.refresh_from_db()
    assert opening.is_open is (name == "hiring:opening_close")  # unchanged
