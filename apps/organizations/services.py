from django.db import transaction

from .models import Membership, Organization


@transaction.atomic
def create_organization(*, user, name, slug, description=""):
    organization = Organization.objects.create(
        name=name,
        slug=slug,
        description=description,
    )

    Membership.objects.create(
        user=user,
        organization=organization,
        role=Membership.Role.OWNER,
    )

    return organization
