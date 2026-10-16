import pytest
from django.urls import reverse
from rest_framework import status

from apps.organizations.models import Membership
from apps.projects.models import Project


@pytest.mark.django_db
def test_owner_can_create_project(api_client, organization, user):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )
    api_client.force_authenticate(user=user)
    url = reverse("project-list-create", args=[organization.id])
    data = {
        "name": "New Project",
        "description": "A new project description",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == data["name"]
    assert response.data["description"] == data["description"]
    assert response.data["organization"] == organization.id


@pytest.mark.django_db
def test_admin_can_create_project(api_client, organization, organization_admin_user):
    api_client.force_authenticate(user=organization_admin_user)
    url = reverse("project-list-create", args=[organization.id])
    data = {
        "name": "Admin Project",
        "description": "A project created by admin",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == data["name"]
    assert response.data["description"] == data["description"]
    assert response.data["organization"] == organization.id


@pytest.mark.django_db
def test_member_cannot_create_project(api_client, organization, member_user):
    api_client.force_authenticate(user=member_user)
    url = reverse("project-list-create", args=[organization.id])
    data = {
        "name": "Member Project",
        "description": "A project created by member",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_non_member_cannot_create_project(api_client, organization, non_member_user):
    api_client.force_authenticate(user=non_member_user)
    url = reverse("project-list-create", args=[organization.id])
    data = {
        "name": "Non-member Project",
        "description": "A project created by non-member",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_member_can_list_projects(api_client, organization, member_user):
    api_client.force_authenticate(user=member_user)
    url = reverse("project-list-create", args=[organization.id])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_non_member_cannot_list_projects(api_client, organization, non_member_user):
    api_client.force_authenticate(user=non_member_user)
    url = reverse("project-list-create", args=[organization.id])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_can_only_list_its_own_projects(
    api_client,
    organization,
    other_organization,
    member_user,
    project,
):
    # Arrange: create a project in the other organization.
    other_project = Project.objects.create(
        organization=other_organization,
        created_by=project.created_by,
        name="Other Organization Project",
    )

    api_client.force_authenticate(user=member_user)
    url = reverse("project-list-create", args=[organization.id])

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == status.HTTP_200_OK

    returned_ids = {item["id"] for item in response.data}

    assert str(project.id) in returned_ids
    assert str(other_project.id) not in returned_ids


@pytest.mark.django_db
def test_admin_can_archive_project(
    api_client, organization_admin_user, organization, project
):
    api_client.force_authenticate(user=organization_admin_user)
    url = reverse(
        "project-archive",
        kwargs={
            "organization_id": organization.id,
            "project_id": project.id,
        },
    )
    response = api_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    project.refresh_from_db()
    assert project.status == Project.Status.ARCHIVED
    assert response.data["status"] == Project.Status.ARCHIVED


@pytest.mark.django_db
def test_admin_can_restore_project(
    api_client, organization_admin_user, organization, project
):
    # First, archive the project
    project.status = Project.Status.ARCHIVED
    project.save()

    api_client.force_authenticate(user=organization_admin_user)
    url = reverse(
        "project-restore",
        kwargs={
            "organization_id": organization.id,
            "project_id": project.id,
        },
    )
    response = api_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    project.refresh_from_db()
    assert project.status == Project.Status.ACTIVE
    assert response.data["status"] == Project.Status.ACTIVE


@pytest.mark.django_db
def test_member_cannot_archive_project(api_client, member_user, organization, project):
    api_client.force_authenticate(user=member_user)

    url = reverse(
        "project-archive",
        kwargs={
            "organization_id": organization.id,
            "project_id": project.id,
        },
    )

    response = api_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN

    project.refresh_from_db()
    assert project.status == Project.Status.ACTIVE


@pytest.mark.django_db
def test_member_cannot_restore_project(api_client, member_user, organization, project):
    project.status = Project.Status.ARCHIVED
    project.save(update_fields=["status"])

    api_client.force_authenticate(user=member_user)

    url = reverse(
        "project-restore",
        kwargs={
            "organization_id": organization.id,
            "project_id": project.id,
        },
    )

    response = api_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN

    project.refresh_from_db()
    assert project.status == Project.Status.ARCHIVED


@pytest.mark.django_db
def test_non_member_cannot_retrieve_project(
    api_client, non_member_user, organization, project
):
    api_client.force_authenticate(user=non_member_user)

    url = reverse(
        "project-detail",
        kwargs={
            "organization_id": organization.id,
            "project_id": project.id,
        },
    )

    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_update_project(
    api_client, organization_admin_user, organization, project
):
    api_client.force_authenticate(user=organization_admin_user)

    url = reverse(
        "project-detail",
        kwargs={
            "organization_id": organization.id,
            "project_id": project.id,
        },
    )

    response = api_client.patch(
        url,
        {
            "name": "Updated Project",
            "description": "Updated description",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    project.refresh_from_db()
    assert project.name == "Updated Project"
    assert project.description == "Updated description"


@pytest.mark.django_db
def test_member_cannot_update_project(api_client, member_user, organization, project):
    api_client.force_authenticate(user=member_user)

    url = reverse(
        "project-detail",
        kwargs={
            "organization_id": organization.id,
            "project_id": project.id,
        },
    )

    response = api_client.patch(
        url,
        {"name": "Unauthorized Update"},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    project.refresh_from_db()
    assert project.name != "Unauthorized Update"
