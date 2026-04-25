from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


_projects: dict[UUID, Project] = {}


@router.get("")
def list_projects() -> list[Project]:
    return list(_projects.values())


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreate) -> Project:
    project = Project(name=body.name, description=body.description)
    _projects[project.id] = project
    return project


@router.get("/{project_id}")
def get_project(project_id: UUID) -> Project:
    if project_id not in _projects:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    return _projects[project_id]


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID) -> None:
    if project_id not in _projects:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    _cleanup_project(project_id)
    del _projects[project_id]


def _cleanup_project(project_id: UUID) -> None:
    from app.api.firmware import cleanup_project_firmware_state
    from app.api.run import cleanup_project_run_state

    cleanup_project_run_state(project_id)
    cleanup_project_firmware_state(project_id)
