from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User
from apps.organizations.models import (
    Invitation,
    Membership,
    Organization,
)
from apps.organizations.services import (
    accept_invitation,
    create_organization,
    decline_invitation,
)


@pytest.fixture
def user():
    return User.objects.create_user(
        email="test@example.com",
        password="Testpassword123!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def organization():
    return Organization.objects.create(
        name="Test Organization",
        slug="test-organization",
        description="A test organization.",
    )


@pytest.mark.django_db
def test_create_organization_creates_owner_membership(user):
    organization = create_organization(
        user=user,
        name="Test Organization",
        slug="test-organization",
        description="A test organization.",
    )

    membership = Membership.objects.get(
        user=user,
        organization=organization,
    )

    assert membership.role == Membership.Role.OWNER


# This tests creates a valid invitation to create membership


@pytest.mark.django_db
def test_accept_invitation_create(user, organization):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    membership = accept_invitation(
        invitation=invitation,
        user=user,
    )

    assert membership.user == user
    assert membership.organization == organization
    assert membership.role == Membership.Role.MEMBER


# Test for correct role is assigned
@pytest.mark.django_db
def test_accept_invitation_assigns_correct_role(user, organization):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.ADMIN,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    membership = accept_invitation(invitation=invitation, user=user)

    assert membership.role == Membership.Role.ADMIN


@pytest.mark.django_db
def test_accept_invitation_sets_accepted_at(user, organization):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    assert invitation.accepted_at is None

    accept_invitation(
        invitation=invitation,
        user=user,
    )

    invitation.refresh_from_db()

    assert invitation.accepted_at is not None
    assert invitation.declined_at is None


@pytest.mark.django_db
def test_accepted_invitation_cannot_be_accepted_again(user, organization):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
        accepted_at=timezone.now(),
    )

    with pytest.raises(
        ValidationError,
        match="This invitation has already been accepted.",
    ):
        accept_invitation(
            invitation=invitation,
            user=user,
        )


@pytest.mark.django_db
def test_expired_invitation_rejected(user, organization):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    with pytest.raises(
        ValidationError,
        match="This invitation has expired.",
    ):
        accept_invitation(
            invitation=invitation,
            user=user,
        )


@pytest.mark.django_db
def test_wrong_user_cannot_accept_invitation(user, organization):
    other_user = User.objects.create_user(
        email="other@example.com",
        first_name="Other",
        last_name="User",
        password="testpassword123!",
    )

    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    with pytest.raises(
        ValidationError,
        match="This invitation is not for the current user.",
    ):
        accept_invitation(
            invitation=invitation,
            user=other_user,
        )


@pytest.mark.django_db
def test_existing_membership_reject(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.ADMIN,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    with pytest.raises(
        ValidationError, match="This user is already a member of the organization."
    ):
        accept_invitation(
            invitation=invitation,
            user=user,
        )


# Decline Invitation tests
@pytest.mark.django_db
def test_decline_invitation_successfully(user, organization):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    decline_invitation(
        invitation=invitation,
        user=user,
    )

    invitation.refresh_from_db()

    assert invitation.declined_at is not None
    assert invitation.accepted_at is None


@pytest.mark.django_db
def test_accepted_invitation_cannot_be_decline(user, organization):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
        accepted_at=timezone.now(),
    )

    with pytest.raises(
        ValidationError,
        match="This invitation has already been accepted.",
    ):
        decline_invitation(
            invitation=invitation,
            user=user,
        )


@pytest.mark.django_db
def test_expired_invitation_cannot_be_declined(user, organization):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    with pytest.raises(
        ValidationError,
        match="This invitation has expired.",
    ):
        decline_invitation(
            invitation=invitation,
            user=user,
        )


@pytest.mark.django_db
def test_wrong_user_cannot_decline_invitation(user, organization):
    other_user = User.objects.create_user(
        email="other@example.com",
        first_name="Other",
        last_name="User",
        password="testpassword123",
    )

    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    with pytest.raises(
        ValidationError,
        match="This invitation was sent to a different address.",
    ):
        decline_invitation(
            invitation=invitation,
            user=other_user,
        )


@pytest.mark.django_db
def test_accept_invitation_rolls_back_when_membership_creation_fails(
    user,
    organization,
):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    with patch(
        "apps.organizations.services.Membership.objects.create",
        side_effect=Exception("Membership creation failed"),
    ):
        with pytest.raises(Exception, match="Membership creation failed"):
            accept_invitation(
                invitation=invitation,
                user=user,
            )

    invitation.refresh_from_db()

    assert invitation.accepted_at is None

    assert not Membership.objects.filter(
        organization=organization,
        user=user,
    ).exists()


@pytest.mark.django_db
def test_accept_invitation_rolls_back_membership_if_invitation_update_fails(
    user,
    organization,
):
    invitation = Invitation.objects.create(
        organization=organization,
        email=user.email,
        role=Invitation.Role.MEMBER,
        invited_by=user,
        expires_at=timezone.now() + timedelta(days=3),
    )

    with patch(
        "apps.organizations.services.Invitation.save",
        side_effect=Exception("Invitation update failed"),
    ):
        with pytest.raises(Exception, match="Invitation update failed"):
            accept_invitation(
                invitation=invitation,
                user=user,
            )

    invitation.refresh_from_db()

    assert invitation.accepted_at is None

    assert not Membership.objects.filter(
        organization=organization,
        user=user,
    ).exists()
