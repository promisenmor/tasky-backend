from .models import User
from .tasks import send_verification_email_task


def register_user(*, serializer):
    """
    Register a new user and trigger the email verification process
    """
    user = serializer.save()

    # Queue email sending
    send_verification_email_task.delay(str(user.id))

    return user


def resend_verification_email(*, email):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return

    if user.is_email_verified:
        return

    send_verification_email_task.delay(user.id)
