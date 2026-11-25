from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.organizations.models import Membership
from apps.tasks.models import TaskAssignee


def _get_actor_memebership(user, task):
    """This ensure the acting user belongs to the task's organization."""

    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    membership = Membership.objects.filter(
        user=user,
        organization=task.project.organization,
    ).first()

    if membership is None:
        raise PermissionDenied("You are not a member of this organization.")

    return membership


def _validate_task(task):
    if task.archived:
        raise ValidationError("Cannot manage assignees in an archived project.")

    if task.project.status != task.project.Status.ACTIVE:
        raise ValidationError("Cannot manage assignees in archive project.")


@transaction.atomic
def assign_user_to_task(*, task, organization_membership, user):
    """This assign an organization member to a task."""

    _get_actor_memebership(user, task)
    _validate_task(task)

    if organization_membership.organization_id != task.project.organization_id:
        raise ValidationError("The assignee must belong to the task organization.")

    if TaskAssignee.objects.filter(
        task=task,
        organization_membership=organization_membership,
    ).exists():
        raise ValidationError("This member is already assigned to the task.")

    return TaskAssignee.objects.create(
        task=task, organization_membership=organization_membership
    )


@transaction.atomic
def remove_user_from_task(*, task, organization_membership, user):
    """Remove an organization member from a task."""

    _get_actor_memebership(user, task)
    _validate_task(task)

    assignment = TaskAssignee.objects.filter(
        task=task, organization_membership=organization_membership
    ).first()

    if assignment is None:
        raise ValidationError("This member is not assigned to the task.")

    assignment.delete()

    return True
