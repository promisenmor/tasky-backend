import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.tasks.services.comment_service import (
    create_comment,
    update_comment,
)


@pytest.fixture
def task(project, user):
    return Task.objects.create(
        project=project,
        created_by=user,
        title="Implement authentication",
    )


@pytest.mark.django_db
def test_member_can_create_comment(task, member_user):
    comment = create_comment(
        task=task,
        user=member_user,
        body="Authentication implementation is in progress.",
    )

    assert comment.task == task
    assert comment.author == member_user
    assert comment.body == "Authentication implementation is in progress."
    assert comment.edited is False


@pytest.mark.django_db
def test_non_member_cannot_create_comment(task, non_member_user):
    with pytest.raises(PermissionDenied):
        create_comment(
            task=task,
            user=non_member_user,
            body="Unauthorised comment",
        )


@pytest.mark.django_db
def test_comment_body_cannot_be_empty(task, member_user):
    with pytest.raises(ValidationError):
        create_comment(
            task=task,
            user=member_user,
            body="",
        )


@pytest.mark.django_db
def test_comment_body_cannot_be_whitespace(task, member_user):
    with pytest.raises(ValidationError):
        create_comment(
            task=task,
            user=member_user,
            body="   ",
        )


@pytest.mark.django_db
def test_comment_body_is_trimmed(task, member_user):
    comment = create_comment(
        task=task,
        user=member_user,
        body="  Hello Tasky  ",
    )

    assert comment.body == "Hello Tasky"


@pytest.mark.django_db
def test_author_can_edit_own_comment(task, member_user):
    comment = create_comment(
        task=task,
        user=member_user,
        body="Original comment",
    )

    updated_comment = update_comment(
        comment=comment,
        user=member_user,
        body="Updated comment",
    )

    assert updated_comment.body == "Updated comment"
    assert updated_comment.edited is True


@pytest.mark.django_db
def test_user_cannot_edit_another_users_comment(
    task,
    user,
    member_user,
):
    comment = create_comment(
        task=task,
        user=user,
        body="Comment written by owner",
    )

    with pytest.raises(PermissionDenied):
        update_comment(
            comment=comment,
            user=member_user,
            body="Trying to edit another user's comment",
        )

    comment.refresh_from_db()
    assert comment.body == "Comment written by owner"
    assert comment.edited is False


@pytest.mark.django_db
def test_editing_comment_does_not_change_author(
    task,
    member_user,
):
    comment = create_comment(
        task=task,
        user=member_user,
        body="Original comment",
    )

    original_author = comment.author

    update_comment(
        comment=comment,
        user=member_user,
        body="Updated comment",
    )

    comment.refresh_from_db()

    assert comment.author == original_author


@pytest.mark.django_db
def test_cannot_comment_on_archived_task(task, member_user):
    task.archived = True
    task.save()

    with pytest.raises(ValidationError):
        create_comment(
            task=task,
            user=member_user,
            body="Comment on archived task",
        )


@pytest.mark.django_db
def test_cannot_comment_on_task_in_archived_project(
    task,
    member_user,
):
    task.project.status = Project.Status.ARCHIVED
    task.project.save()

    with pytest.raises(ValidationError):
        create_comment(
            task=task,
            user=member_user,
            body="Comment on task in archived project",
        )


@pytest.mark.django_db
def test_cannot_edit_comment_with_empty_body(
    task,
    member_user,
):
    comment = create_comment(
        task=task,
        user=member_user,
        body="Original comment",
    )

    with pytest.raises(ValidationError):
        update_comment(
            comment=comment,
            user=member_user,
            body="   ",
        )

    comment.refresh_from_db()
    assert comment.body == "Original comment"
