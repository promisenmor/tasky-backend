from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Membership,
    Organization,
)
from .permissions import (
    IsMembershipManager,
    IsOrganizationMember,
)
from .serializers import (
    InvitationCreateSerializer,
    InvitationSerializer,
    MembershipSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
)
from .services import create_invitation, create_organization


class OrganizationCreateView(generics.CreateAPIView):
    serializer_class = OrganizationCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = create_organization(
            user=request.user,
            **serializer.validated_data,
        )

        return Response(
            OrganizationSerializer(organization).data, status=status.HTTP_201_CREATED
        )


class OrganizationListView(generics.ListAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user
        ).distinct()


class OrganizationDetailView(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [
        IsAuthenticated,
        IsOrganizationMember,
    ]

    queryset = Organization.objects.all()


class InvitationCreateView(generics.CreateAPIView):
    serializer_class = InvitationCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOrganizationMember,
    ]

    def get_organization(self):
        return get_object_or_404(
            Organization,
            id=self.kwargs["organization_id"],
        )

    def create(self, request, *args, **kwargs):
        organization = self.get_organization()

        self.check_object_permissions(
            request,
            organization,
        )

        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        try:
            invitation = create_invitation(
                organization=organization,
                invited_by=request.user,
                **serializer.validated_data,
            )

        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            InvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class MembershipListView(generics.ListAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [
        IsAuthenticated,
        IsOrganizationMember,
    ]

    def get_queryset(self):
        organization = get_object_or_404(
            Organization,
            id=self.kwargs["organization_id"],
        )

        self.check_object_permissions(
            self.request,
            organization,
        )

        return Membership.objects.filter(organization=organization).select_related(
            "user"
        )


class MembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MembershipSerializer
    queryset = Membership.objects.select_related("user", "organization")

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [
                IsAuthenticated,
                IsOrganizationMember,
            ]
        else:
            permission_classes = [
                IsAuthenticated,
                IsMembershipManager,
            ]

        return [permission() for permission in permission_classes]

    def get_object(self):
        organization = get_object_or_404(
            Organization,
            id=self.kwargs["organization_id"],
        )

        membership = get_object_or_404(
            Membership.objects.select_related("user", "organization"),
            id=self.kwargs["membership_id"],
            organization=organization,
        )

        self.check_object_permissions(
            self.request,
            membership,
        )

        return membership
