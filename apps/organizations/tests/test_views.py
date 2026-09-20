import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import (
    Membership,
    Organization,
    Team,
    TeamMembership,
)


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


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        email="owner@example.com",
        password="Testpassword123!",
        first_name="Team",
        last_name="Owner",
    )


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        email="admin@example.com",
        password="Testpassword123!",
        first_name="Team",
        last_name="Admin",
    )


@pytest.fixture
def member(db):
    return User.objects.create_user(
        email="member@example.com",
        password="Testpassword123!",
        first_name="Team",
        last_name="Member",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other@example.com",
        password="Testpassword123!",
        first_name="Other",
        last_name="User",
    )


@pytest.fixture
def organization(db):
    return Organization.objects.create(
        name="Test Organization",
        slug="test-organization",
        description="A test organization.",
    )


@pytest.fixture
def other_organization(db):
    return Organization.objects.create(
        name="Other Organization",
        slug="other-organization",
        description="Another organization.",
    )


@pytest.fixture
def organization_members(organization, owner, admin, member):
    Membership.objects.create(
        user=owner,
        organization=organization,
        role=Membership.Role.OWNER,
    )
    Membership.objects.create(
        user=admin,
        organization=organization,
        role=Membership.Role.ADMIN,
    )
    Membership.objects.create(
        user=member,
        organization=organization,
        role=Membership.Role.MEMBER,
    )


@pytest.fixture
def other_organization_members(other_organization, other_user):
    Membership.objects.create(
        user=other_user,
        organization=other_organization,
        role=Membership.Role.OWNER,
    )


@pytest.fixture
def team(organization, owner, organization_members):
    return Team.objects.create(
        organization=organization,
        name="Backend Team",
        description="Backend development team.",
        created_by=owner,
    )


# ---------------------------------------------------------------------------
# CREATE TEAM
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_owner_can_create_team(api_client, organization, owner, organization_members):
    api_client.force_authenticate(user=owner)

    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.post(
        url,
        {
            "name": "Frontend Team",
            "description": "Frontend development team.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Frontend Team"
    assert response.data["description"] == "Frontend development team."
    assert response.data["organization"] == uuid.UUID(str(organization.id))
    assert response.data["created_by"] == owner.id

    assert Team.objects.filter(
        organization=organization,
        name="Frontend Team",
    ).exists()


@pytest.mark.django_db
def test_admin_can_create_team(api_client, organization, admin, organization_members):
    api_client.force_authenticate(user=admin)

    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.post(
        url,
        {
            "name": "Frontend Team",
            "description": "Frontend development team.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_member_cannot_create_team(
    api_client, organization, member, organization_members
):
    api_client.force_authenticate(user=member)

    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.post(
        url,
        {
            "name": "Frontend Team",
            "description": "Frontend development team.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_anonymous_user_cannot_create_team(api_client, organization):
    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.post(
        url,
        {
            "name": "Frontend Team",
            "description": "Frontend development team.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_cannot_create_duplicate_team_name(
    api_client,
    organization,
    owner,
    organization_members,
    team,
):
    api_client.force_authenticate(user=owner)

    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.post(
        url,
        {
            "name": "Backend Team",
            "description": "Another backend team.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# LIST TEAMS
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_organization_member_can_list_teams(
    api_client,
    organization,
    member,
    organization_members,
    team,
):
    api_client.force_authenticate(user=member)

    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Backend Team"


@pytest.mark.django_db
def test_non_member_cannot_list_teams(
    api_client,
    organization,
    other_user,
    organization_members,
    team,
):
    api_client.force_authenticate(user=other_user)

    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_anonymous_user_cannot_list_teams(api_client, organization):
    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_team_list_only_returns_teams_from_requested_organization(
    api_client,
    organization,
    other_organization,
    owner,
    other_user,
    organization_members,
    other_organization_members,
    team,
):
    other_team = Team.objects.create(
        organization=other_organization,
        name="Other Team",
        description="Other organization team.",
        created_by=other_user,
    )

    api_client.force_authenticate(user=owner)

    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["id"] == str(team.id)
    assert response.data["results"][0]["id"] != str(other_team.id)


@pytest.mark.django_db
def test_team_list_includes_member_count(
    api_client,
    organization,
    owner,
    admin,
    member,
    organization_members,
    team,
):
    TeamMembership.objects.create(
        team=team,
        membership=Membership.objects.get(
            organization=organization,
            user=owner,
        ),
    )
    TeamMembership.objects.create(
        team=team,
        membership=Membership.objects.get(
            organization=organization,
            user=admin,
        ),
    )
    TeamMembership.objects.create(
        team=team,
        membership=Membership.objects.get(
            organization=organization,
            user=member,
        ),
    )

    api_client.force_authenticate(user=owner)

    url = reverse(
        "team-list-create",
        kwargs={"organization_id": organization.id},
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["member_count"] == 3


# ---------------------------------------------------------------------------
# TEAM DETAIL
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_organization_member_can_view_team_detail(
    api_client,
    organization,
    member,
    organization_members,
    team,
):
    api_client.force_authenticate(user=member)

    url = reverse(
        "team-detail",
        kwargs={
            "organization_id": organization.id,
            "pk": team.id,
        },
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(team.id)
    assert response.data["name"] == "Backend Team"


@pytest.mark.django_db
def test_non_member_cannot_view_team_detail(
    api_client,
    organization,
    other_user,
    organization_members,
    team,
):
    api_client.force_authenticate(user=other_user)

    url = reverse(
        "team-detail",
        kwargs={
            "organization_id": organization.id,
            "pk": team.id,
        },
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_anonymous_user_cannot_view_team_detail(
    api_client,
    organization,
    team,
):
    url = reverse(
        "team-detail",
        kwargs={
            "organization_id": organization.id,
            "pk": team.id,
        },
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_team_detail_cannot_access_team_from_wrong_organization(
    api_client,
    organization,
    other_organization,
    owner,
    organization_members,
    other_organization_members,
    team,
    other_user,
):
    api_client.force_authenticate(user=other_user)

    url = reverse(
        "team-detail",
        kwargs={
            "organization_id": other_organization.id,
            "pk": team.id,
        },
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
