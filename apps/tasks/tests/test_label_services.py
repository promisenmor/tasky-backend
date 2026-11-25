import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.projects.models import Project
from apps.tasks.models import Label, Task
from apps.tasks.services.label_service import (
    attach_label_to_task,
    create_label,
    remove_label_from_task,
)


@pytest.fixture
def task(project, user):
    return Task.objects.create(
        project=project,
        created_by=user,
        title="Implement authentication",
    )


@pytest.fixture
def label(organization, user):
    return create_label(
        organization=organization,
        user=user,
        name="Backend",
    )


@pytest.mark.django_db
def test_member_can_create_label(organization, member_user):
    label = create_label(
        organization=organization,
        user=member_user,
        name="Frontend",
    )

    assert label.name == "Frontend"
    assert label.organization == organization


@pytest.mark.django_db
def test_non_member_cannot_create_label(organization, non_member_user):
    with pytest.raises(PermissionDenied):
        create_label(
            organization=organization,
            user=non_member_user,
            name="Backend",
        )


@pytest.mark.django_db
def test_label_name_cannot_be_empty(organization, member_user):
    with pytest.raises(ValidationError):
        create_label(
            organization=organization,
            user=member_user,
            name="   ",
        )


@pytest.mark.django_db
def test_duplicate_label_name_is_rejected(organization, user):
    create_label(
        organization=organization,
        user=user,
        name="Backend",
    )

    with pytest.raises(ValidationError):
        create_label(
            organization=organization,
            user=user,
            name="Backend",
        )

    assert (
        Label.objects.filter(
            organization=organization,
            name="Backend",
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_label_name_is_trimmed(organization, user):
    label = create_label(
        organization=organization,
        user=user,
        name="  Backend  ",
    )

    assert label.name == "Backend"


@pytest.mark.django_db
def test_member_can_attach_label_to_task(task, label, member_user):
    task_label = attach_label_to_task(
        task=task,
        label=label,
        user=member_user,
    )

    assert task_label.task == task
    assert task_label.label == label
    assert task.labels.filter(id=label.id).exists()


@pytest.mark.django_db
def test_non_member_cannot_attach_label(task, label, non_member_user):
    with pytest.raises(PermissionDenied):
        attach_label_to_task(
            task=task,
            label=label,
            user=non_member_user,
        )


@pytest.mark.django_db
def test_cannot_attach_label_from_another_organisation(
    task,
    other_organization,
    member_user,
):
    other_label = Label.objects.create(
        organization=other_organization,
        name="Research",
    )

    with pytest.raises(ValidationError):
        attach_label_to_task(
            task=task,
            label=other_label,
            user=member_user,
        )


@pytest.mark.django_db
def test_cannot_attach_same_label_twice(task, label, member_user):
    attach_label_to_task(
        task=task,
        label=label,
        user=member_user,
    )

    with pytest.raises(ValidationError):
        attach_label_to_task(
            task=task,
            label=label,
            user=member_user,
        )

    assert task.labels.count() == 1


@pytest.mark.django_db
def test_member_can_remove_label_from_task(task, label, member_user):
    attach_label_to_task(
        task=task,
        label=label,
        user=member_user,
    )

    result = remove_label_from_task(
        task=task,
        label=label,
        user=member_user,
    )

    assert result is True
    assert task.labels.count() == 0


@pytest.mark.django_db
def test_removing_label_does_not_delete_label(task, label, member_user):
    attach_label_to_task(
        task=task,
        label=label,
        user=member_user,
    )

    remove_label_from_task(
        task=task,
        label=label,
        user=member_user,
    )

    assert Label.objects.filter(id=label.id).exists()


@pytest.mark.django_db
def test_cannot_attach_label_to_archived_task(task, label, member_user):
    task.archived = True
    task.save()

    with pytest.raises(ValidationError):
        attach_label_to_task(
            task=task,
            label=label,
            user=member_user,
        )


@pytest.mark.django_db
def test_cannot_attach_label_to_task_in_archived_project(
    task,
    label,
    member_user,
):
    task.project.status = Project.Status.ARCHIVED
    task.project.save()

    with pytest.raises(ValidationError):
        attach_label_to_task(
            task=task,
            label=label,
            user=member_user,
        )
