from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.organizations.models import Membership
from apps.tasks.models import (
    Attachment,
    Comment,
    Label,
    Task,
    TaskAssignee,
    TaskLabel,
    TimeEntry,
)


@pytest.mark.django_db
class TestTaskModel:
    def test_create_task(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Implement Authentication",
            description="Build JWT authentication",
            created_by=user,
        )

        assert task.title == "Implement Authentication"
        assert task.description == "Build JWT authentication"
        assert task.project == project
        assert task.created_by == user

    def test_task_has_uuid(self, project, user):
        task = Task.objects.create(
            project=project,
            title="TEST UUID",
            created_by=user,
        )

        assert task.id is not None

    def test_default_piority_is_meduim(self, project, user):
        task = Task.objects.create(
            project=project,
            title="TEST MODE",
            created_by=user,
        )

        assert task.priority == Task.Priority.MEDIUM

    def test_default_status_is_to_do(self, project, user):
        task = Task.objects.create(
            project=project,
            title="TEST STATUS",
            created_by=user,
        )

        assert task.status == Task.Status.TODO

    def test_task_is_not_archived_by_default(self, project, user):
        task = Task.objects.create(
            project=project,
            title="No due date",
            created_by=user,
        )

        assert task.archieved is False

    def test_task_due_date_is_optional(self, project, user):
        task = Task.objects.create(
            project=project,
            title="No due date",
            created_by=user,
        )

        assert task.due_date is None

    def test_completed_at_is_optional(self, project, user):
        task = Task.objects.create(
            project=project,
            title="No completed",
            created_by=user,
        )

        assert task.completed_at is None

    def test_task_string_representation(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build dashboard",
            created_by=user,
        )

        assert str(task) == "Build dashboard"

    def test_task_belongs_to_project(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Project relationship",
            created_by=user,
        )

        assert task in project.tasks.all()


