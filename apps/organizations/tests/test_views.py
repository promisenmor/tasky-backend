import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Membership, Organization


@pytest.fixture
def user():
    return User.objects.create_user(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password="testpassword123",
    )


@pytest.mark.django_db
def test_create_organization_success(user):
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        reverse("create-organization"),
        {
            "name": "Tasky",
            "slug": "tasky",
            "description": "Task management workspace",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["name"] == "Tasky"
    assert response.data["slug"] == "tasky"

    organization = Organization.objects.get(slug="tasky")

    assert Membership.objects.filter(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    ).exists()


@pytest.mark.django_db
def test_create_organization_requires_authentication():
    client = APIClient()

    response = client.post(
        reverse("create-organization"),
        {
            "name": "Tasky",
            "slug": "tasky",
            "description": "Tasky management workspace",
        },
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_organization_duplicated_slug(user):
    Organization.objects.create(
        name="Existing Organization",
        slug="tasky",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        reverse("create-organization"),
        {
            "name": "Another Organization",
            "slug": "tasky",
            "description": "Another workspace",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "slug" in response.data


@pytest.mark.django_db
def test_list_organizations_return_user_organization(user):
    organization = Organization.objects.create(
        name="Tasky",
        slug="tasky",
    )

    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("organization-list"))

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["id"] == str(organization.id)


@pytest.mark.django_db
def test_list_organizations_excludes_non_member_organizations(user):
    user_organization = Organization.objects.create(
        name="My Organization",
        slug="my-organization",
    )

    Organization.objects.create(
        name="Other Organization",
        slug="other-organization",
    )

    Membership.objects.create(
        user=user,
        organization=user_organization,
        role=Membership.Role.OWNER,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("organization-list"))

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["slug"] == "my-organization"


@pytest.mark.django_db
def test_list_organizations_requires_authentication():
    client = APIClient()

    response = client.get(reverse("organization-list"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_organization_detail_member_can_access(user):
    organization = Organization.objects.create(
        name="Tasky",
        slug="tasky",
    )

    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse(
            "organization-detail",
            kwargs={"pk": organization.id},
        )
    )

    assert response.status_code == 200
    assert response.data["id"] == str(organization.id)
    assert response.data["name"] == "Tasky"


@pytest.mark.django_db
def test_organization_detail_non_member_cannot_access(user):
    organization = Organization.objects.create(
        name="Tasky",
        slug="tasky",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        reverse(
            "organization-detail",
            kwargs={"pk": organization.id},
        )
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_update_membership_role_returns_updated_role(user):
    organization = Organization.objects.create(
        name="Tasky",
        slug="tasky",
    )
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    target_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )
    membership = Membership.objects.create(
        user=target_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        reverse(
            "detail-member",
            kwargs={
                "organization_id": organization.id,
                "membership_id": membership.id,
            },
        ),
        {"role": Membership.Role.ADMIN},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["role"] == Membership.Role.ADMIN

    membership.refresh_from_db()
    assert membership.role == Membership.Role.ADMIN
