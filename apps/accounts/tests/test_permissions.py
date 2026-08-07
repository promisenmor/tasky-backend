import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User


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
def authenticated_client(user):
    client = APIClient()

    # For permission testing, force authentication.
    client.force_authenticate(user=user)

    return client


# -------------------------------------------------------------------
# Anonymous access
# -------------------------------------------------------------------


@pytest.mark.django_db
def test_register_allows_anonymous(api_client):
    response = api_client.post(
        "/api/v1/accounts/register/",
        {},
        format="json",
    )

    assert response.status_code != 401
    assert response.status_code != 403


@pytest.mark.django_db
def test_login_allows_anonymous(api_client):
    response = api_client.post(
        "/api/v1/accounts/login/",
        {},
        format="json",
    )

    assert response.status_code != 401
    assert response.status_code != 403


@pytest.mark.django_db
def test_forgot_password_allows_anonymous(api_client):
    response = api_client.post(
        "/api/v1/accounts/forgot-password/",
        {},
        format="json",
    )

    assert response.status_code != 401
    assert response.status_code != 403


@pytest.mark.django_db
def test_resend_verification_allows_anonymous(api_client):
    response = api_client.post(
        "/api/v1/accounts/resend-verification/",
        {},
        format="json",
    )

    assert response.status_code != 401
    assert response.status_code != 403


@pytest.mark.django_db
def test_refresh_token_allows_anonymous(api_client):
    response = api_client.post(
        "/api/v1/accounts/refresh/",
        {},
        format="json",
    )

    assert response.status_code != 401
    assert response.status_code != 403


# -------------------------------------------------------------------
# Authenticated access
# -------------------------------------------------------------------


@pytest.mark.django_db
def test_me_requires_authentication(api_client):
    response = api_client.get(
        "/api/v1/accounts/me/",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/accounts/logout/",
        {},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_change_password_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/accounts/change-password/",
        {},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_requires_authentication(api_client):
    response = api_client.patch(
        "/api/v1/accounts/profile/",
        {},
        format="json",
    )

    assert response.status_code == 401
