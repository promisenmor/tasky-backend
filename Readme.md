# Tasky Backend

Tasky is a modern project management platform built with Django REST Framework.

## Tech Stack

- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Channels
- Docker

## Status

🚧 Sprint 0 - Project Bootstrap


## sections:
- Are contianers that organize tasks within a project.
- for example a project called tasky-backend could have:
- Backlog
3 tasks
Pending work


In Progress
2 tasks
Active work


Done
4 tasks
Completed work

**sections** will be inside the apps/projects, since it belongs to to project
model overview:
id	UUID	Unique identifier
project	ForeignKey	Parent project
name	CharField (100)	Section name
description	TextField	Optional description
position	PositiveIntegerField	Display order
created_at	DateTimeField	Creation timestamp
updated_at
