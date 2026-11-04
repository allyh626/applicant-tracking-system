"""Shared pytest fixtures used across the test suite."""

import pytest


@pytest.fixture
def staff_user(django_user_model):
    """An ordinary staff account, like one an admin creates in the Django admin."""
    return django_user_model.objects.create_user(username="staff", password="test-pass-123")


@pytest.fixture
def staff_client(client, staff_user):
    """A test client that is already logged in as `staff_user`."""
    client.force_login(staff_user)
    return client
