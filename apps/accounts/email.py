from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_verification_email(user, verification_url):
    """
    send an email verification message
    """

    context = {
        "user": user,
        "verification_url": verification_url,
    }

    subject = "Verify your Tasky account"

    text_content = render_to_string(
        "accounts/emails/verify_email.txt",
        context,
    )

    html_content = render_to_string(
        "accounts/emails/verify_email.html",
        context,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")

    email.send()
