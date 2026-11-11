import pytest
from django.db import IntegrityError, transaction

from apps.projects.models import Project, Section


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


# section test
@pytest.mark.django_db
def test_section_can_be_created(project):
    section = Section.objects.create(
        project=project,
        name="backlog",
        description="Tasks waiting to be started",
    )

    assert section.project == project
    assert section.name == "backlog"


@pytest.mark.django_db
def test_section_generates_uuid(project):
    section = Section.objects.create(
        project=project,
        name="backlog",
    )

    assert section.project == project
    assert section.id is not None


@pytest.mark.django_db
def test_section_defaults_to_position_zero(project):
    section = Section.objects.create(
        project=project,
        name="backlog",
    )

    assert section.project == project
    assert section.id is not None


@pytest.mark.django_db
def test_section_str(section):
    assert str(section) == f"{section.project.name} - {section.name}"


@pytest.mark.django_db
def test_section_name_is_unique_per_project(project):
    Section.objects.create(
        project=project,
        name="backlog",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Section.objects.create(
                project=project,
                name="backlog",
            )


@pytest.mark.django_db
def test_same_section_name_allowed_in_different_projects(project, organization, user):
    another_project = Project.objects.create(
        organization=organization,
        name="Another project",
        created_by=user,
    )

    Section.objects.create(project=project, name="backlog")
    Section.objects.create(project=another_project, name="backlog")
