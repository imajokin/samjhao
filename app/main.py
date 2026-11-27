"""Samjhao server: the API routes, and the web page served from web/.

This file must import and start with no keys set. Anything that needs a key
answers with a clean "keys_not_set" reply instead of crashing.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, load_settings

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def keys_not_set(missing: list[str]) -> JSONResponse:
    """The one reply used whenever a needed key is missing."""
    return JSONResponse(
        status_code=503,
        content={"error": "keys_not_set", "missing": missing},
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Samjhao", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    @app.get("/api/config")
    def config() -> dict:
        # Tells the page which features are on. Never contains a key.
        return settings.public()

    @app.post("/api/session/start")
    def session_start() -> JSONResponse:
        if not settings.judging:
            return keys_not_set(["OPENROUTER_API_KEY"])
        return JSONResponse(status_code=501, content={"error": "not_built_yet"})

    @app.post("/api/transcribe")
    def transcribe() -> JSONResponse:
        if not settings.speech:
            return keys_not_set(["SARVAM_API_KEY"])
        return JSONResponse(status_code=501, content={"error": "not_built_yet"})

    @app.post("/api/speak")
    def speak() -> JSONResponse:
        if not settings.speech:
            return keys_not_set(["SARVAM_API_KEY"])
        return JSONResponse(status_code=501, content={"error": "not_built_yet"})

    # The web page. Mounted last so the routes above win.
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


app = create_app()
