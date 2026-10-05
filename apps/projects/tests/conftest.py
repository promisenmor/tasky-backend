import pytest

from apps.accounts.models import User
from apps.organizations.models import Organization


@pytest.fixture
def user():
    return User.objects.create_user(
        email="test@example.com",
        password="Testpassword123!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def organization():
    return Organization.objects.create(
        name="Test Organization",
        slug="test-organization",
        description="A test organization.",
    )


@pytest.fixture
def other_organization():
    return Organization.objects.create(
        name="Other Organization",
        slug="other-organization",
        description="Another test organization.",
    )
