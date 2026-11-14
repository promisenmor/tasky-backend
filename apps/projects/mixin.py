from django.shortcuts import get_object_or_404

from apps.organizations.models import Organization
from apps.projects.models import Project, Section

# This SectionProjectMixin is designed to help your views retrieve a Project
# and its Section while making sure they belong to the correct Organization


class SectionProjectMixin:
    def get_project(self, request):
        organization = get_object_or_404(
            Organization,
            id=self.kwargs["organization_id"],
        )

        self.check_object_permissions(request, organization)

        return get_object_or_404(
            Project.objects.select_related("organization"),
            id=self.kwargs["project_id"],
            organization=organization,
        )

    def get_section(self, request):
        project = self.get_project(request)

        return get_object_or_404(
            Section.objects.select_related("project", "project__organization"),
            id=self.kwargs["section_id"],
            project=project,
        )
