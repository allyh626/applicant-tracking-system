"""Job openings: create, edit, view (user stories 32, 33, 34, 43)."""

import pytest
from django.urls import reverse

from hiring.models import JobOpening, Skill

pytestmark = pytest.mark.django_db


def skill_names(opening):
    return {s.name for s in opening.required_skills.all()}


def test_creating_an_opening_saves_it_open_with_the_chosen_skills(staff_client):
    python = Skill.objects.create(name="Python")
    sql = Skill.objects.create(name="SQL")
    Skill.objects.create(name="Excel")  # exists but not chosen

    response = staff_client.post(
        reverse("hiring:opening_create"),
        {
            "title": "Data Analyst",
            "department": "Finance",
            "location": "Amarillo, TX",
            "description": "Builds the monthly reports.",
            "required_skills": [python.pk, sql.pk],
        },
    )

    assert JobOpening.objects.count() == 1
    opening = JobOpening.objects.get()
    assert response["Location"] == reverse("hiring:opening_detail", args=[opening.pk])
    assert (opening.title, opening.department, opening.location, opening.description) == (
        "Data Analyst",
        "Finance",
        "Amarillo, TX",
        "Builds the monthly reports.",
    )
    assert opening.is_open is True
    assert skill_names(opening) == {"Python", "SQL"}


