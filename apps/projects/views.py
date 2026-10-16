from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organizations.models import Organization
from apps.organizations.permissions import (
    IsOrganizationAdmin,
    IsOrganizationMember,
)
from apps.projects.models import Project
from apps.projects.serializers import (
    ProjectCreateSerializer,
    ProjectSerializer,
)
from apps.projects.services import (
    create_project,
)


class ProjectListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination for this view

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsOrganizationAdmin()]

        return [IsAuthenticated(), IsOrganizationMember()]

    def _get_organization(self):
        organization = get_object_or_404(
            Organization,
            id=self.kwargs["organization_id"],
        )

        self.check_object_permissions(self.request, organization)
        return organization

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectCreateSerializer

        return ProjectSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organization"] = self._get_organization()
        return context

    def get_queryset(self):
        organization = self._get_organization()

        return (
            Project.objects.filter(organization=organization)
            .select_related("organization", "created_by")
            .order_by("name")
        )

    def create(self, request, *args, **kwargs):
        organization = self._get_organization()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = create_project(
                organization=organization,
                created_by=request.user,
                **serializer.validated_data,
            )
        except IntegrityError as exc:
            if "unique_project_name_per_organization" in str(exc):
                raise serializers.ValidationError(
                    {
                        "name": (
                            "A Project with this name already exists "
                            "in this organization."
                        )
                    }
                ) from exc
            raise
        except ValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
