"""Samjhao server: the API routes, and the web page served from web/.

This file must import and start with no keys set. Anything that needs a key
answers with a clean "keys_not_set" reply instead of crashing. No route ever
returns a key, and learners' words are never logged.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import Settings, load_settings
from app.providers import stt_sarvam, tts_sarvam
from app.providers.errors import ServiceDown
from app.providers.llm_openrouter import OpenRouter
from app.ratelimit import RateLimiter
from app.sessions import SessionStore
from app.tutor.engine import Tutor
from app.tutor.judge import LLMJudge
from app.tutor.strings import say

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class StartBody(BaseModel):
    topic_text: str = Field(default="", max_length=500)
    level: str = Field(default="", max_length=80)
    voice: str = Field(default="male", max_length=10)
    language_code: str = Field(default="", max_length=10)


class TurnBody(BaseModel):
    transcript: str = Field(default="", max_length=4000)
    heard_ok: bool = True
    silent: bool = False
    redo: bool = False  # "Heard it wrong? Say it again": replaces the last answer


class SpeakBody(BaseModel):
    text: str = Field(default="", max_length=2500)
    lang: str = Field(default="hindi", max_length=12)
    voice: str = Field(default="male", max_length=10)


MAX_AUDIO_BYTES = 4 * 1024 * 1024  # one piece of up to 30 seconds is far smaller


def error(status: int, code: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, **extra})


def keys_not_set(missing: list[str]) -> JSONResponse:
    """The one reply used whenever a needed key is missing."""
    return error(503, "keys_not_set", missing=missing)


def create_app(settings: Settings | None = None, judge=None) -> FastAPI:
    """Builds the app. Tests may pass their own settings and a fake judge."""
    settings = settings or load_settings()
    app = FastAPI(title="Samjhao", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings

    sessions = SessionStore(settings.session_ttl_minutes)
    limiter = RateLimiter(settings.rate_limit_per_minute, settings.daily_request_cap)
    tutor = Tutor(judge or LLMJudge(OpenRouter(settings)))

    def blocked(request: Request) -> JSONResponse | None:
        """A reply if this visitor must wait, or None to go ahead."""
        visitor = request.client.host if request.client else "unknown"
        reason = limiter.check(visitor)
        if reason == "daily_cap":
            return error(429, "daily_cap", text=say("daily_cap", "english"),
                         text_hi=say("daily_cap", "hindi"), video_url=settings.video_url)
        if reason == "rate_limited":
            return error(429, "rate_limited")
        return None

    def service_down(problem: ServiceDown, lang: str, voice: str = "male") -> JSONResponse:
        # Plain words for the learner. The technical detail stays on the server.
        return error(503, "service_down", service=problem.service,
                     text=say("service_down", lang, voice))

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    @app.get("/api/config")
    def config() -> dict:
        # Tells the page which features are on. Never contains a key.
        return settings.public()

    @app.post("/api/session/start")
    def session_start(body: StartBody, request: Request):
        if not settings.judging:
            return keys_not_set(["OPENROUTER_API_KEY"])
        if (stop := blocked(request)) is not None:
            return stop
        session = sessions.create(body.voice)
        try:
            reply = tutor.start(session, body.topic_text, body.level, body.language_code)
        except ServiceDown as problem:
            return service_down(problem, session.lang, session.voice)
        return {"session_id": session.id, "points_total": len(session.points), **reply}

    @app.post("/api/session/{session_id}/turn")
    def session_turn(session_id: str, body: TurnBody, request: Request):
        if not settings.judging:
            return keys_not_set(["OPENROUTER_API_KEY"])
        if (stop := blocked(request)) is not None:
            return stop
        session = sessions.get(session_id)
        if session is None:
            return error(404, "session_not_found")
        if body.redo:
            # Go back to how things stood before the misheard answer.
            sessions.rewind(session)
        sessions.remember(session)
        try:
            return tutor.turn(session, body.transcript, body.heard_ok, body.silent)
        except ServiceDown as problem:
            # The learner's words were not judged, so they can simply try again.
            if session.history and session.history[-1][0] == "learner":
                session.history.pop()
            return service_down(problem, session.lang, session.voice)

    @app.get("/api/session/{session_id}/summary")
    def session_summary(session_id: str):
        session = sessions.get(session_id)
        if session is None:
            return error(404, "session_not_found")
        if session.phase != "summary":
            # Key points stay hidden until the session is finished.
            return error(409, "session_not_finished")
        return session.summary()

    @app.post("/api/transcribe")
    async def transcribe(request: Request):
        """One piece of recorded audio in, its transcript out. Nothing is kept."""
        if not settings.speech:
            return keys_not_set(["SARVAM_API_KEY"])
        if (stop := blocked(request)) is not None:
            return stop
        audio = await request.body()
        if not audio:
            return {"transcript": "", "language_code": ""}
        if len(audio) > MAX_AUDIO_BYTES:
            return error(413, "audio_too_large")
        content_type = request.headers.get("content-type", "audio/webm")
        try:
            return await run_in_threadpool(stt_sarvam.transcribe, settings, audio, content_type)
        except ServiceDown as problem:
            return service_down(problem, "hinglish")

    @app.post("/api/speak")
    def speak(body: SpeakBody, request: Request):
        """Text in, spoken audio out."""
        if not settings.speech:
            return keys_not_set(["SARVAM_API_KEY"])
        if (stop := blocked(request)) is not None:
            return stop
        if not body.text.strip():
            return error(400, "nothing_to_say")
        try:
            audio = tts_sarvam.speak(settings, body.text, body.lang, body.voice)
        except ServiceDown as problem:
            return service_down(problem, body.lang, body.voice)
        return Response(content=audio, media_type="audio/mpeg")

    # The web page. Mounted last so the routes above win.
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


app = create_app()