@pytest.mark.django_db
class TestTaskAssigneeModel:
    def test_create_task_assignee(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        membership = Membership.objects.get(
            user=user,
            organization=project.organization,
        )

        assignment = TaskAssignee.objects.create(
            task=task,
            organization_membership=membership,
        )

        assert assignment.task == task
        assert assignment.organization_membership == membership

    def test_task_can_have_multiple_assignees(self, project, user, member_user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        memberships = Membership.objects.filter(
            organization=project.organization,
            user__in=[user, member_user],
        )

        for membership in memberships:
            TaskAssignee.objects.create(
                task=task,
                organization_membership=membership,
            )

        assert task.assignees.count() == 2

    def test_same_member_cannot_be_assigned_twice(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        membership = Membership.objects.get(
            user=user,
            organization=project.organization,
        )

        TaskAssignee.objects.create(
            task=task,
            organization_membership=membership,
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                TaskAssignee.objects.create(
                    task=task,
                    organization_membership=membership,
                )

    def test_assignee_must_belong_to_project_organization(
        self, project, user, other_organization
    ):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        other_membership = Membership.objects.create(
            user=user,
            organization=other_organization,
            role=Membership.Role.MEMBER,
        )

        assignment = TaskAssignee(
            task=task,
            organization_membership=other_membership,
        )

        with pytest.raises(ValidationError):
            assignment.full_clean()

    def test_assignment_string_representation(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        membership = Membership.objects.get(
            user=user,
            organization=project.organization,
        )

        assignment = TaskAssignee.objects.create(
            task=task,
            organization_membership=membership,
        )

        assert str(assignment) == f"{user.full_name} - Build API"


@pytest.mark.django_db
class TestLabelModel:
    def test_create_label(self, organization):
        label = Label.objects.create(
            organization=organization,
            name="Backend",
        )

        assert label.name == "Backend"
        assert label.organization == organization

    def test_label_string_representation(self, organization):
        label = Label.objects.create(
            organization=organization,
            name="Frontend",
        )

        assert str(label) == "Frontend"

    def test_label_name_must_be_unique_per_organization(self, organization):
        Label.objects.create(
            organization=organization,
            name="Backend",
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Label.objects.create(
                    organization=organization,
                    name="Backend",
                )

    def test_same_label_name_allowed_in_different_organizations(
        self, organization, other_organization
    ):
        first_label = Label.objects.create(
            organization=organization,
            name="Backend",
        )

        second_label = Label.objects.create(
            organization=other_organization,
            name="Backend",
        )

        assert first_label.name == second_label.name
        assert first_label.organization != second_label.organization


@pytest.mark.django_db
class TestTaskLabelModel:
    def test_create_task_label(self, project, user):
        task = Task.objects.create(project=project, title="Build API", created_by=user)

        label = Label.objects.create(
            organization=project.organization,
            name="Backend",
        )

        task_label = TaskLabel.objects.create(
            task=task,
            label=label,
        )

        assert task_label.task == task
        assert task_label.label == label

    def test_task_can_have_multiple_labels(self, project, user):
        task = Task.objects.create(project=project, title="Build API", created_by=user)

        labels = [
            Label.objects.create(
                organization=project.organization,
                name="Backend",
            ),
            Label.objects.create(
                organization=project.organization,
                name="Frontend",
            ),
        ]

        for label in labels:
            TaskLabel.objects.create(
                task=task,
                label=label,
            )

        assert task.label.count() == 2

    def test_label_can_be_reused_by_multiple_tasks(self, project, user):
        label = Label.objects.create(
            organization=project.organization,
            name="Backend",
        )

        first_task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        second_task = Task.objects.create(
            project=project,
            title="Build Authentication",
            created_by=user,
        )

        TaskLabel.objects.create(task=first_task, label=label)
        TaskLabel.objects.create(task=second_task, label=label)

        assert label.tasks.count() == 2

    def test_duplicated_task_label_is_rejected(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        label = Label.objects.create(
            organization=project.organization,
            name="Backend",
        )

        TaskLabel.objects.create(task=task, label=label)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                TaskLabel.objects.create(
                    task=task,
                    label=label,
                )

    def test_label_must_belong_to_task_organization(
        self, project, user, other_organization
    ):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        label = Label.objects.create(
            organization=other_organization,
            name="Backend",
        )

        task_label = TaskLabel(
            task=task,
            label=label,
        )

        with pytest.raises(ValidationError):
            task_label.full_clean()

    def test_task_label_string_representation(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        label = Label.objects.create(
            organization=project.organization,
            name="Backend",
        )

        task_label = TaskLabel.objects.create(task=task, label=label)

        assert str(task_label) == "Build API - Backend"


@pytest.mark.django_db
class TestCommentModel:
    def test_create_comment(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        comment = Comment.objects.create(
            task=task,
            author=user,
            body="The API implementation is underway.",
        )

        assert comment.task == task
        assert comment.author == user
        assert comment.body == "The API implementation is underway."

    def test_comment_has_uuid(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        comment = Comment.objects.create(
            task=task,
            author=user,
            body="Working on this.",
        )

        assert comment.id is not None

    def test_comment_is_not_edited_by_default(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        comment = Comment.objects.create(
            task=task,
            author=user,
            body="Initial comment.",
        )

        assert comment.edited is False

    def test_comment_records_creation_time(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        before_creation = timezone.now()

        comment = Comment.objects.create(
            task=task,
            author=user,
            body="Initial comment.",
        )

        after_creation = timezone.now()

        assert before_creation <= comment.created_at <= after_creation

    def test_task_can_have_multiple_comments(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        Comment.objects.create(
            task=task,
            author=user,
            body="First comment.",
        )

        Comment.objects.create(
            task=task,
            author=user,
            body="Second comment.",
        )

        assert task.comments.count() == 2

    def test_comment_string_representation(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        comment = Comment.objects.create(
            task=task,
            author=user,
            body="Implementation completed.",
        )

        assert str(comment) == f"{user.full_name} - Build API"

    def test_deleting_task_deletes_its_comments(self, project, user):
        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        comment = Comment.objects.create(
            task=task,
            author=user,
            body="Implementation completed.",
        )

        task.delete()

        assert not Comment.objects.filter(id=comment.id).exists()


@pytest.mark.django_db
def test_attachment_can_be_created(project, user):
    uploaded_file = SimpleUploadedFile(
        "screenshot.png", b"fake image content", content_type="image/png"
    )

    task = Task.objects.create(
        project=project,
        title="Build API",
        created_by=user,
    )

    attachment = Attachment.objects.create(
        task=task,
        uploaded_by=user,
        file=uploaded_file,
        file_size=19,
        mime_type="image/png",
    )

    assert attachment.task == task
    assert attachment.uploaded_by == user
    assert attachment.file_size == 19
    assert attachment.mime_type == "image/png"


@pytest.mark.django_db
def test_attachment_has_uuid(project, user):
    uploaded_file = SimpleUploadedFile(
        "document.pdf", b"fake pdf content", content_type="application/pdf"
    )

    task = Task.objects.create(
        project=project,
        title="Build API",
        created_by=user,
    )

    attachment = Attachment.objects.create(
        task=task,
        uploaded_by=user,
        file=uploaded_file,
        file_size=16,
        mime_type="application/pdf",
    )

    assert attachment.id is not None


@pytest.mark.django_db
def test_attachment_has_creation_timestamp(project, user):
    before = timezone.now()

    uploaded_file = SimpleUploadedFile(
        "document.pdf", b"content", content_type="application/pdf"
    )

    task = Task.objects.create(
        project=project,
        title="Build API",
        created_by=user,
    )

    attachment = Attachment.objects.create(
        task=task,
        uploaded_by=user,
        file=uploaded_file,
        file_size=7,
        mime_type="application/pdf",
    )

    after = timezone.now()

    assert before <= attachment.uploaded_at <= after


@pytest.mark.django_db
def test_task_can_have_multiple_attachments(project, user):
    for filename in ["first.pdf", "second.png"]:
        uploaded_file = SimpleUploadedFile(
            filename, b"file content", content_type="application/octet-stream"
        )

        task = Task.objects.create(
            project=project,
            title="Build API",
            created_by=user,
        )

        Attachment.objects.create(
            task=task,
            uploaded_by=user,
            file=uploaded_file,
            file_size=12,
            mime_type="application/octet-stream",
        )

    assert task.attachments.count() == 1


@pytest.mark.django_db
def test_attachment_string_representation(project, user):
    uploaded_file = SimpleUploadedFile(
        "report.pdf", b"report content", content_type="application/pdf"
    )

    task = Task.objects.create(
        project=project,
        title="Build API",
        created_by=user,
    )

    attachment = Attachment.objects.create(
        task=task,
        uploaded_by=user,
        file=uploaded_file,
        file_size=14,
        mime_type="application/pdf",
    )

    assert str(attachment) == f"{attachment.file.name} - {task.title}"


@pytest.mark.django_db
def test_deleting_task_deletes_attachments(project, user):
    uploaded_file = SimpleUploadedFile(
        "report.pdf", b"report content", content_type="application/pdf"
    )

    task = Task.objects.create(
        project=project,
        title="Build API",
        created_by=user,
    )

    attachment = Attachment.objects.create(
        task=task,
        uploaded_by=user,
        file=uploaded_file,
        file_size=14,
        mime_type="application/pdf",
    )

    task.delete()

    assert not Attachment.objects.filter(id=attachment.id).exists()


@pytest.mark.django_db
def test_time_entry_can_be_created(task, user):
    start = timezone.now()

    entry = TimeEntry.objects.create(task=task, user=user, start_time=start)

    assert entry.task == task
    assert entry.user == user
    assert entry.start_time == start


@pytest.mark.django_db
def test_time_entry_has_uuid(task, user):
    entry = TimeEntry.objects.create(task=task, user=user, start_time=timezone.now())

    assert entry.id is not None


@pytest.mark.django_db
def test_running_timer_has_no_end_time_or_duration(task, user):
    entry = TimeEntry.objects.create(task=task, user=user, start_time=timezone.now())

    assert entry.end_time is None
    assert entry.duration is None


@pytest.mark.django_db
def test_completed_time_entry_can_store_end_time_and_duration(task, user):
    start = timezone.now()
    end = start + timedelta(hours=2)

    entry = TimeEntry.objects.create(
        task=task,
        user=user,
        start_time=start,
        end_time=end,
        duration=timedelta(hours=2),
    )

    assert entry.end_time == end
    assert entry.duration == timedelta(hours=2)


@pytest.mark.django_db
def test_time_entry_has_creation_timestamp(task, user):
    before = timezone.now()

    entry = TimeEntry.objects.create(task=task, user=user, start_time=timezone.now())

    after = timezone.now()

    assert before <= entry.created_at <= after


@pytest.mark.django_db
def test_task_can_have_multiple_time_entries(task, user):
    for _ in range(2):
        TimeEntry.objects.create(task=task, user=user, start_time=timezone.now())

    assert task.time_entries.count() == 2


@pytest.mark.django_db
def test_time_entry_string_representation(task, user):
    entry = TimeEntry.objects.create(task=task, user=user, start_time=timezone.now())

    assert str(entry) == f"{user.full_name} - {task.title}"


@pytest.mark.django_db
def test_deleting_task_deletes_time_entries(task, user):
    entry = TimeEntry.objects.create(task=task, user=user, start_time=timezone.now())

    entry_id = entry.id
    task.delete()

    assert not TimeEntry.objects.filter(id=entry_id).exists()
