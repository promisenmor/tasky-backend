from celery import shared_task
from django.conf import settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .email import send_verification_email
from .models import User
from .tokens import email_verification_token


@shared_task
def send_verification_email_task(user_id):
    """
    Generate a verification link and send it to the user.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)

    path = reverse(
        "verify-email",
        kwargs={
            "uidb64": uid,
            "token": token,
        },
    )

    verification_url = f"{settings.BACKEND_URL}{path}"

    try:
        send_verification_email(
            user=user,
            verification_url=verification_url,
        )
    except Exception:
        raise
