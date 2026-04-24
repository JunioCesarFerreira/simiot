#!/usr/bin/env python3
"""Run ESP-IDF QEMU with a small TCP proxy for guest MQTT traffic."""

from __future__ import annotations

import os
import select
import socket
import subprocess
import threading


LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = int(os.getenv("SIMIOT_MQTT_PROXY_PORT", "1883"))
TARGET_HOST = os.getenv("SIMIOT_MQTT_TARGET_HOST", "mosquitto")
TARGET_PORT = int(os.getenv("SIMIOT_MQTT_TARGET_PORT", "1883"))


def pipe(left: socket.socket, right: socket.socket) -> None:
    sockets = [left, right]
    try:
        while True:
            readable, _, _ = select.select(sockets, [], [])
            for source in readable:
                data = source.recv(8192)
                if not data:
                    return
                target = right if source is left else left
                target.sendall(data)
    finally:
        for sock in sockets:
            try:
                sock.close()
            except OSError:
                pass


def handle_client(client: socket.socket) -> None:
    try:
        upstream = socket.create_connection((TARGET_HOST, TARGET_PORT), timeout=10)
    except OSError as exc:
        print(f"simiot mqtt proxy: failed to connect to {TARGET_HOST}:{TARGET_PORT}: {exc}", flush=True)
        client.close()
        return
    pipe(client, upstream)


def serve_proxy() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LISTEN_HOST, LISTEN_PORT))
        server.listen()
        print(
            f"simiot mqtt proxy: listening on {LISTEN_HOST}:{LISTEN_PORT}, "
            f"forwarding to {TARGET_HOST}:{TARGET_PORT}",
            flush=True,
        )
        while True:
            client, _ = server.accept()
            threading.Thread(target=handle_client, args=(client,), daemon=True).start()


def main() -> int:
    threading.Thread(target=serve_proxy, daemon=True).start()
    return subprocess.call(["idf.py", "qemu"])


if __name__ == "__main__":
    raise SystemExit(main())
