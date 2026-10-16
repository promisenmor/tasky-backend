from django.urls import path

from apps.projects.views import ProjectListCreateView

urlpatterns = [
    path(
        "organizations/<uuid:organization_id>/projects/",
        ProjectListCreateView.as_view(),
        name="project-list-create",
    ),
]
