from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.organizations.tasks import send_invitation_email_task

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

    invitation = Invitation.objects.create(
        organization=organization,
        email=email,
        role=role,
        invited_by=invited_by,
        expires_at=timezone.now() + timedelta(hours=INVITATION_EXPIRATION_HOURS),
    )

    transaction.on_commit(lambda: send_invitation_email_task.delay(invitation.id))

    return invitation


@transaction.atomic
def accept_invitation(*, invitation, user):
    if invitation.accepted_at is not None:
        raise ValidationError("This invitation has already been accepted.")

    if invitation.declined_at is not None:
        raise ValidationError("This invitation has already been declined.")

    if invitation.expires_at < timezone.now():
        raise ValidationError("This invitation has expired.")

    if invitation.email.lower() != user.email.lower():
        raise ValidationError("This invitation is not for the current user.")

    existing_membership = Membership.objects.filter(
        organization=invitation.organization,
        user=user,
    ).exists()

    if existing_membership:
        raise ValidationError("This user is already a member of the organization.")

    membership = Membership.objects.create(
        user=user,
        organization=invitation.organization,
        role=invitation.role,
    )

    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["accepted_at", "updated_at"])

    return membership


@transaction.atomic
def decline_invitation(*, invitation, user):
    if invitation.accepted_at is not None:
        raise ValidationError("This invitation has already been accepted.")

    if invitation.is_declined:
        raise ValidationError("This invitation has already been declined.")

    if invitation.is_expired:
        raise ValidationError("This invitation has expired.")

    if invitation.email.lower() != user.email.lower():
        raise ValidationError("This invitation was sent to a different address.")

    invitation.declined_at = timezone.now()
    invitation.save(update_fields=["declined_at", "updated_at"])


# Membership activites
@transaction.atomic
def change_member_role(*, membership, actor, new_role):
    actor_membership = Membership.objects.get(
        user=actor,
        organization=Membership.organization,
    )

    if membership.role == Membership.Role.OWNER:
        raise ValidationError("The organization owner cannot have their role changed.")

    if new_role == Membership.Role.OWNER:
        raise ValidationError("Ownership cannot be assigned through this operation.")

    if actor_membership.role == Membership.Role.MEMBER:
        raise ValidationError("Members cannot change their membership roles.")

    if (
        actor_membership.role == Membership.Role.ADMIN
        and membership.role == Membership.Role.ADMIN
    ):
        raise ValidationError("Admins cannot change another admins's role")

    membership.role = new_role
    membership.save(update_fields=["role"])

    return membership


@transaction.atomic
def remove_member(*, membership, actor):
    actor_membership = Membership.objects.get(
        user=actor,
        organization=membership.organization,
    )

    if membership.role == Membership.Role.OWNER:
        raise ValidationError("The organization owner cannot be removed.")

    if actor_membership.role == Membership.Role.MEMBER:
        raise ValidationError("Members cannot remove other members.")

    if (
        actor_membership.role == Membership.Role.ADMIN
        and membership.role == Membership.Role.ADMIN
    ):
        raise ValidationError("Admins cannot remove other admins.")

    if membership.user_id == actor.id:
        raise ValidationError("use the leave organization endpoint to leave.")

    membership.delete()


@transaction.atomic
def leave_organization(*, organization, user):
    membership = Membership.objects.filter(
        organization=organization,
        user=user,
    ).first()

    if membership is None:
        raise ValidationError("You are not a member of this organization.")

    if membership.role == Membership.Role.OWNER:
        raise ValidationError(
            "The organization owner cannot leave. Transfer ownership first."
        )

    membership.delete()
