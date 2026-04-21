from __future__ import annotations

import threading
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from docker.models.containers import Container
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.firmware import BuildStatus, _builds, _project_builds, build_workdir
from app.api.projects import _projects
from app.core.config import settings
from app.services.runner import start_node, stop_node, stream_logs

router = APIRouter()


class RunStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class Run(BaseModel):
    project_id: UUID
    status: RunStatus
    build_id: UUID | None = None
    logs: str = ""
    container_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stop_requested: bool = False


_runs: dict[UUID, Run] = {}
_containers: dict[UUID, Container] = {}


def _ensure_project(project_id: UUID) -> None:
    if project_id not in _projects:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")


def _latest_succeeded_build(project_id: UUID) -> UUID | None:
    for bid in reversed(_project_builds.get(project_id, [])):
        if _builds[bid].status == BuildStatus.SUCCEEDED:
            return bid
    return None


def _append_log(project_id: UUID, chunk: str) -> None:
    run = _runs.get(project_id)
    if run is not None:
        run.logs += chunk


def _follow(project_id: UUID, container: Container) -> None:
    exit_code = stream_logs(container, on_log=lambda c: _append_log(project_id, c))
    run = _runs.get(project_id)
    if run is None or run.container_id != container.id:
        return
    if run.stop_requested or exit_code == 0:
        run.status = RunStatus.STOPPED
    else:
        run.status = RunStatus.FAILED
    run.finished_at = datetime.now(timezone.utc)
    _containers.pop(project_id, None)


@router.get("/{project_id}/run", response_model=Run)
def get_run(project_id: UUID) -> Run:
    _ensure_project(project_id)
    if project_id not in _runs:
        return Run(project_id=project_id, status=RunStatus.IDLE)
    return _runs[project_id]


@router.post(
    "/{project_id}/run",
    response_model=Run,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_run(project_id: UUID) -> Run:
    _ensure_project(project_id)
    current = _runs.get(project_id)
    if current and current.status in (RunStatus.RUNNING, RunStatus.STOPPING):
        raise HTTPException(status.HTTP_409_CONFLICT, "already running")

    build_id = _latest_succeeded_build(project_id)
    if build_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "no succeeded build for this project — build the firmware first",
        )
    workdir = build_workdir(build_id)
    if not workdir.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "build workdir missing on disk",
        )

    run = Run(
        project_id=project_id,
        status=RunStatus.RUNNING,
        build_id=build_id,
        started_at=datetime.now(timezone.utc),
    )
    _runs[project_id] = run

    try:
        container = start_node(
            image=settings.qemu_image,
            workdir=workdir,
            network=settings.docker_network,
            name=f"simiot-node-{project_id}",
        )
    except Exception as exc:
        run.status = RunStatus.FAILED
        run.logs = f"failed to start container: {exc}\n"
        run.finished_at = datetime.now(timezone.utc)
        return run

    _containers[project_id] = container
    run.container_id = container.id
    threading.Thread(target=_follow, args=(project_id, container), daemon=True).start()
    return run


@router.post("/{project_id}/stop", response_model=Run)
def stop_run(project_id: UUID) -> Run:
    _ensure_project(project_id)
    run = _runs.get(project_id)
    container = _containers.get(project_id)
    if run is None or container is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no active run")
    run.stop_requested = True
    run.status = RunStatus.STOPPING
    stop_node(container)
    return run
