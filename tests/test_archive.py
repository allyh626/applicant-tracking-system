"""Archiving and restoring candidates (user stories 26, 27, 28, 29, 30)."""

import pytest
from django.urls import reverse

from hiring.models import Application, Candidate, JobOpening

pytestmark = pytest.mark.django_db

Stage = Application.Stage

ACTIVE_REFUSAL = "reject or withdraw"


def make_candidate(first_name="Ana", last_name="Lopez", email="ana@example.com", **extra):
    extra.setdefault("source", Candidate.Source.REFERRAL)
    return Candidate.objects.create(
        first_name=first_name, last_name=last_name, email=email, **extra
    )


def make_opening(title="Data Analyst", is_open=True):
    return JobOpening.objects.create(
        title=title, department="Finance", location="Remote", description="...", is_open=is_open
    )


def give_applications(candidate, stages):
    # Stages are set directly here only to arrange the test; the app moves them with move_to().
    for number, stage in enumerate(stages):
        Application.objects.create(
            candidate=candidate, opening=make_opening(f"Opening {number}"), stage=stage
        )


@pytest.mark.parametrize(
    "stages, archived",
    [
        ([], True),  # no applications at all
        ([Stage.HIRED, Stage.REJECTED, Stage.WITHDRAWN], True),  # all final
        ([Stage.APPLIED], False),
        ([Stage.OFFER], False),
        ([Stage.REJECTED, Stage.INTERVIEW], False),  # one active is enough to block
    ],
)
def test_archiving_is_refused_while_any_application_is_active(staff_client, stages, archived):
    candidate = make_candidate()
    give_applications(candidate, stages)

    response = staff_client.post(
        reverse("hiring:candidate_archive", args=[candidate.pk]), follow=True
    )

    candidate.refresh_from_db()
    assert candidate.archived is archived
    assert response.redirect_chain[-1][0] == reverse("hiring:candidate_detail", args=[candidate.pk])
    page = response.content.decode()
    if archived:
        assert ACTIVE_REFUSAL not in page
    else:
        assert ACTIVE_REFUSAL in page  # the refusal explains what to do first


@pytest.mark.parametrize(
    "query, expected",
    [
        ("", ["Ana Lopez", "Ben Lopez"]),  # archived hidden by default
        ("?archived=1", ["Ana Lopez", "Ben Lopez", "Cara Lopez", "Dan Lopez"]),
        ("?archived=1&q=cara", ["Cara Lopez"]),
        ("?q=cara", []),  # the search alone doesn't reveal archived people
        ("?archived=1&source=job_board", ["Ben Lopez", "Dan Lopez"]),
        ("?source=job_board", ["Ben Lopez"]),
    ],
)
def test_the_list_hides_archived_candidates_unless_the_toggle_is_on(staff_client, query, expected):
    make_candidate("Ana", email="ana@example.com")
    make_candidate("Ben", email="ben@example.com", source=Candidate.Source.JOB_BOARD)
    make_candidate("Cara", email="cara@example.com", archived=True)
    make_candidate("Dan", email="dan@example.com", source=Candidate.Source.JOB_BOARD, archived=True)

    response = staff_client.get(reverse("hiring:candidate_list") + query)

    assert [c.full_name for c in response.context["candidates"]] == expected


def test_a_crafted_post_with_an_archived_candidate_is_refused(staff_client):
    archived = make_candidate(archived=True)
    opening = make_opening()

    response = staff_client.post(
        reverse("hiring:application_create"), {"candidate": archived.pk, "opening": opening.pk}
    )

    assert response.status_code == 200  # the form is shown again, not a redirect
    assert "archived" in " ".join(response.context["form"].errors["candidate"])
    assert not Application.objects.exists()


# --- Covered the normal way (not TDD) ---


def test_restore_clears_the_archived_flag(staff_client):
    candidate = make_candidate(archived=True)

    response = staff_client.post(reverse("hiring:candidate_restore", args=[candidate.pk]))

    candidate.refresh_from_db()
    assert candidate.archived is False
    assert response["Location"] == reverse("hiring:candidate_detail", args=[candidate.pk])


def test_a_restored_candidate_can_apply_again(staff_client):
    candidate = make_candidate(archived=True)
    opening = make_opening()
    staff_client.post(reverse("hiring:candidate_restore", args=[candidate.pk]))

    response = staff_client.post(
        reverse("hiring:application_create"), {"candidate": candidate.pk, "opening": opening.pk}
    )

    assert response.status_code == 302
    assert Application.objects.filter(candidate=candidate).exists()


def test_archiving_keeps_the_candidates_applications(staff_client):
    candidate = make_candidate()
    give_applications(candidate, [Stage.HIRED, Stage.REJECTED])

    staff_client.post(reverse("hiring:candidate_archive", args=[candidate.pk]))

    assert candidate.applications.count() == 2


def test_the_refusal_message_counts_the_active_applications(staff_client):
    candidate = make_candidate()
    give_applications(candidate, [Stage.APPLIED, Stage.INTERVIEW, Stage.HIRED])

    response = staff_client.post(
        reverse("hiring:candidate_archive", args=[candidate.pk]), follow=True
    )

    assert b"their 2 active applications" in response.content


@pytest.mark.parametrize(
    "name, starts_archived",
    [("hiring:candidate_archive", False), ("hiring:candidate_restore", True)],
)
def test_archive_and_restore_refuse_a_get(staff_client, name, starts_archived):
    candidate = make_candidate(archived=starts_archived)

    response = staff_client.get(reverse(name, args=[candidate.pk]))

    assert response.status_code == 405
    candidate.refresh_from_db()
    assert candidate.archived is starts_archived


