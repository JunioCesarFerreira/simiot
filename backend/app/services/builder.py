"""Run ESP-IDF firmware builds inside the espressif/idf container."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import docker
from docker.errors import DockerException

ESP_IDF_IMAGE = "espressif/idf:release-v5.4"
BUILD_CMD = "idf.py set-target esp32 && idf.py build"

LogSink = Callable[[str], None]


def build_firmware(
    files: dict[str, str],
    workdir: Path,
    on_log: LogSink | None = None,
) -> int:
    """Write `files` to `workdir`, build with ESP-IDF, return exit_code.

    Logs are streamed chunk-by-chunk to `on_log`. The workdir is kept on disk
    so the runner can mount the build artifacts into the QEMU container.
    """
    def emit(chunk: str) -> None:
        if on_log is not None:
            on_log(chunk)

    workdir.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        target = workdir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    try:
        client = docker.from_env()
    except DockerException as exc:
        emit(f"docker engine unreachable: {exc}\n")
        return 1

    try:
        container = client.containers.run(
            ESP_IDF_IMAGE,
            command=["sh", "-c", BUILD_CMD],
            volumes={str(workdir.resolve()): {"bind": "/project", "mode": "rw"}},
            working_dir="/project",
            detach=True,
        )
    except DockerException as exc:
        emit(f"failed to start build container: {exc}\n")
        return 1

    try:
        for chunk in container.logs(stream=True, follow=True):
            emit(chunk.decode("utf-8", errors="replace"))
        result = container.wait()
    finally:
        try:
            container.remove(force=True)
        except DockerException:
            pass

    return int(result.get("StatusCode", 1))
