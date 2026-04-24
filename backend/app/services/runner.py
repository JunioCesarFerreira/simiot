"""Manage a long-lived QEMU-ESP32 container per project."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

LogSink = Callable[[str], None]


def start_node(image: str, workdir: Path, network: str, name: str) -> Container:
    client = docker.from_env()
    _ensure_network(client, network)
    with suppress(NotFound):
        client.containers.get(name).remove(force=True)
    return client.containers.run(
        image,
        command=["simiot-qemu-runner"],
        volumes={str(workdir.resolve()): {"bind": "/project", "mode": "rw"}},
        working_dir="/project",
        network=network,
        name=name,
        detach=True,
        stdout=True,
        stderr=True,
        tty=False,
    )


def stream_logs(container: Container, on_log: LogSink) -> int:
    try:
        for chunk in container.logs(stream=True, follow=True):
            on_log(chunk.decode("utf-8", errors="replace"))
    except DockerException as exc:
        on_log(f"\nlog stream error: {exc}\n")
    result = container.wait()
    return int(result.get("StatusCode", 1))


def stop_node(container: Container) -> None:
    with suppress(DockerException):
        container.stop(timeout=5)
    with suppress(DockerException):
        container.remove(force=True)


def _ensure_network(client: docker.DockerClient, network: str) -> None:
    try:
        client.networks.get(network)
    except NotFound:
        client.networks.create(network, driver="bridge")
