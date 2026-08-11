from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Organization
from .permissions import IsOrganizationMember
from .serializers import (
    OgranizationCreateSerailizer,
    OrganizationSerializer,
)
from .services import create_organization


class OrganizationCreateView(generics.CreateAPIView):
    serializer_class = OgranizationCreateSerailizer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializeer = self.get_serializer(data=request.data)
        serializeer.is_valid(raise_exception=True)

        organization = create_organization(
            user=request.user,
            **serializeer.validated_data,
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
