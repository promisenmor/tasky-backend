import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="StrongPassword123!",
    )

    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"

    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_email_verified is False

    assert user.check_password("StrongPassword123!")
    assert user.password != "StrongPassword123!"


@pytest.mark.django_db
def test_create_superuser():
    admin = User.objects.create_superuser(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="StrongPassword123!",
    )

    assert admin.is_active is True
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.check_password("StrongPassword123!")


@pytest.mark.django_db
def test_user_full_name_and_initial():
    user = User.objects.create_user(
        email="test@example.com",
        first_name="Promise",
        last_name="Nmor",
        password="StrongPassword123!",
    )

    assert user.full_name == "Promise Nmor"
    assert user.initials == "PN"
