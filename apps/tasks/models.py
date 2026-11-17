from uuid import uuid4

from django.conf import settings
from django.db import models


class Task(models.Model):
    class Piority(models.TextChoices):
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
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="tasks"
    )
    piority = models.CharField(
        max_length=10, choices=Piority.choices, default=Piority.MEDIUM
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
    archieved = models.BooleanField(default=False)

    class Meta:
        ordering = ["due_date", "title"]

    def __str__(self):
        return self.title
