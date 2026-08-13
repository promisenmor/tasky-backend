from rest_framework.permissions import BasePermission

from .models import Membership


class IsOrganizationMember(BasePermission):
    """
    Allows access only to users who are members of the organization.
    """

    def has_object_permission(self, request, view, obj):
        return Membership.objects.filter(
            user=request.user,
            organization=obj,
        ).exists()


class IsOrganizationAdmin(BasePermission):
    """
    Allows organization owners and admins
    """

    def has_object_permission(self, request, view, obj):
        membership = Membership.objects.filter(
            user=request.user,
            organization=obj,
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
