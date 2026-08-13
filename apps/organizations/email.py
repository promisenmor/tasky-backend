from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_invitation_email(*, invitation, invitation_url):
    """
    Send an organization invitation email.
    """

    context = {
        "invitation": invitation,
        "invitation_url": invitation_url,
    }

    subject = f"You've been invited to join {invitation.organization.name} on Tasky"

    text_content = render_to_string(
        "organizations/emails/invitation_email.txt",
        context,
    )

    html_content = render_to_string(
        "organizations/emails/invitation_email.html",
        context,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invitation.email],
    )

    email.attach_alternative(html_content, "text/html")

    email.send()
