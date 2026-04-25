from __future__ import annotations

import pytest

from app.api import firmware, projects, run


@pytest.fixture(autouse=True)
def reset_state(tmp_path, monkeypatch):
    projects._projects.clear()
    firmware._firmware.clear()
    firmware._builds.clear()
    firmware._project_builds.clear()
    run._runs.clear()
    run._containers.clear()
    monkeypatch.setattr(firmware.settings, "work_dir", tmp_path / ".simiot-work")
    yield
    projects._projects.clear()
    firmware._firmware.clear()
    firmware._builds.clear()
    firmware._project_builds.clear()
    run._runs.clear()
    run._containers.clear()
