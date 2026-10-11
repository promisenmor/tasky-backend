import pytest
from django.core.exceptions import ValidationError

from apps.organizations.models import Membership
from apps.projects.models import Project
from apps.projects.services import create_project


@pytest.mark.django_db
def test_owner_can_create_project(organization, user):
    Membership.objects.create(
        user=user, organization=organization, role=Membership.Role.OWNER
    )

    project = create_project(
        organization=organization,
        created_by=user,
        name="Tasky",
    )

    assert project.pk is not None
    assert project.organization == organization
    assert project.created_by == user
    assert project.name == "Tasky"
    assert project.status == Project.Status.ACTIVE


@pytest.mark.django_db
def test_admin_can_create_project(organization, user):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.ADMIN,
    )

    project = create_project(
        organization=organization,
        created_by=user,
        name="Taky",
    )

    assert project.pk is not None
    assert project.organization == organization
    assert project.created_by == user
    assert project.name == "Taky"
    assert project.status == Project.Status.ACTIVE


@pytest.mark.django_db
def test_member_cannot_create_project(organization, user):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    with pytest.raises(
        ValidationError, match="You must be an admin or owner of this organization"
    ):
        create_project(organization=organization, created_by=user, name="Tasky")

    assert Project.objects.filter(organization=organization).count() == 0


@pytest.mark.django_db
def test_non_member_cannot_create_project(organization, user):
    # The user has no membership in this organization

    with pytest.raises(
        ValidationError,
        match="You must be an admin or owner of this organization",
    ):
        create_project(
            organization=organization,
            created_by=user,
            name="Tasky",
        )

    assert Project.objects.filter(organization=organization).count() == 0


@pytest.mark.django_db
def test_create_project_strips_name_and_description(organization, user):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    project = create_project(
        organization=organization,
        created_by=user,
        name=" Tasky ",
        description=" Project management app ",
    )

    assert project.name == "Tasky"
    assert project.description == "Project management app"


@pytest.mark.django_db
def test_create_project_rejects_empty_name(organization, user):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    with pytest.raises(ValidationError, match="Project name cannot be empty"):
        create_project(
            organization=organization,
            created_by=user,
            name="    ",
        )

    assert Project.objects.filter(organization=organization).count() == 0


@pytest.mark.django_db
def test_create_project_description_ddefaults_to_empty_string(
    organization,
    user,
):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    project = create_project(
        organization=organization,
        created_by=user,
        name="Tasky",
    )

    assert project.description == ""
