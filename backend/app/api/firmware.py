from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel

from app.api.projects import _projects
from app.services.builder import build_firmware
from app.services.templates import DEFAULT_FIRMWARE_FILES

router = APIRouter()


class BuildStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Build(BaseModel):
    id: UUID
    project_id: UUID
    status: BuildStatus
    logs: str = ""
    exit_code: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class FirmwareFiles(BaseModel):
    files: dict[str, str]


_firmware: dict[UUID, dict[str, str]] = {}
_builds: dict[UUID, Build] = {}
_project_builds: dict[UUID, list[UUID]] = {}


def _ensure_project(project_id: UUID) -> None:
    if project_id not in _projects:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")


def _firmware_for(project_id: UUID) -> dict[str, str]:
    if project_id not in _firmware:
        _firmware[project_id] = dict(DEFAULT_FIRMWARE_FILES)
    return _firmware[project_id]


@router.get("/{project_id}/firmware", response_model=FirmwareFiles)
def get_firmware(project_id: UUID) -> FirmwareFiles:
    _ensure_project(project_id)
    return FirmwareFiles(files=_firmware_for(project_id))


@router.put("/{project_id}/firmware", response_model=FirmwareFiles)
def put_firmware(project_id: UUID, body: FirmwareFiles) -> FirmwareFiles:
    _ensure_project(project_id)
    if not body.files:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "firmware must not be empty")
    _firmware[project_id] = dict(body.files)
    return body


def _run_build(build_id: UUID, files: dict[str, str]) -> None:
    build = _builds[build_id]
    build.status = BuildStatus.RUNNING
    build.started_at = datetime.now(timezone.utc)

    def append_log(chunk: str) -> None:
        build.logs += chunk

    try:
        exit_code = build_firmware(files, on_log=append_log)
    except Exception as exc:
        build.logs += f"\ninternal error: {exc}\n"
        build.exit_code = 1
        build.status = BuildStatus.FAILED
        build.finished_at = datetime.now(timezone.utc)
        return
    build.exit_code = exit_code
    build.status = BuildStatus.SUCCEEDED if exit_code == 0 else BuildStatus.FAILED
    build.finished_at = datetime.now(timezone.utc)


@router.post(
    "/{project_id}/builds",
    response_model=Build,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_build(project_id: UUID, tasks: BackgroundTasks) -> Build:
    _ensure_project(project_id)
    files = dict(_firmware_for(project_id))
    build = Build(id=uuid4(), project_id=project_id, status=BuildStatus.PENDING)
    _builds[build.id] = build
    _project_builds.setdefault(project_id, []).append(build.id)
    tasks.add_task(_run_build, build.id, files)
    return build


@router.get("/{project_id}/builds", response_model=list[Build])
def list_builds(project_id: UUID) -> list[Build]:
    _ensure_project(project_id)
    ids = _project_builds.get(project_id, [])
    return [_builds[bid] for bid in ids]


@router.get("/{project_id}/builds/{build_id}", response_model=Build)
def get_build(project_id: UUID, build_id: UUID) -> Build:
    _ensure_project(project_id)
    if build_id not in _builds or _builds[build_id].project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "build not found")
    return _builds[build_id]
