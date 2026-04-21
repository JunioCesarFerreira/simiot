from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import firmware, projects, run
from app.core.config import settings

app = FastAPI(title="SimIoT", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(firmware.router, prefix="/api/projects", tags=["firmware"])
app.include_router(run.router, prefix="/api/projects", tags=["run"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
