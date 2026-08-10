import pytest
from django.db import IntegrityError

from apps.accounts.models import User
from apps.organizations.models import Membership, Organization


@pytest.fixture
def user():
    return User.objects.create_user(
        email="test@example.com",
        password="Testpassword123!",
        first_name="Test",
        last_name="User",
    )


@pytest.mark.django_db
class TestOrganizationModel:
    def test_organization_creation(self):
        organization = Organization.objects.create(
            name="Tasky",
            slug="tasky",
            description="Task management workspace",
        )

        assert organization.name == "Tasky"
        assert organization.slug == "tasky"

    def test_organization_string_representation(self):
        organization = Organization.objects.create(
            name="Tasky",
            slug="tasky",
        )

        assert str(organization) == "Tasky"


@pytest.mark.django_db
class TestMembershipModel:
    def test_membership_creation(self, user):
        organization = Organization.objects.create(
            name="Tasky",
            slug="tasky",
        )

        membership = Membership.objects.create(
            user=user,
            organization=organization,
            role=Membership.Role.OWNER,
        )

        assert membership.user == user
        assert membership.organization == organization
        assert membership.role == Membership.Role.OWNER

    def test_membership_string_representation(self, user):
        organization = Organization.objects.create(
            name="Tasky",
            slug="tasky",
        )

        membership = Membership.objects.create(
            user=user,
            organization=organization,
            role=Membership.Role.OWNER,
        )

        assert str(membership) == f"{user.email} → Tasky"


@pytest.mark.django_db
def test_user_cannot_have_duplicate_membership(user):
    organization = Organization.objects.create(
        name="Tasky",
        slug="tasky",
    )

    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    with pytest.raises(IntegrityError):
        Membership.objects.create(
            user=user,
            organization=organization,
            role=Membership.Role.ADMIN,
        )
