from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.organizations.models import Membership, Organization
from apps.organizations.permissions import is_organization_admin
from apps.projects.models import Project


@transaction.atomic
def create_project(
    *,
    organization: Organization,
    created_by,
    name: str,
    description: str = "",
) -> Project:
    """
    Create a new project and assign the user as the owner.
    """
    is_admin = Membership.objects.filter(
        user=created_by,
        organization=organization,
        role__in=[
            Membership.Role.ADMIN,
            Membership.Role.OWNER,
        ],
    ).exists()

    if not is_admin:
        raise ValidationError("You must be an admin or owner of this organization.")

    name = name.strip()
    description = (description or "").strip()

    if not name:
        raise ValidationError("Project name cannot be empty")

    # Reject duplicate names within the organization.
    if Project.objects.filter(
        organization=organization,
        name=name,
    ).exists():
        raise ValidationError(
            "A project with this name already exists in this organization."
        )

    return Project.objects.create(
        organization=organization,
        created_by=created_by,
        name=name,
        description=description,
    )


@transaction.atomic
def update_project(
    *,
    project: Project,
    actor,
    name: str | None = None,
    description: str | None = None,
) -> Project:
    """Update a project's name and description."""

    if not is_organization_admin(
        user=actor,
        organization=project.organization,
    ):
        raise ValidationError("You must be an admin or owner of this organization.")

    update_fields = []

    if name is not None:
        name = name.strip()

        if not name:
            raise ValidationError("Project name cannot be empty.")

        duplicate_exists = (
            Project.objects.filter(
                organization=project.organization,
                name=name,
            )
            .exclude(pk=project.pk)
            .exists()
        )

        if duplicate_exists:
            raise ValidationError(
                "A project with this name already exists in this organization"
            )

        project.name = name
        update_fields.append("name")

    if description is not None:
        project.description = description.strip()
        update_fields.append("description")

    if not update_fields:
        return project

    try:
        with transaction.atomic():
            project.save(update_fields=update_fields + ["updated_at"])
    except IntegrityError as exc:
        raise ValidationError(
            "A project with this name already exists in this organization."
        ) from exc

    return project


@transaction.atomic
def archive_project(*, project: Project, actor) -> Project:
    """Archive a project."""

    if not is_organization_admin(
        user=actor,
        organization=project.organization,
    ):
        raise ValidationError("You must be an admin or owner of this organization.")

    project.status = Project.Status.ARCHIVED
    project.save(update_fields=["status", "updated_at"])

    return project


@transaction.atomic
def restore_project(*, project: Project, actor) -> Project:
    """Restore an archieved project"""

    if not is_organization_admin(
        user=actor,
        organization=project.organization,
    ):
        raise ValidationError("You must be an admin or owner of this organization.")

    project.status = Project.Status.ACTIVE
    project.save(update_fields=["status", "updated_at"])

    return project
