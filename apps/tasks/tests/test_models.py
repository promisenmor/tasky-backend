import pytest

from apps.tasks.models import Task


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

        assert task.piority == Task.Piority.MEDIUM

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
