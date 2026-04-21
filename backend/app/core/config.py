from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIMIOT_")

    cors_origins: list[str] = ["http://localhost:5173"]
    docker_host: str | None = None
    work_dir: Path = Path(".simiot-work")
    qemu_image: str = "simiot/esp32-qemu:latest"
    docker_network: str = "simiot-net"


settings = Settings()
settings.work_dir.mkdir(parents=True, exist_ok=True)
