import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.tasks.models import Attachment
from apps.tasks.services.attachment_service import (
    create_attachment,
    delete_attachment,
)


@pytest.mark.django_db
def test_create_attachment_success(project, user, uploaded_file, task):
    task = project.tasks.first()

    attachment = create_attachment(
        task=task,
        user=user,
        file=uploaded_file,
    )

    assert isinstance(attachment, Attachment)
    assert attachment.task == task
    assert attachment.uploaded_by == user
    assert attachment.file_size == len(b"Tasky attachment test content")
    assert attachment.mime_type == "application/pdf"
    assert attachment.file
    assert Attachment.objects.filter(id=attachment.id).exists()


@pytest.mark.django_db
def test_create_attachment_rejects_non_member(
    project, non_member_user, uploaded_file, task
):
    with pytest.raises(PermissionDenied):
        create_attachment(
            task=task,
            user=non_member_user,
            file=uploaded_file,
        )


@pytest.mark.django_db
def test_create_attachment_rejects_unauthenticated_user(project, uploaded_file, task):
    with pytest.raises(PermissionDenied):
        create_attachment(
            task=task,
            user=None,
            file=uploaded_file,
        )


@pytest.mark.django_db
def test_create_attachment_rejects_archived_task(project, user, uploaded_file, task):
    task.archived = True
    task.save(update_fields=["archived"])

    with pytest.raises(ValidationError):
        create_attachment(
            task=task,
            user=user,
            file=uploaded_file,
        )


@pytest.mark.django_db
def test_create_attachment_rejects_archived_project(project, user, uploaded_file, task):
    project.status = project.Status.ARCHIVED
    project.save(update_fields=["status"])

    with pytest.raises(ValidationError):
        create_attachment(
            task=task,
            user=user,
            file=uploaded_file,
        )


@pytest.mark.django_db
def test_delete_attachment_success(project, user, uploaded_file, task):
    attachment = create_attachment(
        task=task,
        user=user,
        file=uploaded_file,
    )

    file_name = attachment.file.name

    delete_attachment(
        attachment=attachment,
        user=user,
    )

    assert not Attachment.objects.filter(id=attachment.id).exists()
    assert not attachment.file.storage.exists(file_name)


@pytest.mark.django_db
def test_delete_attachment_rejects_non_uploader(
    project, member_user, user, uploaded_file, task
):
    attachment = create_attachment(
        task=task,
        user=user,
        file=uploaded_file,
    )

    with pytest.raises(PermissionDenied):
        delete_attachment(
            attachment=attachment,
            user=member_user,
        )

    assert Attachment.objects.filter(id=attachment.id).exists()


@pytest.mark.django_db
def test_delete_attachment_rejects_unauthenticated_user(
    project, user, uploaded_file, task
):
    attachment = create_attachment(
        task=task,
        user=user,
        file=uploaded_file,
    )

    with pytest.raises(PermissionDenied):
        delete_attachment(
            attachment=attachment,
            user=None,
        )

    assert Attachment.objects.filter(id=attachment.id).exists()
