from rest_framework.permissions import BasePermission

from .models import Membership


class IsOrganizationMember(BasePermission):
    """
    Allows access only to users who are members of the organization.
    """

    message = "You must be a member of this organization."

    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", obj)
        return Membership.objects.filter(
            user=request.user,
            organization=organization,
        ).exists()


class IsOrganizationAdmin(BasePermission):
    """
    Allows organization owners and admins
    """

    message = "You must be an admin or owner of this organization."

    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", obj)
        membership = Membership.objects.filter(
            user=request.user,
            organization=organization,
        ).first()

        if membership is None:
            return False

        return membership.role in {
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        }


class IsMembershipManager(BasePermission):
    """
    Allows organization owners and admins to manage memberships.
    """

    message = (
        "You must be an admin or owner of this organization to manage memberships."
    )

    def has_object_permission(self, request, view, obj):
        requester_membership = Membership.objects.filter(
            user=request.user,
            organization=obj.organization,
        ).first()

        if requester_membership is None:
            return False

        return requester_membership.role in {
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        }


def is_organization_admin(*, user, organization):
    """check if a user is an admin or owner of an organization."""
    return Membership.objects.filter(
        user=user,
        organization=organization,
        role__in=[
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        ],
    ).exists()
