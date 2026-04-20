"""Run ESP-IDF firmware builds inside the espressif/idf container."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

import docker
from docker.errors import DockerException

ESP_IDF_IMAGE = "espressif/idf:release-v5.4"
BUILD_CMD = "idf.py set-target esp32 && idf.py build"

LogSink = Callable[[str], None]


def build_firmware(files: dict[str, str], on_log: LogSink | None = None) -> int:
    """Write `files` to a temp workdir, build with ESP-IDF, return exit_code.

    Logs are streamed chunk-by-chunk to `on_log` as they are produced.
    The workdir is removed after the build — no artifacts kept yet.
    """
    def emit(chunk: str) -> None:
        if on_log is not None:
            on_log(chunk)

    workdir = Path(tempfile.mkdtemp(prefix="simiot-build-"))
    try:
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
                volumes={str(workdir): {"bind": "/project", "mode": "rw"}},
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
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