def test_editing_an_opening_changes_its_fields_and_adds_and_removes_skills(staff_client):
    python = Skill.objects.create(name="Python")
    sql = Skill.objects.create(name="SQL")
    django = Skill.objects.create(name="Django")
    opening = JobOpening.objects.create(
        title="Data Analyst", department="Finance", location="Amarillo, TX", description="Old."
    )
    opening.required_skills.set([python, sql])

    response = staff_client.post(
        reverse("hiring:opening_edit", args=[opening.pk]),
        {
            "title": "Senior Data Analyst",
            "department": "Finance",
            "location": "Remote",
            "description": "New.",
            "required_skills": [sql.pk, django.pk],  # Python removed, Django added
        },
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("hiring:opening_detail", args=[opening.pk])
    opening.refresh_from_db()
    assert (opening.title, opening.location, opening.description) == (
        "Senior Data Analyst",
        "Remote",
        "New.",
    )
    assert skill_names(opening) == {"SQL", "Django"}


def make_opening(title, department, location, skills=()):
    opening = JobOpening.objects.create(
        title=title, department=department, location=location, description="..."
    )
    opening.required_skills.set(skills)
    return opening


def table_row(html, text):
    """The one <tr>...</tr> in the page that contains `text`."""
    rows = [row for row in html.split("<tr")[1:] if text in row]
    assert len(rows) == 1, f"expected one row containing {text!r}, found {len(rows)}"
    return rows[0].split("</tr>")[0]


def test_the_list_and_detail_pages_show_department_location_and_skills(staff_client):
    python = Skill.objects.create(name="Python")
    sql = Skill.objects.create(name="SQL")
    figma = Skill.objects.create(name="Figma")
    analyst = make_opening("Data Analyst", "Finance", "Amarillo, TX", [python, sql])
    make_opening("UX Designer", "Product", "Remote", [figma])

    listing = staff_client.get(reverse("hiring:opening_list")).content.decode()
    detail = staff_client.get(reverse("hiring:opening_detail", args=[analyst.pk])).content.decode()

    analyst_row = table_row(listing, "Data Analyst")
    designer_row = table_row(listing, "UX Designer")
    for text in ["Finance", "Amarillo, TX", "Python", "SQL"]:
        assert text in analyst_row
        assert text in detail
    assert "Figma" not in analyst_row and "Figma" not in detail
    for text in ["Product", "Remote", "Figma"]:
        assert text in designer_row
    assert "Python" not in designer_row and "SQL" not in designer_row


def test_one_skill_can_be_required_by_several_openings():
    python = Skill.objects.create(name="Python")
    analyst = make_opening("Data Analyst", "Finance", "Amarillo, TX", [python])
    engineer = make_opening("Backend Engineer", "IT", "Remote", [python])

    assert set(python.openings.all()) == {analyst, engineer}


def test_an_opening_can_be_created_without_skills(staff_client):
    response = staff_client.post(
        reverse("hiring:opening_create"),
        {
            "title": "Receptionist",
            "department": "Admin",
            "location": "Canyon, TX",
            "description": "Front desk.",
        },
    )

    opening = JobOpening.objects.get()
    assert response.status_code == 302
    assert skill_names(opening) == set()


@pytest.mark.parametrize("missing", ["title", "department", "location", "description"])
def test_required_fields_are_required(staff_client, missing):
    data = {"title": "T", "department": "D", "location": "L", "description": "Desc"}
    del data[missing]

    response = staff_client.post(reverse("hiring:opening_create"), data)

    assert response.status_code == 200
    assert response.context["form"].errors[missing]
    assert not JobOpening.objects.exists()


def test_the_form_does_not_offer_an_open_closed_field(staff_client):
    response = staff_client.get(reverse("hiring:opening_create"))

    assert "is_open" not in response.context["form"].fields


def test_the_form_offers_every_existing_skill(staff_client):
    Skill.objects.create(name="Python")
    Skill.objects.create(name="SQL")

    response = staff_client.get(reverse("hiring:opening_create"))

    choices = [label for _, label in response.context["form"].fields["required_skills"].choices]
    assert choices == ["Python", "SQL"]


def test_the_form_points_to_the_skills_page_when_no_skills_exist(staff_client):
    response = staff_client.get(reverse("hiring:opening_create"))

    assert b"No skills yet" in response.content
    assert reverse("hiring:skill_list").encode() in response.content


def test_a_skill_that_does_not_exist_is_refused(staff_client):
    response = staff_client.post(
        reverse("hiring:opening_create"),
        {
            "title": "T",
            "department": "D",
            "location": "L",
            "description": "Desc",
            "required_skills": [999],
        },
    )

    assert response.context["form"].errors["required_skills"]
    assert not JobOpening.objects.exists()


def test_text_fields_are_trimmed_when_saved():
    opening = make_opening("  Data Analyst ", " Finance", "Remote  ")

    opening.refresh_from_db()
    assert (opening.title, opening.department, opening.location) == (
        "Data Analyst",
        "Finance",
        "Remote",
    )


def test_a_failed_edit_keeps_the_saved_title_in_the_heading(staff_client):
    opening = make_opening("Data Analyst", "Finance", "Remote")

    response = staff_client.post(
        reverse("hiring:opening_edit", args=[opening.pk]),
        {"title": "Lead Analyst", "department": "", "location": "Remote", "description": "x"},
    )

    assert response.status_code == 200
    assert b"Edit Data Analyst" in response.content
    assert b"Edit Lead Analyst" not in response.content
    opening.refresh_from_db()
    assert opening.title == "Data Analyst"


def test_editing_does_not_change_the_open_status(staff_client):
    opening = make_opening("Data Analyst", "Finance", "Remote")
    JobOpening.objects.filter(pk=opening.pk).update(is_open=False)

    staff_client.post(
        reverse("hiring:opening_edit", args=[opening.pk]),
        {
            "title": "Data Analyst",
            "department": "Finance",
            "location": "Remote",
            "description": "x",
        },
    )

    opening.refresh_from_db()
    assert opening.is_open is False


def test_the_list_shows_a_message_when_there_are_no_openings(staff_client):
    response = staff_client.get(reverse("hiring:opening_list"))

    assert b"No job openings yet" in response.content


def test_an_unknown_opening_is_a_404(staff_client):
    assert staff_client.get(reverse("hiring:opening_detail", args=[999])).status_code == 404
    assert staff_client.get(reverse("hiring:opening_edit", args=[999])).status_code == 404


def test_the_admin_lists_job_openings(admin_client):
    make_opening("Data Analyst", "Finance", "Remote")

    response = admin_client.get(reverse("admin:hiring_jobopening_changelist"))

    assert response.status_code == 200
    assert b"Data Analyst" in response.content


@pytest.mark.parametrize(
    "name, needs_pk",
    [
        ("hiring:opening_list", False),
        ("hiring:opening_create", False),
        ("hiring:opening_detail", True),
        ("hiring:opening_edit", True),
    ],
)
def test_opening_pages_require_login(client, name, needs_pk):
    args = [make_opening("Data Analyst", "Finance", "Remote").pk] if needs_pk else []
    url = reverse(name, args=args)

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"
