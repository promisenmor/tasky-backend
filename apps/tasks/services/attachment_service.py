from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.organizations.models import Membership
from apps.projects.models import Project
from apps.tasks.models import Attachment

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}


MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


def _get_membership(user, task):
    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication is required")

    membership = Membership.objects.filter(
        user=user, organization=task.project.organization
    ).first()

    if membership is None:
        raise PermissionDenied("You are not a member of this organization")

    return membership


def _validate_task(task):
    if task.archived:
        raise ValidationError("You cannot add an attachment to an archived task.")

    if task.project.status == Project.Status.ARCHIVED:
        raise ValidationError("You cannot add an attachment to an archived project.")


def _validate_attachment_type(*, file_size, mime_type):
    if not mime_type or mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError("File type not allowed")

    if file_size <= 0:
        raise ValidationError({"file": "File cannot be empty"})

    if file_size > MAX_ATTACHMENT_SIZE:
        raise ValidationError("File too large for the application")


@transaction.atomic
def create_attachment(*, task, user, file):
    _get_membership(user, task)
    _validate_task(task)
    _validate_attachment_type(
        file_size=file.size,
        mime_type=file.content_type,
    )

    return Attachment.objects.create(
        uploaded_by=user,
        task=task,
        file=file,
        file_size=file.size,
        mime_type=file.content_type,
    )


@transaction.atomic
def delete_attachment(*, attachment, user):
    _get_membership(user, attachment.task)

    if attachment.uploaded_by_id != user.id:
        raise PermissionDenied("You can only delete your own attachments.")

    attachment.delete()

    transaction.on_commit(
        lambda: attachment.file.delete(save=False)
    )  # Ensure the transaction is committed before returning
