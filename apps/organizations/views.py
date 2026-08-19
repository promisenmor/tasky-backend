from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Invitation,
    Membership,
    Organization,
)
from .permissions import (
    IsMembershipManager,
    IsOrganizationMember,
)
from .serializers import (
    InvitationCreateSerializer,
    InvitationDetailSerailizer,
    InvitationSerializer,
    MembershipSerializer,
    MembershipUpdateSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
)
from .services import (
    accept_invitation,
    change_member_role,
    create_invitation,
    create_organization,
    decline_invitation,
    leave_organization,
    remove_member,
)


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


@extend_schema(
    request=None,
    responses={201: MembershipSerializer},
)
class InvitationAcceptView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invitation = get_object_or_404(
            Invitation,
            token=token,
        )

        try:
            membership = accept_invitation(
                invitation=invitation,
                user=request.user,
            )

        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=None,
    responses={200: serializers.Serializer()},
)
class InvitationDeclineView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)

        try:
            decline_invitation(
                invitation=invitation,
                user=request.user,
            )

        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            {"detail": "Invitation declined successfully."}, status=status.HTTP_200_OK
        )


class InvitationDetailView(generics.RetrieveAPIView):
    serializer_class = InvitationDetailSerailizer
    permission_classes = [AllowAny]
    lookup_field = "token"

    def get_queryset(self):
        return Invitation.objects.select_related(
            "organization",
            "invited_by",
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
    queryset = Membership.objects.select_related("user", "organization")

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return MembershipUpdateSerializer

        return MembershipSerializer

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

    def perform_update(self, serializer):
        membership = self.get_object()

        try:
            change_member_role(
                membership=membership,
                actor=self.request.user,
                new_role=serializer.validated_data["role"],
            )
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        membership.refresh_from_db()

    def perform_destroy(self, instance):
        try:
            remove_member(
                membership=instance,
                actor=self.request.user,
            )
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc


class OrganizationLeaveView(generics.GenericAPIView):
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def post(self, request, organization_id):
        organization = get_object_or_404(
            Organization,
            id=organization_id,
        )

        try:
            leave_organization(
                organization=organization,
                user=request.user,
            )
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            {"detail": "You have left the organization."}, status=status.HTTP_200_OK
        )
