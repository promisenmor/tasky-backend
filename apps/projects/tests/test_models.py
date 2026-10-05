import pytest
from django.db import IntegrityError

from apps.projects.models import Project


@pytest.mark.django_db
def test_project_can_be_created(organization, user):
    project = Project.objects.create(
        organization=organization,
        name="Tasky",
        created_by=user,
    )

    assert project.pk is not None
    assert project.organization == organization
    assert project.name == "Tasky"
    assert project.created_by == user


@pytest.mark.django_db
def test_project_generates_uuid(organization, user):
    project = Project.objects.create(
        organization=organization,
        name="Tasky",
        created_by=user,
    )

    assert project.id is not None


@pytest.mark.django_db
def test_project_defaults_to_active(organization, user):
    project = Project.objects.create(
        organization=organization,
        name="Tasky",
        created_by=user,
    )

    assert project.status == Project.Status.ACTIVE


@pytest.mark.django_db
def test_project_str(organization, user):
    project = Project.objects.create(
        organization=organization,
        name="Tasky",
        created_by=user,
    )

    assert str(project) == "Test Organization - Tasky"


@pytest.mark.django_db
def test_project_name_is_unique_per_organization(organization, user):
    Project.objects.create(
        organization=organization,
        name="Tasky",
        created_by=user,
    )

    with pytest.raises(IntegrityError):
        Project.objects.create(
            organization=organization,
            name="Tasky",
            created_by=user,
        )


@pytest.mark.django_db
def test_same_project_name_allowed_in_different_organization(
    organization,
    other_organization,
    user,
):
    Project.objects.create(
        organization=organization,
        name="Tasky",
        created_by=user,
    )

    Project.objects.create(
        organization=other_organization,
        name="Tasky",
        created_by=user,
    )

    assert Project.objects.filter(name="Tasky").count() == 2
