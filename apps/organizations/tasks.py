from celery import shared_task
from django.conf import settings
from django.urls import reverse

from .email import send_invitation_email
from .models import Invitation


@shared_task
def send_invitation_email_task(invitation_id):
    """
    Generate an invitation link and send it to the invited user.
    """
    try:
        invitation = Invitation.objects.select_related(
            "organization",
            "invited_by",
        ).get(id=invitation_id)

    except Invitation.DoesNotExist:
        return

    invitation_url = f"{settings.BACKEND_URL}{reverse('accept-invitation', kwargs={'invitation_id': invitation.id})}"

    send_invitation_email(
        invitation=invitation,
        invitation_url=invitation_url,
    )
