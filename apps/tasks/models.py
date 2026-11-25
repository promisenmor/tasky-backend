from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.organizations.models import Membership, Organization


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    class Status(models.TextChoices):
        TODO = "TODO", "To do"
        IN_PROGRESS = "IN_PROGESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    labels = models.ManyToManyField(
        "Label", through="TaskLabel", related_name="tasks", blank=True
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="tasks"
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.TODO
    )
    due_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tasks",
    )

    completed_at = models.DateTimeField(blank=True, null=True)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["due_date", "title"]

    def __str__(self):
        return self.title


class TaskAssignee(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="assignees",
    )
    organization_membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="task_assignments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "organization_membership"],
                name="unique_task_assignee",
            ),
        ]

    def clean(self):
        if (
            self.task.id
            and self.organization_membership_id
            and self.task.project.organization_id
            != self.organization_membership.organization_id
        ):
            raise ValidationError(
                {
                    "organization_membership": "The assignee must belong to the task's project organization."
                }
            )

    def __str__(self):
        return f"{self.organization_membership.user.full_name} - {self.task.title}"


class Label(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="task_labels"
    )
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_label_name_per_organization",
            ),
        ]

    def __str__(self):
        return self.name


# TaskLabel - an intermediary model connecting tasks and labels.
class TaskLabel(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_labels")
    label = models.ForeignKey(
        Label, on_delete=models.CASCADE, related_name="task_labels"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "label"],
                name="unique_label_per_task",
            ),
        ]

    # this clean method enforces organization consistency when model validation is explicity called. As with TaskAssignee.
    # this will be enforced in the service layer later.
    def clean(self):
        if (
            self.task.id
            and self.label.id
            and self.task.project.organization_id != self.label.organization_id
        ):
            raise ValidationError(
                {"label": ("The label must belong to the task's project organization")}
            )

    def __str__(self):
        return f"{self.task.title} - {self.label.name}"


class Comment(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="task_comments"
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.full_name} - {self.task.title}"


class Attachment(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="task_attachments/%Y/%m/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_attachments",
    )
    file_size = models.PositiveBigIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} - {self.task.title}"


class TimeEntry(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="time_entries"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="time_entries"
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)

    duration = models.DurationField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.user.full_name} - {self.task.title}"
