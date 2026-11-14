from rest_framework import serializers

from .models import Project, Section


class ProjectSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )
    created_by_email = serializers.EmailField(
        source="created_by.email",
        read_only=True,
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "organization",
            "organization_name",
            "name",
            "description",
            "status",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "organization_name",
            "status",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Project name cannot be empty.")

        organization = self.context.get("organization")

        if organization:
            queryset = Project.objects.filter(
                organization=organization,
                name__iexact=value,
            )

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "A project with this name already exists in the organization."
                )
        return value

    def validate_description(self, value):
        value = value.strip()
        return value


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Project name cannot be empty.")

        organization = self.context.get("organization")

        if Project.objects.filter(
            organization=organization,
            name__iexact=value,
        ).exists():
            raise serializers.ValidationError(
                "A project with this name already exists in the organization."
            )
        return value

    def validate_description(self, value):
        return value.strip()


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = [
            "id",
            "project",
            "name",
            "description",
            "position",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "project", "position", "created_at", "updated_at"]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Section name cannot be empty.")

        return value

    def validate_description(self, value):
        if value is not None:
            return value.strip()

        return value


class SectionReorderSerializer(serializers.Serializer):
    position = serializers.IntegerField(min_value=0)
