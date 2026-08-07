from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.tokens import email_verification_token, password_reset_token


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="StrongPassword123!",
    )


@pytest.fixture
def verified_user():
    return User.objects.create_user(
        email="verified@example.com",
        first_name="Verified",
        last_name="User",
        password="StrongPassword123!",
        is_email_verified=True,
    )


@pytest.mark.django_db
@patch("apps.accounts.services.send_verification_email_task.delay")
def test_register_success(mock_task, api_client):
    payload = {
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
    }

    response = api_client.post(
        reverse("register"),
        payload,
        format="json",
    )

    assert response.status_code == 201

    assert response.data["message"] == (
        "Registration successful. Please check your email to verify your account."
    )

    user = User.objects.get(email="newuser@example.com")

    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.is_email_verified is False

    mock_task.assert_called_once_with(str(user.id))


@pytest.mark.django_db
def test_register_password_mismatch(api_client):
    payload = {
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "StrongPassword123!",
        "password_confirm": "DifferentPassword123!",
    }

    response = api_client.post(
        reverse("register"),
        payload,
        format="json",
    )

    assert response.status_code == 400

    assert "password_confirm" in response.data


@pytest.mark.django_db
def test_register_duplicate_email(api_client, user):
    payload = {
        "email": user.email,
        "first_name": "Another",
        "last_name": "User",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
    }

    response = api_client.post(
        reverse("register"),
        payload,
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_login_success(api_client, verified_user):
    payload = {
        "email": verified_user.email,
        "password": "StrongPassword123!",
    }

    response = api_client.post(
        reverse("login"),
        payload,
        format="json",
    )

    assert response.status_code == 200

    assert "access" in response.data
    assert "refresh" in response.data
    assert "user" in response.data

    assert response.data["user"]["email"] == verified_user.email


@pytest.mark.django_db
def test_login_invalid_credentials(api_client, verified_user):
    payload = {
        "email": verified_user.email,
        "password": "WrongPassword123!",
    }

    response = api_client.post(
        reverse("login"),
        payload,
        format="json",
    )

    assert response.status_code == 401

    assert response.data["detail"] == "Invalid credentials."


@pytest.mark.django_db
def test_login_unverified_user(api_client, user):
    payload = {
        "email": user.email,
        "password": "StrongPassword123!",
    }

    response = api_client.post(
        reverse("login"),
        payload,
        format="json",
    )

    assert response.status_code == 403

    assert response.data["detail"] == ("Please verify your email before logging in.")


@pytest.mark.django_db
def test_me_returns_authenticated_user(api_client, verified_user):
    api_client.force_authenticate(user=verified_user)

    response = api_client.get(reverse("me"))

    assert response.status_code == 200

    assert response.data["email"] == verified_user.email
    assert response.data["first_name"] == verified_user.first_name
    assert response.data["last_name"] == verified_user.last_name


@pytest.mark.django_db
def test_logout_success(api_client, verified_user):
    login_response = api_client.post(
        reverse("login"),
        {
            "email": verified_user.email,
            "password": "StrongPassword123!",
        },
        format="json",
    )

    refresh_token = login_response.data["refresh"]

    api_client.force_authenticate(user=verified_user)

    response = api_client.post(
        reverse("logout"),
        {
            "refresh": refresh_token,
        },
        format="json",
    )

    assert response.status_code == 205

    assert response.data["detail"] == "Logout successful."


@pytest.mark.django_db
def test_logout_without_refresh_token(api_client, verified_user):
    api_client.force_authenticate(user=verified_user)

    response = api_client.post(
        reverse("logout"),
        {},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_verify_email_success(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    token = email_verification_token.make_token(user)

    response = api_client.get(
        reverse(
            "verify-email",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )
    )

    assert response.status_code == 200

    user.refresh_from_db()

    assert user.is_email_verified is True


@pytest.mark.django_db
def test_verify_email_invalid_token(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = api_client.get(
        reverse(
            "verify-email",
            kwargs={
                "uidb64": uid,
                "token": "invalid-token",
            },
        )
    )

    assert response.status_code == 400

    user.refresh_from_db()

    assert user.is_email_verified is False


@pytest.mark.django_db
def test_verify_email_already_verified(api_client, verified_user):
    uid = urlsafe_base64_encode(force_bytes(verified_user.pk))

    token = email_verification_token.make_token(verified_user)

    response = api_client.get(
        reverse(
            "verify-email",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )
    )

    assert response.status_code == 200
    assert "Email Already Verified" in response.content.decode()


@pytest.mark.django_db
@patch("apps.accounts.services.send_password_reset_email_task.delay")
def test_forgot_password_existing_user(mock_task, api_client, verified_user):
    response = api_client.post(
        reverse("forgot-password"),
        {
            "email": verified_user.email,
        },
        format="json",
    )

    assert response.status_code == 200

    mock_task.assert_called_once()


@pytest.mark.django_db
def test_reset_password_success(api_client, user):
    token = password_reset_token.make_token(user)

    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = api_client.post(
        reverse(
            "password-reset",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        ),
        {
            "password": "NewStrongPassword123!",
            "password_confirm": "NewStrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 200

    user.refresh_from_db()

    assert user.check_password("NewStrongPassword123!")


@pytest.mark.django_db
def test_reset_password_invalid_token(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = api_client.post(
        reverse(
            "password-reset",
            kwargs={
                "uidb64": uid,
                "token": "invalid-token",
            },
        ),
        {
            "password": "NewStrongPassword123!",
            "password_confirm": "NewStrongPassword123!",
        },
        format="json",
    )

    assert response.status_code == 400

    user.refresh_from_db()

    assert user.check_password("StrongPassword123!") is True


@pytest.mark.django_db
def test_reset_password_password_mismatch(api_client, user):
    token = password_reset_token.make_token(user)

    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = api_client.post(
        reverse(
            "password-reset",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        ),
        {
            "password": "NewStrongPassword123!",
            "password_confirm": "DifferentPassword123!",
        },
        format="json",
    )

    assert response.status_code == 400
