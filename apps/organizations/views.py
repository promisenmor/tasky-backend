from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Invitation,
    Membership,
    Organization,
    Team,
    TeamMembership,
)
from .permissions import (
    IsMembershipManager,
    IsOrganizationAdmin,
    IsOrganizationMember,
)
from .serializers import (
    InvitationCreateSerializer,
    InvitationDetailSerializer,
    InvitationSerializer,
    MembershipSerializer,
    MembershipUpdateSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
    TeamCreateSerializer,
    TeamMemberCreateSerializer,
    TeamMemberSerializer,
    TeamSerializer,
)
from .services import (
    accept_invitation,
    add_team_member,
    change_member_role,
    create_invitation,
    create_organization,
    create_team,
    decline_invitation,
    delete_team,
    leave_organization,
    remove_member,
    remove_team_member,
    update_team,
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
    serializer_class = InvitationDetailSerializer
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
        membership = serializer.instance

        try:
            updated_membership = change_member_role(
                membership=membership,
                actor=self.request.user,
                new_role=serializer.validated_data["role"],
            )
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        serializer.instance = updated_membership
        updated_membership.refresh_from_db()

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


# Team views


class TeamListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsOrganizationAdmin()]
        return [IsAuthenticated(), IsOrganizationMember()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TeamCreateSerializer
        return TeamSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # `organization` is resolved in _get_organization(); stash it so the
        # serializer can access it during validation.
        context["organization"] = self._get_organization()
        return context

    def get_queryset(self):
        organization = self._get_organization()
        return (
            Team.objects.filter(organization=organization)
            .select_related("organization", "created_by")
            .annotate(member_count=Count("memberships"))
            .order_by("name")
        )

    def create(self, request, *args, **kwargs):
        organization = self._get_organization()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            team = create_team(
                organization=organization,
                created_by=request.user,
                **serializer.validated_data,
            )
        except IntegrityError as exc:
            if "unique_team_name_per_organization" in str(exc):
                raise serializers.ValidationError(
                    {
                        "name": "A team with this name already exists "
                        "in this organization."
                    }
                ) from exc
            raise
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            TeamSerializer(team).data,
            status=status.HTTP_201_CREATED,
        )

    def _get_organization(self):
        organization = get_object_or_404(
            Organization,
            id=self.kwargs["organization_id"],
        )
        self.check_object_permissions(self.request, organization)
        return organization


class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Team.objects.filter(
                organization_id=self.kwargs["organization_id"],
            )
            .select_related("organization", "created_by")
            .annotate(member_count=Count("memberships"))
        )

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return TeamCreateSerializer

        return TeamSerializer

    def get_object(self):
        team = get_object_or_404(
            self.get_queryset(),
            id=self.kwargs["pk"],
            organization_id=self.kwargs["organization_id"],
        )

        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            permission = IsOrganizationAdmin()

        else:
            permission = IsOrganizationMember()

        if not permission.has_object_permission(
            self.request,
            self,
            team.organization,
        ):
            self.permission_denied(
                self.request,
                message="You do not have permission to access this team.",
            )

        return team

    def update(self, request, *args, **kwargs):
        team = self.get_object()

        serializer = self.get_serializer(
            instance=team,
            data=request.data,
            partial=kwargs.pop("partial", False),
        )
        serializer.is_valid(raise_exception=True)

        try:
            team = update_team(
                team=team,
                actor=request.user,
                **serializer.validated_data,
            )
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            TeamSerializer(team).data,
        )

    def destroy(self, request, *args, **kwargs):
        team = self.get_object()

        try:
            delete_team(
                team=team,
                actor=request.user,
            )
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class TeamMemberListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def get_team(self):
        team = get_object_or_404(
            Team.objects.select_related("organization"),
            id=self.kwargs["team_id"],
            organization_id=self.kwargs["organization_id"],
        )

        self.check_object_permissions(
            self.request,
            team.organization,
        )

        return team

    def get_queryset(self):
        team = self.get_team()

        return TeamMembership.objects.filter(team=team).select_related(
            "membership__user",
            "membership__organization",
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TeamMemberCreateSerializer
        return TeamMemberSerializer

    def create(self, request, *args, **kwargs):
        team = self.get_team()
        self.check_object_permissions(request, team.organization)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = get_object_or_404(
            Membership,
            id=serializer.validated_data["membership_id"],
        )

        try:
            team_membership = add_team_member(
                team=team,
                membership=membership,
                actor=request.user,
            )

        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            TeamMemberSerializer(team_membership).data,
            status=status.HTTP_201_CREATED,
        )


class TeamMemberDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def get_object(self):
        team = get_object_or_404(
            Team,
            id=self.kwargs["team_id"],
            organization_id=self.kwargs["organization_id"],
        )

        self.check_object_permissions(
            self.request,
            team.organization,
        )

        membership = get_object_or_404(
            Membership,
            id=self.kwargs["membership_id"],
            organization=team.organization,
        )

        team_membership = get_object_or_404(
            TeamMembership,
            team=team,
            membership=membership,
        )

        return team_membership

    def perform_destroy(self, instance):
        try:
            remove_team_member(
                team=instance.team,
                membership=instance.membership,
                actor=self.request.user,
            )
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
