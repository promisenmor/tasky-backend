from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Invitation, Membership, Organization

INVITATION_EXPIRATION_HOURS = 72


@transaction.atomic
def create_organization(*, user, name, slug, description=""):
    organization = Organization.objects.create(
        name=name,
        slug=slug,
        description=description,
    )

    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    return organization


@transaction.atomic
def create_invitation(*, organization, invited_by, email, role):
    email = email.lower().strip()

    existing_membership = Membership.objects.filter(
        organization=organization,
        user__email__iexact=email,
    ).exists()

    if existing_membership:
        raise ValidationError("This user is already a member of the organization.")

    if Invitation.objects.filter(
        organization=organization,
        email__iexact=email,
        accepted_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).exists():
        raise ValidationError("A pending invitation already exists for this email.")

    return Invitation.objects.create(
        organization=organization,
        email=email,
        role=role,
        invited_by=invited_by,
        expires_at=timezone.now() + timedelta(hours=INVITATION_EXPIRATION_HOURS),
    )
