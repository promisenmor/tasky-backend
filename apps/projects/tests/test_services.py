import pytest
from django.core.exceptions import ValidationError

from apps.organizations.models import Membership
from apps.projects.models import Project
from apps.projects.services import create_project, update_project


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


@pytest.mark.django_db
def test_duplicate_project_name_in_the_same_organization_is_rejected(
    organization,
    user,
):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    create_project(
        organization=organization,
        created_by=user,
        name="Tasky",
    )

    with pytest.raises(ValidationError):
        create_project(
            organization=organization,
            created_by=user,
            name="Tasky",
        )

    assert (
        Project.objects.filter(
            organization=organization,
            name="Tasky",
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_same_project_name_is_allowed_in_different_organization(
    organization,
    other_organization,
    user,
):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )
    Membership.objects.create(
        user=user,
        organization=other_organization,
        role=Membership.Role.OWNER,
    )

    project_one = create_project(
        organization=organization,
        created_by=user,
        name="Tasky",
    )

    project_two = create_project(
        organization=other_organization,
        created_by=user,
        name="Tasky",
    )

    assert project_one.name == project_two.name


# test for update project
@pytest.mark.django_db
def test_owner_can_update_project(organization, user):
    Membership.objects.update_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.OWNER},
    )

    project = create_project(
        organization=organization,
        created_by=user,
        name="Original Project",
    )

    updated = update_project(
        project=project,
        actor=user,
        name="Updated Project",
    )

    assert updated.name == "Updated Project"


@pytest.mark.django_db
def test_admin_can_update_project(organization, user):
    Membership.objects.update_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.OWNER},
    )

    project = create_project(
        organization=organization,
        created_by=user,
        name="Original Project",
    )

    Membership.objects.filter(
        user=user,
        organization=organization,
    ).update(role=Membership.Role.ADMIN)

    updated = update_project(
        project=project,
        actor=user,
        name="Updated Project",
        description="Updated description",
    )

    assert updated.name == "Updated Project"
    assert updated.description == "Updated description"


@pytest.mark.django_db
def test_regular_memeber_cannot_update_project(organization, user):
    Membership.objects.update_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.OWNER},
    )
    project = create_project(
        organization=organization,
        created_by=user,
        name="Original Project",
    )

    Membership.objects.filter(
        user=user,
        organization=organization,
    ).update(role=Membership.Role.MEMBER)

    with pytest.raises(ValidationError):
        update_project(
            project=project,
            actor=user,
            name="Unauthorized Change",
        )

    project.refresh_from_db()
    assert project.name == "Original Project"


@pytest.mark.django_db
def test_non_member_cannot_update_project(organization, user):
    Membership.objects.update_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.OWNER},
    )
    project = create_project(
        organization=organization,
        created_by=user,
        name="Original Project",
    )

    Membership.objects.filter(
        user=user,
        organization=organization,
    ).delete()

    with pytest.raises(ValidationError):
        update_project(
            project=project,
            actor=user,
            name="Unauthorized Change",
        )

    project.refresh_from_db()
    assert project.name == "Original Project"


@pytest.mark.django_db
def test_update_project_changes_name_and_description(organization, user):
    Membership.objects.update_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.OWNER},
    )
    project = create_project(
        organization=organization,
        created_by=user,
        name="Original Project",
        description="Original description",
    )

    updated = update_project(
        project=project,
        actor=user,
        name="  Updated Project  ",
        description="  Updated description  ",
    )

    assert updated.name == "Updated Project"
    assert updated.description == "Updated description"


@pytest.mark.django_db
def test_update_project_changes_only_name(organization, user):
    Membership.objects.update_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.OWNER},
    )
    project = create_project(
        organization=organization,
        created_by=user,
        name="Original Project",
        description="Keep this description",
    )

    updated = update_project(
        project=project,
        actor=user,
        name="Updated Project",
    )

    assert updated.name == "Updated Project"
    assert updated.description == "Keep this description"


@pytest.mark.django_db
def test_update_project_changes_only_description(organization, user):
    Membership.objects.update_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.OWNER},
    )
    project = create_project(
        organization=organization,
        created_by=user,
        name="Keep this name",
        description="Original description",
    )

    updated = update_project(
        project=project,
        actor=user,
        description="Updated description",
    )

    assert updated.name == "Keep this name"
    assert updated.description == "Updated description"


@pytest.mark.django_db
def test_update_project_rejects_duplicate_name(organization, user):
    Membership.objects.update_or_create(
        user=user,
        organization=organization,
        defaults={"role": Membership.Role.OWNER},
    )

    create_project(
        organization=organization,
        created_by=user,
        name="Existing Project",
    )
    project = create_project(
        organization=organization,
        created_by=user,
        name="Another Project",
    )

    with pytest.raises(ValidationError):
        update_project(
            project=project,
            actor=user,
            name="Existing Project",
        )

    project.refresh_from_db()
    assert project.name == "Another Project"
