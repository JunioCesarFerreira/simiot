from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIMIOT_")

    cors_origins: list[str] = ["http://localhost:5173"]
    docker_host: str | None = None


settings = Settings()
