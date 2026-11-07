"""Creating applications (user stories 23, 39, 44, 45)."""

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from hiring.models import Application, Candidate, JobOpening

pytestmark = pytest.mark.django_db

NEW_URL = reverse("hiring:application_create")


def make_candidate(first_name="Ana", email="ana@example.com"):
    return Candidate.objects.create(
        first_name=first_name, last_name="Lopez", email=email, source=Candidate.Source.REFERRAL
    )


def make_opening(title="Data Analyst", is_open=True):
    return JobOpening.objects.create(
        title=title, department="Finance", location="Remote", description="...", is_open=is_open
    )


def test_a_crafted_post_with_a_closed_opening_is_refused(staff_client):
    candidate = make_candidate()
    closed = make_opening(is_open=False)

    response = staff_client.post(NEW_URL, {"candidate": candidate.pk, "opening": closed.pk})

    assert response.status_code == 200  # the form is shown again, not a redirect
    assert "closed" in " ".join(response.context["form"].errors["opening"])
    assert not Application.objects.exists()


def test_a_second_application_to_the_same_opening_is_refused(staff_client):
    candidate = make_candidate()
    opening = make_opening()
    Application.objects.create(candidate=candidate, opening=opening)

    response = staff_client.post(NEW_URL, {"candidate": candidate.pk, "opening": opening.pk})

    assert response.status_code == 200  # the form is shown again, not a redirect
    assert response.context["form"].non_field_errors() == [
        "Ana Lopez has already applied to Data Analyst."
    ]
    assert Application.objects.count() == 1


def test_a_new_application_starts_at_applied_and_shows_on_the_candidate_page(staff_client):
    candidate = make_candidate()
    opening = make_opening("Data Analyst")
    detail_url = reverse("hiring:candidate_detail", args=[candidate.pk])

    response = staff_client.post(NEW_URL, {"candidate": candidate.pk, "opening": opening.pk})

    application = Application.objects.get()
    assert application.candidate == candidate
    assert application.opening == opening
    assert application.stage == Application.Stage.APPLIED
    assert response.status_code == 302
    assert response["Location"] == detail_url

    html = staff_client.get(detail_url).content.decode()
    assert "Data Analyst" in html
    assert "Applied" in html
    assert "No applications yet" not in html


# --- Covered the normal way (not TDD) ---


def test_only_open_openings_are_offered(staff_client):
    open_one = make_opening("Data Analyst")
    closed = make_opening("UX Designer", is_open=False)

    response = staff_client.get(NEW_URL)

    offered = list(response.context["form"].fields["opening"].queryset)
    assert offered == [open_one]
    assert closed.title not in response.content.decode()


def test_the_database_allows_one_application_per_candidate_and_opening():
    candidate = make_candidate()
    opening = make_opening()
    Application.objects.create(candidate=candidate, opening=opening)

    # Bypasses form validation: the constraint itself must refuse it.
    with pytest.raises(IntegrityError), transaction.atomic():
        Application.objects.create(candidate=candidate, opening=opening)


def test_one_candidate_can_apply_to_several_openings_and_vice_versa(staff_client):
    ana = make_candidate("Ana", "ana@example.com")
    ben = make_candidate("Ben", "ben@example.com")
    analyst = make_opening("Data Analyst")
    designer = make_opening("UX Designer")

    for candidate, opening in [(ana, analyst), (ana, designer), (ben, analyst)]:
        response = staff_client.post(NEW_URL, {"candidate": candidate.pk, "opening": opening.pk})
        assert response.status_code == 302

    assert Application.objects.count() == 3


def test_the_candidate_page_lists_only_their_own_applications(staff_client):
    ana = make_candidate("Ana", "ana@example.com")
    ben = make_candidate("Ben", "ben@example.com")
    Application.objects.create(candidate=ana, opening=make_opening("Data Analyst"))
    Application.objects.create(candidate=ben, opening=make_opening("UX Designer"))

    html = staff_client.get(reverse("hiring:candidate_detail", args=[ana.pk])).content.decode()

    assert "Data Analyst" in html
    assert "UX Designer" not in html


def test_a_candidate_without_applications_says_so(staff_client):
    candidate = make_candidate()

    response = staff_client.get(reverse("hiring:candidate_detail", args=[candidate.pk]))

    assert b"No applications yet" in response.content


def test_missing_choices_are_refused(staff_client):
    # A browser sends both fields even when nothing is chosen.
    response = staff_client.post(NEW_URL, {"candidate": "", "opening": ""})

    form = response.context["form"]
    assert set(form.errors) == {"candidate", "opening"}
    assert not Application.objects.exists()


def test_the_query_string_preselects_the_candidate_and_opening(staff_client):
    candidate = make_candidate()
    opening = make_opening()

    url = f"{NEW_URL}?candidate={candidate.pk}&opening={opening.pk}"
    form = staff_client.get(url).context["form"]

    assert form["candidate"].value() == candidate.pk
    assert form["opening"].value() == opening.pk


@pytest.mark.parametrize(
    "query", ["?candidate=abc", "?opening=-1", "?candidate=999", "?candidate=%C2%B2"]
)
def test_a_bad_preselect_value_is_ignored(staff_client, query):
    make_candidate()
    make_opening()

    assert staff_client.get(NEW_URL + query).status_code == 200


def test_the_candidate_and_open_opening_pages_link_to_the_form(staff_client):
    candidate = make_candidate()
    open_one = make_opening("Data Analyst")
    closed = make_opening("UX Designer", is_open=False)

    def page(name, pk):
        return staff_client.get(reverse(name, args=[pk])).content.decode()

    assert f"{NEW_URL}?candidate={candidate.pk}" in page("hiring:candidate_detail", candidate.pk)
    assert f"{NEW_URL}?opening={open_one.pk}" in page("hiring:opening_detail", open_one.pk)
    assert NEW_URL not in page("hiring:opening_detail", closed.pk)


def test_the_form_explains_when_there_are_no_open_openings(staff_client):
    make_candidate()
    make_opening(is_open=False)

    response = staff_client.get(NEW_URL)

    assert b"No open job openings" in response.content


def test_deleting_a_candidate_in_the_admin_deletes_their_applications(admin_client):
    candidate = make_candidate()
    opening = make_opening()
    Application.objects.create(candidate=candidate, opening=opening)

    response = admin_client.post(
        reverse("admin:hiring_candidate_delete", args=[candidate.pk]), {"post": "yes"}
    )

    assert response.status_code == 302
    assert not Application.objects.exists()
    assert JobOpening.objects.filter(pk=opening.pk).exists()  # the opening stays


def test_the_admin_shows_the_clear_duplicate_message(admin_client):
    candidate = make_candidate()
    opening = make_opening()
    Application.objects.create(candidate=candidate, opening=opening)

    response = admin_client.post(
        reverse("admin:hiring_application_add"),
        {"candidate": candidate.pk, "opening": opening.pk},
    )

    assert response.status_code == 200  # the add form is shown again
    assert b"Ana Lopez has already applied to Data Analyst." in response.content
    assert Application.objects.count() == 1


def test_the_admin_cannot_edit_the_stage(admin_client):
    application = Application.objects.create(candidate=make_candidate(), opening=make_opening())

    admin_client.post(
        reverse("admin:hiring_application_change", args=[application.pk]),
        {
            "candidate": application.candidate_id,
            "opening": application.opening_id,
            "stage": Application.Stage.HIRED,
        },
    )

    application.refresh_from_db()
    assert application.stage == Application.Stage.APPLIED


def test_the_new_application_page_requires_login(client):
    response = client.get(NEW_URL)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={NEW_URL}"
