import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.tasks.services.task_service import (
    archive_task,
    create_task,
    restore_task,
    update_task,
)


@pytest.mark.django_db
def test_member_can_create_task(project, member_user):
    task = create_task(
        project=project,
        user=member_user,
        title="Implement authentication",
    )

    assert task.title == "Implement authentication"
    assert task.project == project
    assert task.created_by == member_user
    assert task.priority == Task.Priority.MEDIUM
    assert task.status == Task.Status.TODO


@pytest.mark.django_db
def test_admin_can_create_task(project, organization_admin_user):
    task = create_task(
        project=project,
        user=organization_admin_user,
        title="Review architecture",
    )

    assert task.created_by == organization_admin_user


@pytest.mark.django_db
def test_non_member_cannot_create_task(project, non_member_user):
    with pytest.raises(PermissionDenied):
        create_task(
            project=project,
            user=non_member_user,
            title="Unauthorised task",
        )


@pytest.mark.django_db
def test_cannot_create_task_in_archived_project(
    project,
    member_user,
):
    project.status = Project.Status.ARCHIVED
    project.save()

    with pytest.raises(ValidationError):
        create_task(
            project=project,
            user=member_user,
            title="New task",
        )


@pytest.mark.django_db
def test_member_can_update_task(project, user, member_user):
    task = create_task(
        project=project,
        user=user,
        title="Original title",
    )

    updated_task = update_task(
        task=task,
        user=member_user,
        title="Updated title",
        priority=Task.Priority.HIGH,
    )

    assert updated_task.title == "Updated title"
    assert updated_task.priority == Task.Priority.HIGH


@pytest.mark.django_db
def test_completing_task_sets_completed_at(project, user, member_user):
    task = create_task(
        project=project,
        user=user,
        title="Finish implementation",
    )

    updated_task = update_task(
        task=task,
        user=member_user,
        status=Task.Status.COMPLETED,
    )

    assert updated_task.status == Task.Status.COMPLETED
    assert updated_task.completed_at is not None


@pytest.mark.django_db
def test_reopening_task_clears_completed_at(project, user, member_user):
    task = create_task(
        project=project,
        user=user,
        title="Finish implementation",
        status=Task.Status.COMPLETED,
    )

    assert task.completed_at is not None

    updated_task = update_task(
        task=task,
        user=member_user,
        status=Task.Status.IN_PROGRESS,
    )

    assert updated_task.status == Task.Status.IN_PROGRESS
    assert updated_task.completed_at is None


@pytest.mark.django_db
def test_member_cannot_archive_task(project, user, member_user):
    task = create_task(
        project=project,
        user=user,
        title="Task to archive",
    )

    with pytest.raises(PermissionDenied):
        archive_task(task=task, user=member_user)

    task.refresh_from_db()
    assert task.archived is False


@pytest.mark.django_db
def test_admin_can_archive_task(project, user, organization_admin_user):
    task = create_task(
        project=project,
        user=user,
        title="Task to archive",
    )

    archive_task(task=task, user=organization_admin_user)

    task.refresh_from_db()
    assert task.archived is True


@pytest.mark.django_db
def test_admin_can_restore_task(project, user, organization_admin_user):
    task = create_task(
        project=project,
        user=user,
        title="Task to restore",
    )

    archive_task(task=task, user=organization_admin_user)
    restore_task(task=task, user=organization_admin_user)

    task.refresh_from_db()
    assert task.archived is False


@pytest.mark.django_db
def test_cannot_update_archived_task(project, user, member_user):
    task = create_task(
        project=project,
        user=user,
        title="Archived task",
    )

    task.archived = True
    task.save()

    with pytest.raises(ValidationError):
        update_task(
            task=task,
            user=member_user,
            title="Trying to update",
        )


@pytest.mark.django_db
def test_cannot_update_protected_fields(project, user, member_user):
    task = create_task(
        project=project,
        user=user,
        title="Original task",
    )

    with pytest.raises(ValidationError):
        update_task(
            task=task,
            user=member_user,
            archived=True,
        )

    task.refresh_from_db()
    assert task.archived is False


@pytest.mark.django_db
def test_cannot_create_task_with_invalid_priority(project, member_user):
    with pytest.raises(ValidationError):
        create_task(
            project=project,
            user=member_user,
            title="Invalid priority task",
            priority="CRITICAL",
        )


@pytest.mark.django_db
def test_cannot_create_task_with_empty_title(project, member_user):
    with pytest.raises(ValidationError):
        create_task(
            project=project,
            user=member_user,
            title="   ",
        )
