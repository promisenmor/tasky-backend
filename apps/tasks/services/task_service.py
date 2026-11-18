from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import Membership
from apps.projects.models import Project
from apps.tasks.models import Task

ADMIN_ROLES = (
    Membership.Role.OWNER,
    Membership.Role.ADMIN,
)

EDITABLE_FIELDS = {
    "title",
    "description",
    "priority",
    "status",
    "due_date",
}


def _get_memebership(user, project):
    """This will return the user's membership in the project's organizaton."""

    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    membership = Membership.objects.filter(
        user=user,
        organization=project.organization,
    ).first()

    if membership is None:
        raise PermissionDenied("You are not a member of this organization.")

    return membership


def _require_admin(user, project):
    """This ensure the user is an organization ONWER or ADMIN."""

    membership = _get_memebership(user, project)

    if membership.role not in ADMIN_ROLES:
        raise PermissionDenied(
            "Only organization onwers and admins can perform this action."
        )

    return membership


def _validate_task_data(title, priority, status):
    """This validate task fields before saving."""

    if not title or not title.strip():
        raise ValidationError({"title": "Task title cannot be empty."})

    if priority not in Task.Priority.values:
        raise ValidationError({"priority": "Invalid task priority."})

    if status not in Task.Status.values:
        raise ValidationError({"status:Invalid task status."})


@transaction.atomic
def create_task(
    *,
    project,
    user,
    title,
    description=None,
    priority=Task.Priority.MEDIUM,
    status=Task.Status.TODO,
    due_date=None,
):
    """This create a task inside an organization's project."""

    _get_memebership(user, project)

    if project.status != Project.Status.ACTIVE:
        raise ValidationError("Cannot create a tasks in an archieved project.")

    _validate_task_data(title, priority, status)

    return Task.objects.create(
        project=project,
        created_by=user,
        title=title.strip(),
        description=description,
        priority=priority,
        status=status,
        due_date=due_date,
        completed_at=(timezone.now() if status == Task.Status.COMPLETED else None),
    )


@transaction.atomic
def update_task(*, task, user, **data):
    """this update an existing task."""

    _get_memebership(user, task.project)

    if task.archived:
        raise ValidationError("Cannot update an archived task. Restore it first.")

    if task.project.status != Project.Status.ACTIVE:
        raise ValidationError("Cannot update tasks in archived project.")

    invalid_fields = set(data) - EDITABLE_FIELDS

    if invalid_fields:
        raise ValidationError({"fields": "These fields cannot be updated."})

    if not data:
        return task

    title = data.get("title", task.title)
    priority = data.get("priority", task.priority)
    status = data.get("status", task.status)

    _validate_task_data(title, priority, status)

    for field, value in data.items():
        setattr(task, field, value.strip() if field == "title" else value)

    if status == Task.Status.COMPLETED and task.completed_at is None:
        task.completed_at = timezone.now()

    elif status != Task.Status.COMPLETED:
        task.completed_at = None

    task.save()

    return task


@transaction.atomic
def archive_task(*, task, user):
    """Archive a task. Only OWNER and ADMIN can do this."""

    _require_admin(user, task.project)

    task.archived = True
    task.save(update_fields=["archived"])

    return task


@transaction.atomic
def restore_task(*, task, user):
    """Restore an archived task. Only OWNER and ADMIN can restore a project"""

    _require_admin(user, task.project)

    task.archived = False
    task.save(update_fields=["archived"])

    return task
