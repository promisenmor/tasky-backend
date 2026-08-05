from .models import User
from .tasks import send_password_reset_email_task, send_verification_email_task
from .tokens import password_reset_token


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


def request_password_reset(*, email):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return

    if not user.is_active:
        return

    token = password_reset_token.make_token(user)

    send_password_reset_email_task.delay(
        user.id,
        token,
    )
