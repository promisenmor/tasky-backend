import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.organizations.models import Membership
from apps.projects.models import Project
from apps.tasks.models import Task, TaskAssignee
from apps.tasks.services.assignee_service import (
    assign_user_to_task,
    remove_user_from_task,
)


@pytest.fixture
def task(project, user):
    return Task.objects.create(
        project=project,
        created_by=user,
        title="Implement authentication",
    )


@pytest.mark.django_db
def test_member_can_assign_another_member(task, member_user):
    membership = Membership.objects.get(
        user=member_user,
        organization=task.project.organization,
    )

    assignment = assign_user_to_task(
        task=task,
        organization_membership=membership,
        user=member_user,
    )

    assert assignment.task == task
    assert assignment.organization_membership == membership


@pytest.mark.django_db
def test_admin_can_assign_member(task, organization_admin_user, member_user):
    membership = Membership.objects.get(
        user=member_user,
        organization=task.project.organization,
    )

    assignment = assign_user_to_task(
        task=task,
        organization_membership=membership,
        user=organization_admin_user,
    )

    assert assignment is not None


@pytest.mark.django_db
def test_non_member_cannot_assign_user(task, non_member_user, member_user):
    membership = Membership.objects.get(
        user=member_user,
        organization=task.project.organization,
    )

    with pytest.raises(PermissionDenied):
        assign_user_to_task(
            task=task,
            organization_membership=membership,
            user=non_member_user,
        )


@pytest.mark.django_db
def test_cannot_assign_member_from_another_organisation(
    task,
    member_user,
    other_organization,
):
    other_membership = Membership.objects.create(
        user=member_user,
        organization=other_organization,
        role=Membership.Role.MEMBER,
    )

    with pytest.raises(ValidationError):
        assign_user_to_task(
            task=task,
            organization_membership=other_membership,
            user=member_user,
        )


@pytest.mark.django_db
def test_cannot_assign_same_member_twice(task, member_user):
    membership = Membership.objects.get(
        user=member_user,
        organization=task.project.organization,
    )

    assign_user_to_task(
        task=task,
        organization_membership=membership,
        user=member_user,
    )

    with pytest.raises(ValidationError):
        assign_user_to_task(
            task=task,
            organization_membership=membership,
            user=member_user,
        )

    assert task.assignees.count() == 1


@pytest.mark.django_db
def test_member_can_remove_assignment(task, member_user):
    membership = Membership.objects.get(
        user=member_user,
        organization=task.project.organization,
    )

    assignment = assign_user_to_task(
        task=task,
        organization_membership=membership,
        user=member_user,
    )

    result = remove_user_from_task(
        task=task,
        organization_membership=membership,
        user=member_user,
    )

    assert result is True
    assert not TaskAssignee.objects.filter(id=assignment.id).exists()


@pytest.mark.django_db
def test_non_member_cannot_remove_assignment(
    task,
    member_user,
    non_member_user,
):
    membership = Membership.objects.get(
        user=member_user,
        organization=task.project.organization,
    )

    assign_user_to_task(
        task=task,
        organization_membership=membership,
        user=member_user,
    )

    with pytest.raises(PermissionDenied):
        remove_user_from_task(
            task=task,
            organization_membership=membership,
            user=non_member_user,
        )

    assert task.assignees.count() == 1


@pytest.mark.django_db
def test_cannot_assign_to_archived_task(task, member_user):
    membership = Membership.objects.get(
        user=member_user,
        organization=task.project.organization,
    )

    task.archived = True
    task.save()

    with pytest.raises(ValidationError):
        assign_user_to_task(
            task=task,
            organization_membership=membership,
            user=member_user,
        )


@pytest.mark.django_db
def test_cannot_assign_to_task_in_archived_project(task, member_user):
    membership = Membership.objects.get(
        user=member_user,
        organization=task.project.organization,
    )

    task.project.status = Project.Status.ARCHIVED
    task.project.save()

    with pytest.raises(ValidationError):
        assign_user_to_task(
            task=task,
            organization_membership=membership,
            user=member_user,
        )
