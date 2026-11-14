from django.urls import path

from apps.projects.views import (
    ProjectArchiveView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectRestoreView,
    SectionDetailView,
    SectionListCreateView,
    SectionReorderView,
)

urlpatterns = [
    # Projects
    path(
        "<uuid:organization_id>/projects/",
        ProjectListCreateView.as_view(),
        name="project-list-create",
    ),
    path(
        "<uuid:organization_id>/projects/<uuid:project_id>/",
        ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "<uuid:organization_id>/projects/<uuid:project_id>/archive/",
        ProjectArchiveView.as_view(),
        name="project-archive",
    ),
    path(
        "<uuid:organization_id>/projects/<uuid:project_id>/restore/",
        ProjectRestoreView.as_view(),
        name="project-restore",
    ),
    # Sections
    # Sections
    path(
        "<uuid:organization_id>/projects/<uuid:project_id>/sections/",
        SectionListCreateView.as_view(),
        name="section-list-create",
    ),
    path(
        "<uuid:organization_id>/projects/<uuid:project_id>/sections/<uuid:section_id>/",
        SectionDetailView.as_view(),
        name="section-detail",
    ),
    path(
        "<uuid:organization_id>/projects/<uuid:project_id>/sections/<uuid:section_id>/reorder/",
        SectionReorderView.as_view(),
        name="section-reorder",
    ),
]
