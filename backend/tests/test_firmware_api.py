from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.firmware import FirmwareFiles, get_firmware, put_firmware
from app.api.projects import ProjectCreate, create_project


def test_rejects_firmware_paths_that_escape_project():
    project = create_project(ProjectCreate(name="lab"))

    with pytest.raises(HTTPException) as exc:
        put_firmware(
            project.id,
            FirmwareFiles(files={"../main.c": "int main(void) { return 0; }"}),
        )

    assert exc.value.status_code == 400
    assert "invalid firmware path" in exc.value.detail


def test_accepts_and_returns_valid_firmware_files():
    project = create_project(ProjectCreate(name="lab"))
    files = {
        "CMakeLists.txt": "project(simiot)",
        "main/main.c": "void app_main(void) {}",
    }

    response = put_firmware(project.id, FirmwareFiles(files=files))

    assert response.files == files
    assert get_firmware(project.id).files == files
