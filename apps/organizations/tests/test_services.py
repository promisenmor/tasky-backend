import pytest

from apps.organizations.models import Membership
from apps.organizations.services import create_organization


@pytest.mark.django_db
def test_create_organization_creates_owner_membership(user):
    organization = create_organization(
        user=user,
        name="Test Organization",
        slug="test-organization",
        description="A test organization.",
    )

    membership = Membership.objects.get(
        user=user,
        organization=organization,
    )

    assert membership.role == Membership.Role.OWNER
