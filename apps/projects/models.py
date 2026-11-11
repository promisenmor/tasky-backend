from uuid import uuid4

from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        choices=Status.choices, default=Status.ACTIVE, max_length=20
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_project_name_per_organization",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class Section(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, editable=-False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="sections"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.TimeField(auto_now_add=True)
    updated_at = models.TimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                name="unique_section_per_project",
            ),
        ]
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.project.name} - {self.name}"
