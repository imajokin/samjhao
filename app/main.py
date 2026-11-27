"""Samjhao server: the API routes, and the web page served from web/.

This file must import and start with no keys set. Anything that needs a key
answers with a clean "keys_not_set" reply instead of crashing. No route ever
returns a key, and learners' words are never logged.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
import hashlib
import re
from html import escape

from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import Settings, load_settings
from app.providers import stt_sarvam, tts_sarvam
from app.providers.errors import DailyCap, ServiceDown
from app.providers.llm_openrouter import OpenRouter
from app.ratelimit import RateLimiter
from app.sessions import SessionStore
from app.tutor.engine import Tutor
from app.tutor.judge import LLMJudge
from app.tutor.strings import say

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class StartBody(BaseModel):
    topic_text: str = Field(default="", max_length=4000)
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


def versioned_home() -> str:
    """The home page, with a version stamp added to each page file it loads.

    The stamp changes whenever any page file changes, so a browser can never
    mix a new page with an old, remembered copy of a script.
    """
    stamp = hashlib.sha256()
    for path in sorted(WEB_DIR.glob("*")):
        if path.is_file():
            stamp.update(path.read_bytes())
    version = stamp.hexdigest()[:10]
    page = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    return re.sub(r'(href|src)="((?:styles\.css|api\.js|audio\.js|app\.js))"',
                  rf'\1="\2?v={version}"', page)


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

    def visitor_of(request: Request) -> str:
        """Who is calling. Behind a tunnel or proxy every request arrives from
        the same address, so use the visitor's own address when it is passed on."""
        forwarded = request.headers.get("cf-connecting-ip") or request.headers.get(
            "x-forwarded-for", ""
        ).split(",")[0]
        return forwarded.strip() or (request.client.host if request.client else "unknown")

    def came_through_a_proxy(request: Request) -> bool:
        names = ("cf-connecting-ip", "cf-ray", "x-forwarded-for", "x-forwarded-host", "forwarded")
        return any(name in request.headers for name in names)

    def blocked(request: Request) -> JSONResponse | None:
        """A reply if this visitor must wait, or None to go ahead."""
        reason = limiter.check(visitor_of(request))
        if reason == "daily_cap":
            return error(429, "daily_cap", text=say("daily_cap", "english"),
                         text_hi=say("daily_cap", "hindi"), video_url=settings.video_url)
        if reason == "rate_limited":
            return error(429, "rate_limited")
        return None

    def service_down(problem: ServiceDown, lang: str, voice: str = "male") -> JSONResponse:
        # Plain words for the learner. The technical detail stays on the server.
        if isinstance(problem, DailyCap):
            return error(429, "daily_cap", text=say("daily_cap", "english"),
                         text_hi=say("daily_cap", "hindi"), video_url=settings.video_url)
        return error(503, "service_down", service=problem.service,
                     text=say("service_down", lang, voice))

    home_page = versioned_home()

    @app.middleware("http")
    async def always_check_for_new_files(request: Request, call_next):
        # Tell browsers to ask before reusing a remembered copy of any file.
        response = await call_next(request)
        response.headers.setdefault("Cache-Control", "no-cache")
        return response

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return home_page

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
        # One turn at a time for each session. A second tap while the first
        # is still being judged is refused instead of being judged twice.
        if not sessions.begin_turn(session.id):
            return error(409, "busy")
        try:
            if body.redo:
                # Go back to how things stood before the misheard answer.
                sessions.rewind(session)
            sessions.remember(session)
            try:
                reply = tutor.turn(session, body.transcript, body.heard_ok, body.silent)
            except ServiceDown as problem:
                # Put everything back exactly as it was, so the learner can say
                # the same answer again and nothing is counted twice.
                sessions.rewind(session)
                return service_down(problem, session.lang, session.voice)
            if reply.get("action") == "done" and not settings.dev_viewer:
                # The summary is all that is needed now. Forget the words.
                sessions.forget_words(session)
            return reply
        finally:
            sessions.end_turn(session.id)

    @app.post("/api/session/{session_id}/finish")
    def session_finish(session_id: str, request: Request):
        """The learner asked to jump straight to the full explanation."""
        if not settings.judging:
            return keys_not_set(["OPENROUTER_API_KEY"])
        if (stop := blocked(request)) is not None:
            return stop
        session = sessions.get(session_id)
        if session is None:
            return error(404, "session_not_found")
        if not sessions.begin_turn(session.id):
            return error(409, "busy")
        try:
            reply = tutor.finish_now(session)
            if reply.get("action") == "done" and not settings.dev_viewer:
                sessions.forget_words(session)
            return reply
        finally:
            sessions.end_turn(session.id)

    @app.get("/api/session/{session_id}/recap")
    def session_recap(session_id: str, request: Request):
        """The full explanation and a diagram, once the session has finished."""
        if not settings.judging:
            return keys_not_set(["OPENROUTER_API_KEY"])
        session = sessions.get(session_id)
        if session is None:
            return error(404, "session_not_found")
        if session.phase != "summary":
            return error(409, "session_not_finished")
        if session.recap is None:
            if (stop := blocked(request)) is not None:
                return stop
            if not sessions.begin_turn(session.id):
                return error(409, "busy")
            try:
                session.recap = tutor.judge.write_recap(session)
            except ServiceDown as problem:
                return service_down(problem, session.lang, session.voice)
            finally:
                sessions.end_turn(session.id)
        return {"lang": session.lang, **session.recap}

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

    if settings.dev_viewer:
        # For the developer only, and only when DEV_VIEWER=on. Shows the
        # conversations that are in memory right now. Nothing is written to disk.
        def session_view(session) -> dict:
            return {
                "id": session.id,
                "topic": session.topic or session.topic_text,
                "level": session.level,
                "lang": session.lang,
                "phase": session.phase,
                "asking_about": session.current_id,
                "points": [
                    {"id": p.id, "statement": p.statement, "status": p.last_status,
                     "result": p.result, "hints": p.hints}
                    for p in session.points
                ],
                "history": [list(line) for line in session.history],
                "notes": session.notes,
            }

        @app.get("/dev/sessions.json")
        def dev_sessions_json(request: Request):
            # Never answer a request that arrived through a tunnel or proxy,
            # even if the switch was left on by mistake.
            if came_through_a_proxy(request):
                return error(404, "not_found")
            return [session_view(s) for s in sessions.recent()]

        @app.get("/dev/sessions", response_class=HTMLResponse)
        def dev_sessions(request: Request):
            if came_through_a_proxy(request):
                return error(404, "not_found")
            parts = ["<!doctype html><meta charset='utf-8'><title>Samjhao viewer</title>",
                     "<body style='font:16px/1.5 system-ui;max-width:820px;margin:20px auto;padding:0 12px'>",
                     "<h1>Samjhao: conversations in memory</h1>",
                     "<p>Developer view. Newest first. Refresh to update.</p>"]
            for view in map(session_view, sessions.recent()):
                parts.append(f"<hr><h2>{escape(view['topic'])} ({escape(view['level'])}, "
                             f"{escape(view['lang'])}, {escape(view['phase'])})</h2><ol>")
                for point in view["points"]:
                    parts.append(f"<li>{escape(point['statement'])} <b>[{escape(str(point['status']))}"
                                 f" / {escape(str(point['result']))}]</b> hints: {len(point['hints'])}</li>")
                parts.append("</ol>")
                notes = iter(view["notes"])
                for who, text in view["history"]:
                    colour = "#0b3d91" if who == "tutor" else "#1b1b1f"
                    extra = ""
                    if who == "tutor":
                        note = next(notes, {})
                        extra = (f" <small style='color:#666'>[{escape(str(note.get('action')))}; model move "
                                 f"{escape(str(note.get('model_move')))}; model reply used: "
                                 f"{note.get('used_model_reply')}]</small>")
                    parts.append(f"<p style='color:{colour}'><b>{escape(who)}:</b> {escape(text)}{extra}</p>")
            return "".join(parts)

    # The web page. Mounted last so the routes above win.
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


app = create_app()
