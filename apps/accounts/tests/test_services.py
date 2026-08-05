from unittest.mock import Mock, patch

import pytest

from apps.accounts.models import User
from apps.accounts.services import (
    register_user,
    request_password_reset,
    resend_verification_email,
)


@pytest.mark.django_db
def test_register_user():
    user = User.objects.create_user(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="StrongPassword123!",
    )

    serializer = Mock()
    serializer.save.return_value = user

    with patch(
        "apps.accounts.services.send_verification_email_task.delay"
    ) as mock_task:
        result = register_user(serializer=serializer)

    serializer.save.assert_called_once_with()
    mock_task.assert_called_once_with(str(user.id))

    assert result == user


@pytest.mark.django_db
def test_resend_verification_email_for_unverified_user():
    user = User.objects.create_user(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="StrongPassword123!",
    )

    user.is_email_verified = False
    user.save(update_fields=["is_email_verified"])

    with patch(
        "apps.accounts.services.send_verification_email_task.delay"
    ) as mock_task:
        resend_verification_email(email=user.email)

    mock_task.assert_called_once_with(user.id)


@pytest.mark.django_db
def test_resend_verification_email_for_verified_user():
    user = User.objects.create_user(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="StrongPassword123!",
    )

    user.is_email_verified = True
    user.save(update_fields=["is_email_verified"])

    with patch(
        "apps.accounts.services.send_verification_email_task.delay"
    ) as mock_task:
        resend_verification_email(email=user.email)

    mock_task.assert_not_called()


@pytest.mark.django_db
def test_resend_verification_email_for_nonexistent_user():
    with patch(
        "apps.accounts.services.send_verification_email_task.delay"
    ) as mock_task:
        result = resend_verification_email(email="doesnotexist@example.com")

    mock_task.assert_not_called()
    assert result is None


@pytest.mark.django_db
def test_request_password_reset():
    user = User.objects.create_user(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="StrongPassword123!",
    )

    with patch(
        "apps.accounts.services.password_reset_token.make_token",
        return_value="test-reset-token",
    ) as mock_token:
        with patch(
            "apps.accounts.services.send_password_reset_email_task.delay"
        ) as mock_task:
            request_password_reset(email=user.email)

    mock_token.assert_called_once_with(user)
    mock_task.assert_called_once_with(
        user.id,
        "test-reset-token",
    )


@pytest.mark.django_db
def test_request_password_reset_for_nonexistent_user():
    with patch("apps.accounts.services.password_reset_token.make_token") as mock_token:
        with patch(
            "apps.accounts.services.send_password_reset_email_task.delay"
        ) as mock_task:
            result = request_password_reset(email="doesnotexist@example.com")

    mock_token.assert_not_called()
    mock_task.assert_not_called()
    assert result is None


@pytest.mark.django_db
def test_request_password_reset_for_inactive_user():
    user = User.objects.create_user(
        email="inactive@example.com",
        first_name="Inactive",
        last_name="User",
        password="StrongPassword123!",
    )

    user.is_active = False
    user.save(update_fields=["is_active"])

    with patch("apps.accounts.services.password_reset_token.make_token") as mock_token:
        with patch(
            "apps.accounts.services.send_password_reset_email_task.delay"
        ) as mock_task:
            result = request_password_reset(email=user.email)

    mock_token.assert_not_called()
    mock_task.assert_not_called()
    assert result is None
