import pytest

from apps.projects.serializers import (
    ProjectCreateSerializer,
    ProjectSerializer,
    SectionSerializer,
)


@pytest.mark.django_db
def test_project_create_serializer_accepts_valid_data(organization):
    serializer = ProjectCreateSerializer(
        data={
            "name": "Website Redesign",
            "description": "Redesign the company website.",
        },
        context={"organization": organization},
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["name"] == "Website Redesign"


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["", " ", "   "])
def test_project_create_serializer_rejects_blank_name(
    organization,
    name,
):
    serializer = ProjectCreateSerializer(
        data={"name": name, "description": ""},
        context={"organization": organization},
    )

    assert not serializer.is_valid()
    assert "name" in serializer.errors


@pytest.mark.django_db
def test_project_create_serializer_strips_name_and_description(
    organization,
):
    serializer = ProjectCreateSerializer(
        data={
            "name": "  Website Redesign  ",
            "description": "  Redesign the website.  ",
        },
        context={"organization": organization},
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["name"] == "Website Redesign"
    assert serializer.validated_data["description"] == "Redesign the website."


@pytest.mark.django_db
def test_project_create_serializer_rejects_duplicate_name(
    organization,
    project,
):
    serializer = ProjectCreateSerializer(
        data={"name": project.name, "description": ""},
        context={"organization": organization},
    )

    assert not serializer.is_valid()
    assert "name" in serializer.errors


@pytest.mark.django_db
def test_project_create_serializer_does_not_accept_read_only_fields(
    organization,
):
    serializer = ProjectCreateSerializer(
        data={
            "name": "New Project",
            "description": "",
            "status": "ARCHIVED",
            "organization": str(organization.id),
        },
        context={"organization": organization},
    )

    assert serializer.is_valid(), serializer.errors
    assert "status" not in serializer.validated_data
    assert "organization" not in serializer.validated_data


@pytest.mark.django_db
def test_project_serializer_exposes_read_only_fields(project):
    serializer = ProjectSerializer(
        project,
        context={"organization": project.organization},
    )

    data = serializer.data

    assert data["id"] == str(project.id)
    assert data["name"] == project.name
    assert data["status"] == project.status
    assert data["organization"] == project.organization.id
    assert data["created_by"] == project.created_by.id
    assert data["organization_name"] == project.organization.name
    assert data["created_by_email"] == project.created_by.email


@pytest.mark.django_db
def test_project_serializer_rejects_blank_updated_name(
    organization,
    project,
):
    serializer = ProjectSerializer(
        project,
        data={"name": "   "},
        partial=True,
        context={"organization": organization},
    )

    assert not serializer.is_valid()
    assert "name" in serializer.errors


@pytest.mark.django_db
def test_project_serializer_allows_unchanged_name(
    organization,
    project,
):
    serializer = ProjectSerializer(
        project,
        data={"name": project.name},
        partial=True,
        context={"organization": organization},
    )

    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_project_serializer_returns_expected_fields(project):
    serializer = ProjectSerializer(instance=project)

    expected_fields = {
        "id",
        "organization",
        "organization_name",
        "name",
        "description",
        "status",
        "created_by",
        "created_by_email",
        "created_at",
        "updated_at",
    }

    assert set(serializer.data.keys()) == expected_fields


@pytest.mark.django_db
def test_project_serializer_validates_name():
    serializer = ProjectSerializer(data={"name": "  My Project  "})

    assert serializer.is_valid()
    assert serializer.validated_data["name"] == "My Project"


@pytest.mark.django_db
def test_project_serializer_rejects_empty_name():
    serializer = ProjectSerializer(data={"name": "   "})

    assert not serializer.is_valid()
    assert "name" in serializer.errors


@pytest.mark.django_db
def test_project_serializer_strips_description():
    serializer = ProjectSerializer(
        data={
            "name": "My Project",
            "description": "  Project description  ",
        }
    )

    assert serializer.is_valid()
    assert serializer.validated_data["description"] == "Project description"


# Section tests


@pytest.mark.django_db
def test_section_serializer_returns_expected_fields(section):
    serializer = SectionSerializer(instance=section)

    expected_fields = {
        "id",
        "project",
        "name",
        "description",
        "position",
        "created_at",
        "updated_at",
    }

    assert set(serializer.data.keys()) == expected_fields


@pytest.mark.django_db
def test_section_serializer_validates_name():
    serializer = SectionSerializer(data={"name": "  Backlog  "})

    assert serializer.is_valid()
    assert serializer.validated_data["name"] == "Backlog"


@pytest.mark.django_db
def test_section_serializer_rejects_empty_name():
    serializer = SectionSerializer(data={"name": "   "})

    assert not serializer.is_valid()
    assert "name" in serializer.errors


@pytest.mark.django_db
def test_section_serializer_strips_description():
    serializer = SectionSerializer(
        data={
            "name": "Backlog",
            "description": "  Tasks waiting to start.  ",
        }
    )

    assert serializer.is_valid()
    assert serializer.validated_data["description"] == "Tasks waiting to start."
