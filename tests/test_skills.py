"""Skills page and skill names (user stories 41, 42)."""

import pytest
from django.db import IntegrityError
from django.urls import reverse

from hiring.models import Skill

pytestmark = pytest.mark.django_db


def test_database_refuses_a_skill_name_differing_only_in_capitalisation():
    Skill.objects.create(name="Python")

    with pytest.raises(IntegrityError):
        Skill.objects.create(name="python")


@pytest.mark.parametrize("submitted", ["python", " Python "])
def test_skills_form_refuses_a_duplicate_name_with_a_form_error(staff_client, submitted):
    Skill.objects.create(name="Python")

    response = staff_client.post(reverse("hiring:skill_list"), {"name": submitted})

    assert response.status_code == 200  # the page is shown again, not a crash
    assert b"A skill with this name already exists." in response.content
    assert Skill.objects.count() == 1


def test_spaces_around_a_skill_name_are_removed_when_saved():
    skill = Skill.objects.create(name="  Django  ")

    skill.refresh_from_db()
    assert skill.name == "Django"


def test_adding_a_skill_saves_it_and_shows_it_in_the_list(staff_client):
    response = staff_client.post(reverse("hiring:skill_list"), {"name": "  Docker "}, follow=True)

    assert response.redirect_chain == [(reverse("hiring:skill_list"), 302)]
    assert Skill.objects.get().name == "Docker"
    assert b">Docker<" in response.content


def test_skills_are_listed_alphabetically(staff_client):
    for name in ["SQL", "django", "Python"]:
        Skill.objects.create(name=name)

    response = staff_client.get(reverse("hiring:skill_list"))

    assert [s.name for s in response.context["skills"]] == ["django", "Python", "SQL"]


def test_a_blank_skill_name_is_refused(staff_client):
    response = staff_client.post(reverse("hiring:skill_list"), {"name": "   "})

    assert response.status_code == 200
    assert response.context["form"].errors["name"]
    assert not Skill.objects.exists()


def test_skills_page_requires_login(client):
    url = reverse("hiring:skill_list")

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next={url}"


def test_admin_can_add_a_skill(admin_client):
    response = admin_client.post(reverse("admin:hiring_skill_add"), {"name": "Kubernetes"})

    assert response.status_code == 302
    assert Skill.objects.filter(name="Kubernetes").exists()
