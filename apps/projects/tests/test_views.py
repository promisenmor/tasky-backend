import pytest
from django.urls import reverse
from rest_framework import status

from apps.projects.models import Project


@pytest.mark.django_db
def test_owner_can_create_project(api_client, organization, user):
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

    assert (project.id) in returned_ids
    assert str(other_project.id) not in returned_ids
