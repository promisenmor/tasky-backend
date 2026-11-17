import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.organizations.models import Membership
from apps.tasks.models import Comment, Label, Task, TaskAssignee, TaskLabel


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
