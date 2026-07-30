from .tasks import send_verification_email_task


def register_user(*, serializer):
    """
    Register a new user and trigger the email verification process
    """
    user = serializer.save()

    # Queue email sending
    send_verification_email_task.delay(str(user.id))

    return user
