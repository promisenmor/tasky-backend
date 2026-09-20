from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import User
from apps.organizations.models import (
    Invitation,
    Membership,
    Organization,
    Team,
    TeamMembership,
)
from apps.organizations.services import (
    accept_invitation,
    add_team_member,
    create_organization,
    create_team,
    decline_invitation,
    delete_team,
    remove_team_member,
    update_team,
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


@pytest.mark.django_db
def test_create_team_and_creates_team_and_creator_membership(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    team = create_team(
        organization=organization,
        created_by=user,
        name="Backend",
        description="Backend engineering team",
    )

    assert team.organization == organization
    assert team.created_by == user
    assert team.name == "Backend"
    assert team.description == "Backend engineering team"

    assert TeamMembership.objects.filter(
        team=team,
        membership__user=user,
        membership__organization=organization,
    ).exists()


@pytest.mark.django_db
def create_team_strips_name_and_description(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    team = create_team(
        organization=organization,
        created_by=user,
        name=" Backend ",
        description=" Backend team ",
    )

    assert team.name == "Backend"
    assert team.description == "Backend team"


@pytest.mark.django_db
def test_create_team_requires_creator_membership(user, organization):
    with pytest.raises(Membership.DoesNotExist):
        create_team(
            organization=organization,
            created_by=user,
            name="Backend",
            description="Backend team",
        )

        assert not Team.objects.filter(
            organization=organization,
            name="Backend",
        ).exists()


@pytest.mark.django_db
def test_create_team_duplicate_name_rejected(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    create_team(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    with pytest.raises(IntegrityError):
        create_team(
            organization=organization,
            created_by=user,
            name="Backend",
        )


@pytest.mark.django_db
def test_updated_team_updates_name_and_description(user, organization):
    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
        description="Old Description",
    )

    updated_team = update_team(
        team=team,
        actor=user,
        name="Platform",
        description="New description",
    )

    team.refresh_from_db()

    assert updated_team == team
    assert team.name == "Platform"
    assert team.description == "New description"


@pytest.mark.django_db
def test_update_team_strips_name_and_description(user, organization):
    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
        description="Old description",
    )

    update_team(
        team=team,
        actor=user,
        name=" Platform ",
        description=" New description ",
    )

    team.refresh_from_db()

    assert team.name == "Platform"
    assert team.description == "New description"


@pytest.mark.django_db
def test_update_team_can_update_only_name(user, organization):
    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
        description="Backend team",
    )

    update_team(
        team=team,
        actor=user,
        name="Platform",
    )

    team.refresh_from_db()

    assert team.name == "Platform"
    assert team.description == "Backend team"


@pytest.mark.django_db
def test_update_team_can_update_only_description(user, organization):
    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
        description="Backend team",
    )

    update_team(
        team=team,
        actor=user,
        description="Platform team",
    )

    team.refresh_from_db()

    assert team.name == "Backend"
    assert team.description == "Platform team"


@pytest.mark.django_db
def test_delete_team_removes_team(user, organization):
    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    delete_team(
        team=team,
        actor=user,
    )

    assert not Team.objects.filter(id=team.id).exists()


@pytest.mark.django_db
def test_add_team_member_successfully(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    member_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )

    member_membership = Membership.objects.create(
        user=member_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    team_membership = add_team_member(
        team=team,
        membership=member_membership,
        actor=user,
    )

    assert team_membership.team == team
    assert team_membership.membership == member_membership

    assert TeamMembership.objects.filter(
        team=team,
        membership=member_membership,
    ).exists()


@pytest.mark.django_db
def test_admin_can_add_team_member(organization):
    admin = User.objects.create_user(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="testpassword123",
    )

    member_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )

    Membership.objects.create(
        user=admin,
        organization=organization,
        role=Membership.Role.ADMIN,
    )

    member_membership = Membership.objects.create(
        user=member_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization, created_by=admin, name="Backend"
    )

    team_membership = add_team_member(
        team=team,
        membership=member_membership,
        actor=admin,
    )

    assert team_membership.membership == member_membership


@pytest.mark.django_db
def test_member_cannot_add_team_member(user, organization):
    admin = User.objects.create_user(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="testpassword123",
    )

    member_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )

    Membership.objects.create(
        user=admin,
        organization=organization,
        role=Membership.Role.ADMIN,
    )

    member_membership = Membership.objects.create(
        user=member_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization, created_by=admin, name="Backend"
    )

    with pytest.raises(ValidationError):
        add_team_member(
            team=team,
            membership=member_membership,
            actor=member_user,
        )

    assert not TeamMembership.objects.filter(
        team=team,
        membership=member_membership,
    ).exists()


