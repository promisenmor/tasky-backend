from django.urls import path

from .views import (
    OrganizationCreateView,
    OrganizationDetailView,
    OrganizationListView,
)

urlpatterns = [
    path(
        "",
        OrganizationListView.as_view(),
        name="organization-list",
    ),
    path("create/", OrganizationCreateView.as_view(), name="create-organization"),
    path("<uuid:pk>/", OrganizationDetailView.as_view(), name="organization-detail"),
]
