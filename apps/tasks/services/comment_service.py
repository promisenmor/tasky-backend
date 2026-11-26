from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.organizations.models import Membership
from apps.projects.models import Project
from apps.tasks.models import Comment


def _get_membership(user, task):
    """This enusres the user belongs to the organization"""

    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    membership = Membership.objects.filter(
        user=user,
        organization=task.project.organization,
    ).first()

    if membership is None:
        raise PermissionDenied("You are not a member of this organization")

    return membership


def _validate_task(task):
    if task.archived:
        raise ValidationError("Cannot comment on an archived task")

    if task.project.status == Project.Status.ARCHIVED:
        raise ValidationError("Cannot comment on a task in an archived project.")


def _validate_body(body):
    if not body or not body.strip():
        raise ValidationError({"body": "Comment cannot be empty."})


@transaction.atomic
def create_comment(*, task, user, body):
    """create a comment on a task."""

    _get_membership(user, task)
    _validate_task(task)
    _validate_body(body)

    return Comment.objects.create(
        task=task,
        author=user,
        body=body.strip(),
    )


@transaction.atomic
def update_comment(*, comment, user, body):
    """this update a comment. Only the author can edit it."""

    _get_membership(user, comment.task)
    _validate_task(comment.task)
    _validate_body(body)

    if comment.author_id != user.id:
        raise PermissionDenied("You can only edit you own comments.")

    comment.body = body.strip()
    comment.edited = True
    comment.save(update_fields=["body", "edited"])

    return comment
