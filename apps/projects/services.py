from django.core.exceptions import ValidationError
from django.db import transaction

from apps.organizations.models import Membership, Organization
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

    return Project.objects.create(
        organization=organization,
        created_by=created_by,
        name=name,
        description=description,
    )
