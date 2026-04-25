from __future__ import annotations

from pathlib import PurePosixPath


def validate_firmware_files(files: dict[str, str]) -> dict[str, str]:
    """Return a normalized firmware file mapping or raise ValueError."""
    if not files:
        raise ValueError("firmware must not be empty")

    normalized: dict[str, str] = {}
    for raw_path, content in files.items():
        path = _normalize_firmware_path(raw_path)
        normalized[path] = content
    return normalized


def _normalize_firmware_path(raw_path: str) -> str:
    if not raw_path or raw_path.strip() != raw_path:
        raise ValueError(f"invalid firmware path: {raw_path!r}")

    path = PurePosixPath(raw_path)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"invalid firmware path: {raw_path!r}")

    return path.as_posix()