@pytest.mark.django_db
def test_cannot_add_member_from_different_organization(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    other_organization = Organization.objects.create(
        name="Other Organization",
        slug="other-organization",
    )

    other_user = User.objects.create_user(
        email="other@example.com",
        first_name="Other",
        last_name="User",
        password="testpassword123",
    )

    other_membership = Membership.objects.create(
        user=other_user,
        organization=other_organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    with pytest.raises(
        ValidationError,
        match="Membership does not belong to the same organization as the team.",
    ):
        add_team_member(
            team=team,
            membership=other_membership,
            actor=user,
        )

    assert not TeamMembership.objects.filter(
        team=team,
        membership=other_membership,
    ).exists()


@pytest.mark.django_db
def test_duplicate_team_membership_rejected(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    member_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )

    member_membership = Membership.objects.create(
        user=member_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    add_team_member(
        team=team,
        membership=member_membership,
        actor=user,
    )

    assert (
        TeamMembership.objects.filter(
            team=team,
            membership=member_membership,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_remove_team_member_successfully(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    member_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )

    member_membership = Membership.objects.create(
        user=member_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    TeamMembership.objects.create(
        team=team,
        membership=member_membership,
    )

    remove_team_member(
        team=team,
        membership=member_membership,
        actor=user,
    )

    assert not TeamMembership.objects.filter(
        team=team,
        membership=member_membership,
    ).exists()


@pytest.mark.django_db
def test_admin_can_remove_team_member(organization):
    admin = User.objects.create_user(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="testpassword123",
    )

    Membership.objects.create(
        user=admin,
        organization=organization,
        role=Membership.Role.ADMIN,
    )

    member_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )

    member_membership = Membership.objects.create(
        user=member_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization,
        created_by=admin,
        name="Backend",
    )

    TeamMembership.objects.create(
        team=team,
        membership=member_membership,
    )

    remove_team_member(
        team=team,
        membership=member_membership,
        actor=admin,
    )

    assert not TeamMembership.objects.filter(
        team=team,
        membership=member_membership,
    ).exists()


@pytest.mark.django_db
def test_member_cannot_remove_team_member(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    member_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )

    member_membership = Membership.objects.create(
        user=member_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    TeamMembership.objects.create(
        team=team,
        membership=member_membership,
    )

    with pytest.raises(
        ValidationError,
        match="You do not have permission to remove members from this team.",
    ):
        remove_team_member(
            team=team,
            membership=member_membership,
            actor=user,
        )

    assert TeamMembership.objects.filter(
        team=team,
        membership=member_membership,
    ).exists()


@pytest.mark.django_db
def test_cannot_remove_member_from_different_organization(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    other_organization = Organization.objects.create(
        name="Other Organization",
        slug="other-organization",
    )

    other_user = User.objects.create_user(
        email="other@example.com",
        first_name="Other",
        last_name="User",
        password="testpassword123",
    )

    other_membership = Membership.objects.create(
        user=other_user,
        organization=other_organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    with pytest.raises(
        ValidationError,
        match="Membership does not belong to the same organization as the team.",
    ):
        remove_team_member(
            team=team,
            membership=other_membership,
            actor=user,
        )


@pytest.mark.django_db
def test_remove_team_member_not_in_team_rejected(user, organization):
    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    member_user = User.objects.create_user(
        email="member@example.com",
        first_name="Member",
        last_name="User",
        password="testpassword123",
    )

    member_membership = Membership.objects.create(
        user=member_user,
        organization=organization,
        role=Membership.Role.MEMBER,
    )

    team = Team.objects.create(
        organization=organization,
        created_by=user,
        name="Backend",
    )

    with pytest.raises(
        ValidationError,
        match="This member is not part of the team.",
    ):
        remove_team_member(
            team=team,
            membership=member_membership,
            actor=user,
        )
