from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.organizations.models import Membership
from apps.tasks.models import Label, TaskLabel


def _get_membership(user, organization):
    """Ensure the acting user belongs to the organisation."""

    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    membership = Membership.objects.filter(
        user=user,
        organization=organization,
    ).first()

    if membership is None:
        raise PermissionDenied("You are not a member of this organisation.")

    return membership


def _validate_task(task):
    if task.archived:
        raise ValidationError("Cannot manage labels on an archived task.")

    if task.project.status != task.project.Status.ACTIVE:
        raise ValidationError("Cannot manage labels in an archived project.")


@transaction.atomic
def create_label(*, organization, user, name):
    """Create a reusable label within an organisation."""

    _get_membership(user, organization)

    if not name or not name.strip():
        raise ValidationError({"name": "Label name cannot be empty."})

    name = name.strip()

    if Label.objects.filter(
        organization=organization,
        name=name,
    ).exists():
        raise ValidationError({"name": "A label with this name already exists."})

    return Label.objects.create(
        organization=organization,
        name=name,
    )


@transaction.atomic
def attach_label_to_task(*, task, label, user):
    """Attach an existing organisation label to a task."""

    _get_membership(user, task.project.organization)
    _validate_task(task)

    if label.organization_id != task.project.organization_id:
        raise ValidationError("The label must belong to the task's organisation.")

    if TaskLabel.objects.filter(task=task, label=label).exists():
        raise ValidationError("This label is already attached to the task.")

    return TaskLabel.objects.create(
        task=task,
        label=label,
    )


@transaction.atomic
def remove_label_from_task(*, task, label, user):
    """Remove a label association without deleting the label."""

    _get_membership(user, task.project.organization)
    _validate_task(task)

    task_label = TaskLabel.objects.filter(
        task=task,
        label=label,
    ).first()

    if task_label is None:
        raise ValidationError("This label is not attached to the task.")

    task_label.delete()

    return True
