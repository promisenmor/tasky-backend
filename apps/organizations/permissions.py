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
