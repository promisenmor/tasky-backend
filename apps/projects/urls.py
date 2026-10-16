from django.urls import path

from apps.projects.views import (
    ProjectArchiveView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectRestoreView,
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
]
