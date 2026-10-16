import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Membership, Organization


@pytest.fixture
def user(organization):
    return User.objects.create_user(
        email="test@example.com",
        password="Testpassword123!",
        first_name="Test",
        last_name="User",
    )

    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    return user


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


@pytest.fixture
def project(organization, user):
    return organization.projects.create(
        name="Test Project",
        description="A test project.",
        created_by=user,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organization_admin_user(django_user_model, organization):
    admin = django_user_model.objects.create_user(
        email="project-admin@example.com",
        first_name="Project",
        last_name="Admin",
        password="password",
    )

    Membership.objects.create(
        user=admin,
        organization=organization,
        role=Membership.Role.ADMIN,
    )

    return admin


@pytest.fixture
def member_user(django_user_model, organization):
    member = django_user_model.objects.create_user(
        email="project-member@example.com",
        first_name="Project",
        last_name="Member",
        password="password",
    )

    Membership.objects.create(
        user=member,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    return member


@pytest.fixture
def non_member_user(django_user_model):
    return django_user_model.objects.create_user(
        email="non-member@example.com",
        first_name="Non",
        last_name="Member",
        password="password",
    )
