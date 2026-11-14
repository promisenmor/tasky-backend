from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction

from apps.organizations.models import Membership, Organization
from apps.organizations.permissions import is_organization_admin
from apps.projects.models import Project, Section


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


# section service


@transaction.atomic
def create_section(
    *,
    project: Project,
    actor,
    name: str,
    description: str = "",
) -> Section:
    """Create a section within a project."""

    if not is_organization_admin(
        user=actor,
        organization=project.organization,
    ):
        raise ValidationError("You must be an admin or owner of this organization.")

    name = name.strip()
    description = (description or "").strip()

    if not name:
        raise ValidationError("A Section name cannot be empty.")

    if Section.objects.filter(project=project, name=name).exists():
        raise ValidationError("A section with this name already exists in this project")
    last_position = (
        Section.objects.filter(project=project)
        .order_by("-position")
        .values_list("position", flat=True)
        .first()
    )

    next_position = 0 if last_position is None else last_position + 1

    try:
        return Section.objects.create(
            project=project,
            name=name,
            description=description,
            position=next_position,
        )
    except IntegrityError as exc:
        raise ValidationError(
            "A section with this name already exists in this project."
        ) from exc


@transaction.atomic
def update_section(
    *,
    section: Section,
    actor,
    name: str,
    description: str | None = None,
) -> Section:
    """Update a section's name and description."""

    if not is_organization_admin(
        user=actor,
        organization=section.project.organization,
    ):
        raise ValidationError("You must be an admin or owner of this organization.")

    update_fields = []

    if name is not None:
        name = name.strip()

        if not name:
            raise ValidationError("section name cannot be empty.")

        duplicates_exists = (
            Section.objects.filter(project=section.project, name=name)
            .exclude(pk=section.pk)
            .exists()
        )
        if duplicates_exists:
            raise ValidationError(
                "A section with this name already exists in this project."
            )
        section.name = name
        update_fields.append("name")

    if description is not None:
        section.description = description.strip()
        update_fields.append("description")

    if not update_fields:
        return section

    try:
        with transaction.atomic():
            section.save(update_fields=update_fields + ["updated_at"])
    except IntegrityError as exc:
        raise ValidationError(
            "A section with this name already exists in this project"
        ) from exc

    return section


@transaction.atomic
def delete_section(*, section: Section, actor) -> None:
    """Delete a section"""

    if not is_organization_admin(
        user=actor,
        organization=section.project.organization,
    ):
        raise ValidationError("You have to be an admin or owner of this organization.")

    section.delete()


@transaction.atomic
def reoder_section(
    *,
    section: Section,
    actor,
    new_position: int,
) -> Section:
    """Move a section to a new position within its project."""

    if not is_organization_admin(
        user=actor,
        organization=section.project.organization,
    ):
        raise ValidationError("You have to be an admin or owner of this organization.")

    if new_position < 0:
        raise ValidationError("Position cannot be negative.")

    sections = Section.objects.filter(project=section.project).order_by(
        "position", "created_at"
    )

    section_count = sections.count()

    if new_position >= section_count:
        raise ValidationError("Position is outsie the valid section range.")

    if section.position == new_position:
        return section

    old_position = section.position

    if new_position < old_position:
        sections.filter(
            position__gte=new_position,
            position__lt=old_position,
        ).update(position=models.F("position") + 1)
    else:
        sections.filter(
            position__gt=old_position,
            position__lte=new_position,
        ).update(position=models.F("position") - 1)

    section.position = new_position
    section.save(update_fields=["position", "updated_at"])
