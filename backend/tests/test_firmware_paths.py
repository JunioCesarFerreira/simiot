from __future__ import annotations

import pytest

from app.services.firmware_paths import validate_firmware_files


@pytest.mark.parametrize("path", ["", " main.c", "/main.c", "../main.c", "main/../main.c"])
def test_validate_firmware_files_rejects_unsafe_paths(path):
    with pytest.raises(ValueError):
        validate_firmware_files({path: "content"})


def test_validate_firmware_files_rejects_empty_mapping():
    with pytest.raises(ValueError, match="firmware must not be empty"):
        validate_firmware_files({})
