from __future__ import annotations

from fastapi import FastAPI, Response, status

from .runtime import RuntimeReadiness

app = FastAPI(title="AUREUS-2026", version="0.1.0")
_state = RuntimeReadiness(False, False, False, False, False, False)


@app.get("/health/live")
def live() -> dict[str, bool]:
    return {"live": True}


@app.get("/health/ready")
def ready(response: Response) -> dict[str, bool]:
    if not _state.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": _state.ready}
