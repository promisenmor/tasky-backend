from django.urls import path

from .views import (
    InvitationCreateView,
    MembershipDetailView,
    MembershipListView,
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
    path(
        "create/",
        OrganizationCreateView.as_view(),
        name="create-organization",
    ),
    path(
        "<uuid:pk>/",
        OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
    path(
        "<uuid:organization_id>/invitations/",
        InvitationCreateView.as_view(),
        name="create-invitation",
    ),
    path(
        "<uuid:organization_id>/members/",
        MembershipListView.as_view(),
        name="list-members",
    ),
    path(
        "<uuid:organization_id>/members/<uuid:membership_id>/",
        MembershipDetailView.as_view(),
        name="detail-member",
    ),
]
