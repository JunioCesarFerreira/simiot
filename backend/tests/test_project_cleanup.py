from __future__ import annotations

from uuid import UUID, uuid4

from app.api.firmware import Build, BuildStatus, _builds, _firmware, _project_builds, build_workdir
from app.api.projects import ProjectCreate, create_project, delete_project


def test_delete_project_cleans_firmware_build_state_and_artifacts():
    project = create_project(ProjectCreate(name="lab"))
    project_id = UUID(str(project.id))
    build_id = uuid4()
    workdir = build_workdir(build_id)
    workdir.mkdir(parents=True)
    (workdir / "artifact.bin").write_text("binary", encoding="utf-8")

    _firmware[project_id] = {"main/main.c": "void app_main(void) {}"}
    _builds[build_id] = Build(id=build_id, project_id=project_id, status=BuildStatus.SUCCEEDED)
    _project_builds[project_id] = [build_id]

    delete_project(project_id)

    assert project_id not in _firmware
    assert project_id not in _project_builds
    assert build_id not in _builds
    assert not workdir.exists()
