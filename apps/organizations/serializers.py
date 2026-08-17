from rest_framework import serializers

from apps.accounts.models import User

from .models import Invitation, Membership, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "description",
        ]

    def validate_slug(self, value):
        if Organization.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                "An organization with this slug already exists."
            )

        return value


class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(
        source="user.id",
        read_only=True,
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    full_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )

    initials = serializers.CharField(
        source="user.initials",
        read_only=True,
    )

    class Meta:
        model = Membership
        fields = [
            "id",
            "user_id",
            "email",
            "full_name",
            "initials",
            "role",
            "joined_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "email",
            "full_nameinitials",
            "joined_at",
        ]


class InvitationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ["email", "role"]

    def validate_email(self, value):
        return value.lower().strip()

    def validate_role(self, value):
        if value == Membership.Role.OWNER:
            raise serializers.ValidationError("An owner cannot be invited.")
        return value


class InvitationSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    invited_by_email = serializers.EmailField(
        source="invited_by.email",
        read_only=True,
    )

    is_expired = serializers.BooleanField(
        read_only=True,
    )

    is_accepted = serializers.BooleanField(
        read_only=True,
    )

    is_declined = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = Invitation
        fields = [
            "id",
            "organization",
            "organization_name",
            "email",
            "role",
            "invited_by",
            "invited_by_email",
            "expires_at",
            "accepted_at",
            "is_expired",
            "is_accepted",
            "declined_at",
            "is_declined",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "invited_by",
            "invited_by_email",
            "expires_at",
            "accepted_at",
            "declined_at",
            "is_declined",
            "is_expired",
            "is_accepted",
            "created_at",
            "updated_at",
        ]


class InvitationDetailSerailizer(serializers.ModelSerializer):
    organization = serializers.CharField(
        source="organization.name",
        read_only=True,
    )
    invited_by_name = serializers.CharField(
        source="invited_by.full_name",
        read_only=True,
    )
    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True,
    )
    requires_registration = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "id",
            "organization_name",
            "invited_by_name",
            "email",
            "role",
            "role_display",
            "expires_at",
            "accepted_at",
            "is_expired",
            "is_accepted",
            "requires_registration",
        ]

    def get_requires_registration(self, obj):
        return not User.objects.filter(email__iexact=obj.email).exists()
