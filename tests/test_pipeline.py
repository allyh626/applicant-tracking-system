"""Stage moves and the pipeline page (user stories 40, 46, 48-55)."""

import re
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from hiring.models import Application, Candidate, JobOpening, StageChange, StageMoveError

pytestmark = pytest.mark.django_db

Stage = Application.Stage
FORWARD = [Stage.APPLIED, Stage.SCREENING, Stage.INTERVIEW, Stage.FINAL_REVIEW, Stage.OFFER]
FINAL = [Stage.HIRED, Stage.REJECTED, Stage.WITHDRAWN]

# Every allowed move: one step forward, or out to Rejected/Withdrawn from any
# stage that isn't final.
ALLOWED = [
    *zip(FORWARD, [*FORWARD[1:], Stage.HIRED], strict=True),
    *[(stage, Stage.REJECTED) for stage in FORWARD],
    *[(stage, Stage.WITHDRAWN) for stage in FORWARD],
]
# Every other (from, to) pair, including "moving" to the stage it's already at.
REFUSED = [(a, b) for a in Stage for b in Stage if (a, b) not in ALLOWED]


def make_opening(title="Data Analyst", is_open=True):
    return JobOpening.objects.create(
        title=title, department="Finance", location="Remote", description="...", is_open=is_open
    )


def make_application(stage=Stage.APPLIED, opening_open=True, *, first_name="Ana", opening=None):
    candidate = Candidate.objects.create(
        first_name=first_name,
        last_name="Lopez",
        email=f"{first_name.lower()}@example.com",
        source="referral",
    )
    opening = opening or make_opening(is_open=opening_open)
    return Application.objects.create(candidate=candidate, opening=opening, stage=stage)


@pytest.mark.parametrize("from_stage, to_stage", ALLOWED)
def test_every_allowed_move_succeeds(staff_user, from_stage, to_stage):
    application = make_application(from_stage)

    application.move_to(to_stage, staff_user)

    application.refresh_from_db()
    assert application.stage == to_stage


@pytest.mark.parametrize("from_stage, to_stage", REFUSED)
def test_every_other_move_is_refused(staff_user, from_stage, to_stage):
    application = make_application(from_stage)

    with pytest.raises(StageMoveError):
        application.move_to(to_stage, staff_user)


def test_a_move_records_one_history_entry_with_the_stages_and_user(staff_user):
    application = make_application(Stage.INTERVIEW)

    application.move_to(Stage.FINAL_REVIEW, staff_user)

    changes = list(StageChange.objects.all())
    assert len(changes) == 1
    [change] = changes
    assert change.application == application
    assert change.from_stage == Stage.INTERVIEW
    assert change.to_stage == Stage.FINAL_REVIEW
    assert change.changed_by == staff_user


def test_a_refused_move_writes_no_history_and_keeps_the_stage(staff_user):
    application = make_application(Stage.INTERVIEW)

    with pytest.raises(StageMoveError):
        application.move_to(Stage.APPLIED, staff_user)  # backwards

    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW
    assert not StageChange.objects.exists()


def move_url(application):
    return reverse("hiring:application_move", args=[application.pk])


def test_a_crafted_refused_move_returns_the_row_with_the_error(staff_client):
    application = make_application(Stage.APPLIED)

    # The page only offers "Move to Screening", but a crafted request can send anything.
    response = staff_client.post(move_url(application), {"to": "hired"}, HTTP_HX_REQUEST="true")

    html = response.content.decode()
    assert response.status_code == 200  # 200, so HTMX swaps the row in
    assert f'<tr id="application-{application.pk}"' in html
    assert "Can&#x27;t move from Applied to Hired." in html
    assert "<html" not in html  # just the row, not a whole page
    application.refresh_from_db()
    assert application.stage == Stage.APPLIED
    assert not StageChange.objects.exists()


def test_a_move_returns_the_updated_row_and_the_history_entry_out_of_band(staff_client):
    application = make_application(Stage.APPLIED)

    response = staff_client.post(move_url(application), {"to": "screening"}, HTTP_HX_REQUEST="true")

    html = response.content.decode()
    assert response.status_code == 200
    assert "<html" not in html  # just the row, not a whole page
    row, _, out_of_band = html.partition("</tr>")
    assert f'<tr id="application-{application.pk}"' in row
    assert "Screening" in row  # the new stage badge
    assert "Move to Interview" in row  # the next button, one step on
    change = StageChange.objects.get()
    assert 'hx-swap-oob="afterbegin:#stage-history"' in out_of_band
    assert f'id="stage-change-{change.pk}"' in out_of_band
    assert "Applied &rarr; Screening" in out_of_band
    assert "by staff" in out_of_band


# --- Covered the normal way (not TDD) ---


def pipeline_url(opening):
    return reverse("hiring:opening_pipeline", args=[opening.pk])


STAGE_BUTTON = re.compile(r"<button[^>]*hx-post[^>]*>(.*?)</button>", re.DOTALL)


def stage_buttons(html):
    """Every stage button on the page, as (opening tag, text) pairs, in order."""
    return [(m.group(0), m.group(1).strip()) for m in STAGE_BUTTON.finditer(html)]


def buttons(html):
    """The text of every stage button on the page, in order."""
    return [text for _, text in stage_buttons(html)]


