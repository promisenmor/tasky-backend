import pytest

from apps.accounts.models import User
from apps.accounts.serializers import (
    LoginSerializer,
    UserCreateSerializer,
)


@pytest.mark.django_db
def test_user_create_serializer():
    data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
    }

    serializer = UserCreateSerializer(data=data)

    assert serializer.is_valid(), serializer.errors

    user = serializer.save()

    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.check_password("StrongPassword123!")
    assert user.password != "StrongPassword123!"


@pytest.mark.django_db
def test_user_create_serializer_password_mismatch():
    data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "StrongPassword123!",
        "password_confirm": "DifferentPassword123!",
    }

    serializer = UserCreateSerializer(data=data)

    assert not serializer.is_valid()
    assert "password_confirm" in serializer.errors


@pytest.mark.django_db
def test_user_create_serializer_duplicate_email():
    User.objects.create_user(
        email="test@example.com",
        first_name="Existing",
        last_name="User",
        password="StrongPassword123!",
    )

    data = {
        "email": "test@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
    }

    serializer = UserCreateSerializer(data=data)

    assert not serializer.is_valid()
    assert "email" in serializer.errors


@pytest.mark.django_db
def test_login_serializer_valid_data():
    data = {
        "email": "test@example.com",
        "password": "StrongPassword123!",
    }

    serializer = LoginSerializer(data=data)

    assert serializer.is_valid()
    assert serializer.validated_data["email"] == "test@example.com"
    assert serializer.validated_data["password"] == "StrongPassword123!"


def test_login_serializer_invalid_email():
    data = {
        "email": "invalid-email",
        "password": "StrongPassword123!",
    }

    serializer = LoginSerializer(data=data)

    assert not serializer.is_valid()
    assert "email" in serializer.errors