@pytest.mark.parametrize("name", ["hiring:candidate_archive", "hiring:candidate_restore"])
def test_archive_and_restore_of_an_unknown_candidate_is_a_404(staff_client, name):
    assert staff_client.post(reverse(name, args=[999])).status_code == 404


@pytest.mark.parametrize(
    "name, starts_archived",
    [("hiring:candidate_archive", False), ("hiring:candidate_restore", True)],
)
def test_archive_and_restore_require_login(client, name, starts_archived):
    candidate = make_candidate(archived=starts_archived)
    url = reverse(name, args=[candidate.pk])

    response = client.post(url)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"
    candidate.refresh_from_db()
    assert candidate.archived is starts_archived  # unchanged


def test_archived_candidates_are_not_offered_in_the_application_form(staff_client):
    active = make_candidate("Ana", email="ana@example.com")
    make_candidate("Cara", email="cara@example.com", archived=True)

    response = staff_client.get(reverse("hiring:application_create"))

    assert list(response.context["form"].fields["candidate"].queryset) == [active]
    assert b"cara@example.com" not in response.content


def test_the_detail_page_offers_archive_for_an_active_candidate(staff_client):
    candidate = make_candidate()

    html = staff_client.get(reverse("hiring:candidate_detail", args=[candidate.pk])).content
    html = html.decode()

    assert reverse("hiring:candidate_archive", args=[candidate.pk]) in html
    assert reverse("hiring:candidate_restore", args=[candidate.pk]) not in html
    assert f"{reverse('hiring:application_create')}?candidate={candidate.pk}" in html


def test_the_detail_page_offers_restore_and_no_new_application_when_archived(staff_client):
    candidate = make_candidate(archived=True)

    html = staff_client.get(reverse("hiring:candidate_detail", args=[candidate.pk])).content
    html = html.decode()

    assert reverse("hiring:candidate_restore", args=[candidate.pk]) in html
    assert reverse("hiring:candidate_archive", args=[candidate.pk]) not in html
    assert reverse("hiring:application_create") not in html
    assert ">Archived</span>" in html


def test_the_list_toggle_shows_its_state_and_badges_archived_rows(staff_client):
    make_candidate("Cara", email="cara@example.com", archived=True)
    url = reverse("hiring:candidate_list")

    off = staff_client.get(url).content.decode()
    on = staff_client.get(url + "?archived=1").content.decode()

    assert 'name="archived" value="1" class="checkbox" >' in off
    assert 'name="archived" value="1" class="checkbox" checked>' in on
    assert "Archived</span>" in on


def test_an_all_archived_list_explains_where_everyone_went(staff_client):
    make_candidate(archived=True)

    response = staff_client.get(reverse("hiring:candidate_list"))

    assert b"No active candidates" in response.content
    assert b"No candidates yet" not in response.content


def test_editing_an_archived_candidate_keeps_them_archived(staff_client):
    candidate = make_candidate(archived=True)

    staff_client.post(
        reverse("hiring:candidate_edit", args=[candidate.pk]),
        {"first_name": "Ana", "last_name": "Ruiz", "email": "ana@example.com", "source": "other"},
    )

    candidate.refresh_from_db()
    assert candidate.last_name == "Ruiz"
    assert candidate.archived is True


def admin_save(admin_client, candidate, archived):
    data = {
        "first_name": "Ana",
        "last_name": "Lopez",
        "email": "ana@example.com",
        "source": "referral",
    }
    if archived:
        data["archived"] = "on"  # an unticked checkbox sends nothing
    return admin_client.post(reverse("admin:hiring_candidate_change", args=[candidate.pk]), data)


def test_the_admin_cannot_archive_a_candidate_with_active_applications(admin_client):
    candidate = make_candidate()
    give_applications(candidate, [Stage.APPLIED])

    response = admin_save(admin_client, candidate, archived=True)

    assert response.status_code == 200  # the change form is shown again
    assert ACTIVE_REFUSAL.encode() in response.content
    candidate.refresh_from_db()
    assert candidate.archived is False


@pytest.mark.parametrize(
    "starts_archived, stages, tick, ends_archived",
    [
        (False, [Stage.HIRED], True, True),  # archive: all applications final
        (True, [], False, False),  # restore
        (True, [Stage.APPLIED], True, True),  # already archived: saving other edits is fine
    ],
)
def test_the_admin_can_archive_and_restore_when_the_rule_allows(
    admin_client, starts_archived, stages, tick, ends_archived
):
    candidate = make_candidate(archived=starts_archived)
    give_applications(candidate, stages)

    response = admin_save(admin_client, candidate, archived=tick)

    assert response.status_code == 302
    candidate.refresh_from_db()
    assert candidate.archived is ends_archived


@pytest.mark.parametrize(
    "name, archived, notice",
    [
        ("hiring:candidate_archive", True, "already archived"),
        ("hiring:candidate_restore", False, "already active"),
    ],
)
def test_repeating_archive_or_restore_says_nothing_changed(staff_client, name, archived, notice):
    candidate = make_candidate(archived=archived)

    response = staff_client.post(reverse(name, args=[candidate.pk]), follow=True)

    candidate.refresh_from_db()
    assert candidate.archived is archived
    assert notice.encode() in response.content
    assert b"has been" not in response.content  # no "archived"/"restored" success message


def test_a_no_match_search_mentions_archived_only_when_there_are_some(staff_client):
    make_candidate()
    url = reverse("hiring:candidate_list") + "?q=zzz"

    without = staff_client.get(url).content
    make_candidate("Cara", email="cara@example.com", archived=True)
    with_some = staff_client.get(url).content

    assert b"Archived candidates are hidden" not in without
    assert b"Archived candidates are hidden" in with_some
