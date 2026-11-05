"""Candidates: create, edit, view, search and filter (user stories 18-22, 24, 25, 31)."""

import pytest
from django.db import IntegrityError
from django.urls import reverse

from hiring.models import Candidate

pytestmark = pytest.mark.django_db

Source = Candidate.Source


def make_candidate(first, last, email, source=Source.JOB_BOARD, **extra):
    return Candidate.objects.create(
        first_name=first, last_name=last, email=email, source=source, **extra
    )


def listed_names(response):
    return {c.full_name for c in response.context["candidates"]}


def test_search_matches_first_name_last_name_or_email_ignoring_capitalisation(staff_client):
    make_candidate("Ana", "Lopez", "ana.lopez@example.com")  # first name matches
    make_candidate("Bob", "Danahy", "bob@example.com")  # last name matches
    make_candidate("Cleo", "Park", "cleo@banana.dev")  # email matches
    make_candidate("Carl", "Smith", "carl@example.com")  # no match

    response = staff_client.get(reverse("hiring:candidate_list"), {"q": "ANA"})

    assert listed_names(response) == {"Ana Lopez", "Bob Danahy", "Cleo Park"}


def test_source_filter_limits_the_list_and_combines_with_search(staff_client):
    make_candidate("Ana", "Lopez", "ana@example.com", Source.REFERRAL)  # both match
    make_candidate("Anika", "Rao", "anika@example.com", Source.JOB_BOARD)  # name only
    make_candidate("Ben", "Ito", "ben@example.com", Source.REFERRAL)  # source only
    url = reverse("hiring:candidate_list")

    source_only = staff_client.get(url, {"source": Source.REFERRAL})
    both = staff_client.get(url, {"source": Source.REFERRAL, "q": "an"})

    assert listed_names(source_only) == {"Ana Lopez", "Ben Ito"}
    assert listed_names(both) == {"Ana Lopez"}


def test_an_unknown_source_value_is_ignored(staff_client):
    make_candidate("Ana", "Lopez", "ana@example.com")

    response = staff_client.get(reverse("hiring:candidate_list"), {"source": "carrier-pigeon"})

    assert listed_names(response) == {"Ana Lopez"}


def test_filters_are_kept_in_the_form_after_submitting(staff_client):
    response = staff_client.get(
        reverse("hiring:candidate_list"), {"q": "lopez", "source": Source.REFERRAL}
    )

    assert b'value="lopez"' in response.content
    assert b'value="referral" selected' in response.content


def test_a_candidate_can_be_created_with_only_the_required_fields(staff_client):
    response = staff_client.post(
        reverse("hiring:candidate_create"),
        {
            "first_name": "Ana",
            "last_name": "Lopez",
            "email": "ana@example.com",
            "source": Source.COMPANY_WEBSITE,
        },
    )

    candidate = Candidate.objects.get()
    assert response["Location"] == reverse("hiring:candidate_detail", args=[candidate.pk])
    assert candidate.phone == candidate.notes == candidate.profile_url == ""
    assert candidate.archived is False


def test_a_candidate_can_be_created_with_every_field_and_the_detail_page_shows_them(
    staff_client,
):
    data = {
        "first_name": "Ana",
        "last_name": "Lopez",
        "email": "ana@example.com",
        "phone": "806-555-0101",
        "source": Source.REFERRAL,
        "source_details": "Referred by Sam in Finance",
        "profile_url": "https://example.com/ana-cv",
        "notes": "Strong SQL background.",
    }

    response = staff_client.post(reverse("hiring:candidate_create"), data, follow=True)

    assert response.status_code == 200
    for value in [*(v for k, v in data.items() if k != "source"), "Referral"]:
        assert value.encode() in response.content


def test_the_create_form_offers_exactly_the_four_sources(staff_client):
    response = staff_client.get(reverse("hiring:candidate_create"))

    choices = [label for value, label in response.context["form"].fields["source"].choices if value]
    assert choices == ["Company Website", "Job Board", "Referral", "Other"]


