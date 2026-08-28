from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .cases import all_cases
from .scanner import scan
from .storage import RunStore
from .targets import OpenAICompatibleTarget, SafeMockTarget, Target
from .tools import ADAPTERS

PACKAGE_DIR = Path(__file__).parent
STATIC_DIR = PACKAGE_DIR / "static"
DB_PATH = Path(os.getenv("REDSENTINEL_DB", "redsentinel.db"))


class ScanRequest(BaseModel):
    provider: str = "mock"
    mock_mode: str = "secure"
    case_ids: list[str] | None = None
    authorized: bool = False


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="RedSentinel", version="0.1.0", description="Authorized, synthetic LLM security evaluation")
    store = RunStore(db_path or DB_PATH)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "offline_default": True}

    @app.get("/api/cases")
    def cases() -> list[dict[str, Any]]:
        return [case.to_dict() for case in all_cases()]

    @app.get("/api/tools")
    def tools() -> list[dict[str, Any]]:
        return [adapter.status() for adapter in ADAPTERS]

    @app.get("/api/runs")
    def runs() -> list[dict[str, Any]]:
        return store.list()

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str) -> dict[str, Any]:
        run = store.get(run_id)
        if not run:
            raise HTTPException(404, "run not found")
        return run

    @app.post("/api/scans", status_code=201)
    def create_scan(request: ScanRequest) -> dict[str, Any]:
        if not request.authorized:
            raise HTTPException(403, "explicit authorization acknowledgment is required")
        if request.provider == "mock":
            target: Target = SafeMockTarget(request.mock_mode)
        elif request.provider == "openai-compatible":
            target = OpenAICompatibleTarget()
        else:
            raise HTTPException(400, "unknown provider")
        run = scan(target, request.case_ids)
        store.save(run)
        return run

    return app


app = create_app()