@pytest.mark.parametrize(
    "stage, expected",
    [
        (Stage.APPLIED, ["Move to Screening", "Reject", "Withdraw"]),
        (Stage.FINAL_REVIEW, ["Move to Offer", "Reject", "Withdraw"]),
        (Stage.OFFER, ["Move to Hired", "Reject", "Withdraw"]),
        (Stage.HIRED, []),
        (Stage.REJECTED, []),
        (Stage.WITHDRAWN, []),
    ],
)
def test_each_row_shows_only_the_buttons_its_stage_allows(staff_client, stage, expected):
    application = make_application(stage)

    html = staff_client.get(pipeline_url(application.opening)).content.decode()

    assert buttons(html) == expected
    assert ("Final stage: no moves" in html) == (not expected)


def test_reject_and_withdraw_ask_for_confirmation_but_moving_forward_does_not(staff_client):
    application = make_application(Stage.INTERVIEW)

    html = staff_client.get(pipeline_url(application.opening)).content.decode()

    [forward, reject, withdraw] = [tag for tag, _ in stage_buttons(html)]
    assert "hx-confirm" not in forward
    assert 'hx-confirm="Reject Ana Lopez? This is final' in reject
    assert 'hx-confirm="Mark Ana Lopez as withdrawn? This is final' in withdraw


def test_the_pipeline_lists_only_this_openings_applications(staff_client):
    analyst = make_opening("Data Analyst")
    designer = make_opening("UX Designer")
    make_application(first_name="Ana", opening=analyst)
    make_application(first_name="Ben", opening=analyst, stage=Stage.HIRED)
    make_application(first_name="Cara", opening=designer)

    response = staff_client.get(pipeline_url(analyst))

    names = [a.candidate.first_name for a in response.context["applications"]]
    assert sorted(names) == ["Ana", "Ben"]  # final stages are listed too
    assert "Cara" not in response.content.decode()


def test_the_pipeline_shows_recent_changes_for_this_opening_only(staff_client, staff_user):
    ana = make_application(first_name="Ana")
    cara = make_application(first_name="Cara", opening=make_opening("UX Designer"))
    ana.move_to(Stage.SCREENING, staff_user)
    cara.move_to(Stage.REJECTED, staff_user)

    html = staff_client.get(pipeline_url(ana.opening)).content.decode()

    history = html.split('id="stage-history"', 1)[1]
    assert "Applied &rarr; Screening" in history
    assert "Rejected" not in history


def test_an_opening_without_applications_says_so(staff_client):
    html = staff_client.get(pipeline_url(make_opening())).content.decode()

    assert "No applications for this opening yet." in html
    assert "No stage changes yet." in html


def test_applications_under_a_closed_opening_can_still_be_moved(staff_client):
    application = make_application(Stage.OFFER, opening_open=False)

    html = staff_client.get(pipeline_url(application.opening)).content.decode()
    assert "Move to Hired" in html
    assert "Add application" not in html  # closed: no new applications

    response = staff_client.post(move_url(application), {"to": "hired"}, HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == Stage.HIRED


def test_a_move_updates_when_the_stage_changed(staff_user):
    application = make_application()
    # A fixed earlier time, so the check can't depend on how fine the clock is.
    before = timezone.now() - timedelta(days=3)
    Application.objects.filter(pk=application.pk).update(stage_changed_at=before)
    application.refresh_from_db()

    application.move_to(Stage.SCREENING, staff_user)

    application.refresh_from_db()
    assert application.stage_changed_at > before
    assert application.stage_changed_at == StageChange.objects.get().changed_at


def test_a_move_made_from_an_out_of_date_copy_is_refused(staff_user):
    # Two staff members load the same Applied application at once.
    mine = make_application()
    theirs = Application.objects.get(pk=mine.pk)
    theirs.move_to(Stage.SCREENING, staff_user)

    # My copy still says Applied, so Screening looks allowed, but it isn't anymore.
    with pytest.raises(StageMoveError, match="Someone else just moved this application"):
        mine.move_to(Stage.SCREENING, staff_user)

    assert StageChange.objects.count() == 1
    assert mine.stage == Stage.SCREENING  # refreshed, so the row shows the real stage


def test_a_missing_stage_in_the_request_is_refused(staff_client):
    application = make_application()

    response = staff_client.post(move_url(application), {}, HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert "Can&#x27;t move from Applied to" in response.content.decode()
    assert not StageChange.objects.exists()


def test_the_move_endpoint_refuses_a_get(staff_client):
    application = make_application()

    response = staff_client.get(move_url(application), {"to": "screening"})

    assert response.status_code == 405
    application.refresh_from_db()
    assert application.stage == Stage.APPLIED


def test_the_move_endpoint_requires_login(client):
    application = make_application()
    url = move_url(application)

    response = client.post(url, {"to": "screening"})

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"
    application.refresh_from_db()
    assert application.stage == Stage.APPLIED
    assert not StageChange.objects.exists()


def test_the_pipeline_page_requires_login(client):
    url = pipeline_url(make_opening())

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"


def test_moving_an_unknown_application_is_a_404(staff_client):
    response = staff_client.post(
        reverse("hiring:application_move", args=[999]), {"to": "screening"}
    )

    assert response.status_code == 404


def test_the_opening_pages_link_to_the_pipeline(staff_client):
    opening = make_opening(is_open=False)  # closed openings keep their pipeline

    detail = staff_client.get(reverse("hiring:opening_detail", args=[opening.pk]))
    listing = staff_client.get(reverse("hiring:opening_list"))

    assert pipeline_url(opening) in detail.content.decode()
    assert pipeline_url(opening) in listing.content.decode()


def test_the_admin_shows_history_read_only(admin_client, staff_user):
    application = make_application()
    application.move_to(Stage.SCREENING, staff_user)
    url = reverse("admin:hiring_application_change", args=[application.pk])

    html = admin_client.get(url).content.decode()

    assert "Stage changes" in html
    assert "stage_changes-0-to_stage" not in html  # no editable history fields