@pytest.mark.parametrize("missing", ["first_name", "last_name", "email", "source"])
def test_required_fields_are_required(staff_client, missing):
    data = {"first_name": "A", "last_name": "B", "email": "a@example.com", "source": "other"}
    del data[missing]

    response = staff_client.post(reverse("hiring:candidate_create"), data)

    assert response.status_code == 200
    assert response.context["form"].errors[missing]
    assert not Candidate.objects.exists()


def test_a_source_outside_the_four_choices_is_refused(staff_client):
    data = {"first_name": "A", "last_name": "B", "email": "a@example.com", "source": "fax"}

    response = staff_client.post(reverse("hiring:candidate_create"), data)

    assert response.context["form"].errors["source"]
    assert not Candidate.objects.exists()


@pytest.mark.parametrize("submitted", ["ana@example.com", "Ana@Example.COM", " ana@example.com "])
def test_a_duplicate_email_is_refused_with_a_clear_form_error(staff_client, submitted):
    make_candidate("Ana", "Lopez", "ana@example.com")

    response = staff_client.post(
        reverse("hiring:candidate_create"),
        {"first_name": "Ann", "last_name": "L", "email": submitted, "source": "other"},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["email"] == [
        "A candidate with this email already exists."
    ]
    assert b"A candidate with this email already exists." in response.content
    assert Candidate.objects.count() == 1


@pytest.mark.parametrize("duplicate", ["ana@example.com", "ANA@example.com", " ana@example.com"])
def test_the_database_refuses_a_duplicate_email_ignoring_capitalisation_and_spaces(duplicate):
    make_candidate("Ana", "Lopez", "ana@example.com")

    with pytest.raises(IntegrityError):
        make_candidate("Ann", "L", duplicate)


def test_the_email_is_stored_as_typed_and_names_are_trimmed():
    candidate = make_candidate("  Ana ", " Lopez", " Ana.Lopez@Example.com ")

    candidate.refresh_from_db()
    assert (candidate.first_name, candidate.last_name) == ("Ana", "Lopez")
    assert candidate.email == "Ana.Lopez@Example.com"


def test_a_candidate_can_change_the_capitalisation_of_their_own_email(staff_client):
    ana = make_candidate("Ana", "Lopez", "ana@example.com")

    response = staff_client.post(
        reverse("hiring:candidate_edit", args=[ana.pk]),
        {"first_name": "Ana", "last_name": "Lopez", "email": "Ana@Example.com", "source": "other"},
    )

    assert response.status_code == 302
    ana.refresh_from_db()
    assert ana.email == "Ana@Example.com"


def test_editing_a_candidate_saves_the_changes_and_the_detail_page_shows_them(staff_client):
    candidate = make_candidate("Ana", "Lopez", "ana@example.com")

    response = staff_client.post(
        reverse("hiring:candidate_edit", args=[candidate.pk]),
        {
            "first_name": "Ana",
            "last_name": "López",
            "email": "ana@example.com",  # unchanged email is not a "duplicate"
            "phone": "806-555-0199",
            "source": Source.OTHER,
        },
        follow=True,
    )

    candidate.refresh_from_db()
    assert candidate.last_name == "López"
    assert candidate.phone == "806-555-0199"
    assert response.redirect_chain == [
        (reverse("hiring:candidate_detail", args=[candidate.pk]), 302)
    ]
    assert "Ana López".encode() in response.content
    assert b"806-555-0199" in response.content


def test_editing_to_another_candidates_email_is_refused(staff_client):
    make_candidate("Ana", "Lopez", "ana@example.com")
    ben = make_candidate("Ben", "Ito", "ben@example.com")

    response = staff_client.post(
        reverse("hiring:candidate_edit", args=[ben.pk]),
        {"first_name": "Ben", "last_name": "Ito", "email": "ana@example.com", "source": "other"},
    )

    assert b"A candidate with this email already exists." in response.content
    ben.refresh_from_db()
    assert ben.email == "ben@example.com"


def test_an_unknown_candidate_is_a_404(staff_client):
    assert staff_client.get(reverse("hiring:candidate_detail", args=[999])).status_code == 404
    assert staff_client.get(reverse("hiring:candidate_edit", args=[999])).status_code == 404


def test_the_app_pages_have_no_delete_action(staff_client):
    candidate = make_candidate("Ana", "Lopez", "ana@example.com")

    urls = [
        reverse("hiring:candidate_list"),
        reverse("hiring:candidate_create"),
        reverse("hiring:candidate_detail", args=[candidate.pk]),
        reverse("hiring:candidate_edit", args=[candidate.pk]),
    ]
    for url in urls:
        assert b"delete" not in staff_client.get(url).content.lower()


def test_searching_a_full_name_finds_the_candidate(staff_client):
    make_candidate("Ana", "Lopez", "ana@example.com")
    make_candidate("Ana", "Ruiz", "ana.ruiz@example.com")

    response = staff_client.get(reverse("hiring:candidate_list"), {"q": "ana lopez"})

    assert listed_names(response) == {"Ana Lopez"}


@pytest.mark.parametrize("q", ["lopez", "López", "LÓPEZ", "ana lopez", "jose"])
def test_search_ignores_accents_on_either_side(staff_client, q):
    make_candidate("Ana", "López", "ana@example.com")
    make_candidate("José", "Ito", "jito@example.com")
    make_candidate("Carl", "Smith", "carl@example.com")

    response = staff_client.get(reverse("hiring:candidate_list"), {"q": q})

    expected = {"José Ito"} if q == "jose" else {"Ana López"}
    assert listed_names(response) == expected


def test_search_still_works_after_a_candidate_is_edited(staff_client):
    ana = make_candidate("Ana", "Lopez", "ana@example.com")
    staff_client.post(
        reverse("hiring:candidate_edit", args=[ana.pk]),
        {"first_name": "Ana", "last_name": "Ruiz", "email": "ana@example.com", "source": "other"},
    )
    url = reverse("hiring:candidate_list")

    assert listed_names(staff_client.get(url, {"q": "ruiz"})) == {"Ana Ruiz"}
    assert listed_names(staff_client.get(url, {"q": "lopez"})) == set()


def test_an_unknown_source_does_not_count_as_an_active_filter(staff_client):
    response = staff_client.get(reverse("hiring:candidate_list"), {"source": "bogus"})

    assert response.context["source"] == ""
    assert b"No candidates yet" in response.content


def test_a_failed_edit_keeps_the_saved_name_in_the_heading(staff_client):
    make_candidate("Ben", "Ito", "ben@example.com")
    ana = make_candidate("Ana", "Lopez", "ana@example.com")

    response = staff_client.post(
        reverse("hiring:candidate_edit", args=[ana.pk]),
        {"first_name": "Ana", "last_name": "Smith", "email": "ben@example.com", "source": "other"},
    )

    assert b"Edit Ana Lopez" in response.content
    assert b"Edit Ana Smith" not in response.content


def test_the_admin_can_delete_a_candidate(admin_client):
    candidate = make_candidate("Ana", "Lopez", "ana@example.com")

    response = admin_client.post(
        reverse("admin:hiring_candidate_delete", args=[candidate.pk]), {"post": "yes"}
    )

    assert response.status_code == 302
    assert not Candidate.objects.exists()


@pytest.mark.parametrize(
    "name, needs_pk",
    [
        ("hiring:candidate_list", False),
        ("hiring:candidate_create", False),
        ("hiring:candidate_detail", True),
        ("hiring:candidate_edit", True),
    ],
)
def test_candidate_pages_require_login(client, name, needs_pk):
    args = [make_candidate("Ana", "Lopez", "ana@example.com").pk] if needs_pk else []
    url = reverse(name, args=args)

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"
