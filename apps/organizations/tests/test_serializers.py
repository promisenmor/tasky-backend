import pytest

from apps.organizations.models import Organization
from apps.organizations.serializers import (
    OrganizationCreateSerializer,
    OrganizationSerializer,
)


@pytest.mark.django_db
def test_organization_serializer():
    organization = Organization.objects.create(
        name="Tasky",
        slug="tasky",
        description="Task management workspace",
    )

    serializer = OrganizationSerializer(organization)

    assert serializer.data["id"] == str(organization.id)
    assert serializer.data["name"] == "Tasky"
    assert serializer.data["slug"] == "tasky"
    assert serializer.data["description"] == "Task management workspace"
    assert "created_at" in serializer.data
    assert "updated_at" in serializer.data


@pytest.mark.django_db
def test_organization_create_serializer_valid_data():
    data = {
        "name": "Tasky",
        "slug": "tasky",
        "description": "Task management workspace",
    }

    serializer = OrganizationCreateSerializer(data=data)

    assert serializer.is_valid()
    assert serializer.validated_data["name"] == "Tasky"
    assert serializer.validated_data["slug"] == "tasky"


@pytest.mark.django_db
def test_organization_create_serializer_duplicate_slug():
    Organization.objects.create(
        name="Existing Organization",
        slug="tasky",
    )

    data = {
        "name": "Another Organization",
        "slug": "tasky",
        "description": "Another workspace",
    }

    serializer = OrganizationCreateSerializer(data=data)

    assert not serializer.is_valid()
    assert "slug" in serializer.errors


@pytest.mark.django_db
def test_organization_create_serializer_missing_name():
    data = {
        "slug": "tasky",
        "description": "Tasky management workspace",
    }

    serializer = OrganizationCreateSerializer(data=data)

    assert not serializer.is_valid()
    assert "name" in serializer.errors


@pytest.mark.django_db
def test_organization_create_serializer_missing_slug():
    data = {
        "name": "Tasky",
        "description": "Tasky management workspace",
    }

    serializer = OrganizationCreateSerializer(data=data)

    assert not serializer.is_valid()
    assert "slug" in serializer.errors
