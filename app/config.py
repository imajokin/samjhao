"""Reads the settings and works out which keys are set.

Every setting is optional. With nothing set, the app still starts and the
home screen says that keys are not set. Keys are read here and nowhere else,
and no function in this file ever returns a key to the browser.
"""

import os
from dataclasses import dataclass

# The links shown on the no-keys screen. Reviewers start the app with no .env
# file, so these must live in the code. They are filled in before submission.
DEFAULT_LIVE_DEMO_URL = ""
DEFAULT_VIDEO_URL = ""


def _text(name: str, default: str = "") -> str:
    """A setting as text. Blank or missing gives the default."""
    value = os.environ.get(name, "").strip()
    return value or default


def _number(name: str, default: int) -> int:
    """A setting as a whole number. A bad value gives the default, not a crash."""
    try:
        value = int(_text(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    llm_model: str
    llm_base_url: str
    sarvam_api_key: str
    sarvam_stt_model: str
    sarvam_stt_mode: str
    sarvam_tts_voice: str
    live_demo_url: str
    video_url: str
    session_ttl_minutes: int
    rate_limit_per_minute: int
    daily_request_cap: int

    @property
    def judging(self) -> bool:
        """True when the language model key is set."""
        return bool(self.openrouter_api_key)

    @property
    def speech(self) -> bool:
        """True when the speech key is set."""
        return bool(self.sarvam_api_key)

    def missing_keys(self) -> list[str]:
        """Names of the keys that are not set. Names only, never values."""
        missing = []
        if not self.judging:
            missing.append("OPENROUTER_API_KEY")
        if not self.speech:
            missing.append("SARVAM_API_KEY")
        return missing

    def public(self) -> dict:
        """What the browser is allowed to know. Contains no key."""
        return {
            "judging": self.judging,
            "speech": self.speech,
            "live_demo_url": self.live_demo_url,
            "video_url": self.video_url,
        }


def load_settings() -> Settings:
    return Settings(
        openrouter_api_key=_text("OPENROUTER_API_KEY"),
        llm_model=_text("LLM_MODEL"),
        llm_base_url=_text("LLM_BASE_URL"),
        sarvam_api_key=_text("SARVAM_API_KEY"),
        sarvam_stt_model=_text("SARVAM_STT_MODEL"),
        sarvam_stt_mode=_text("SARVAM_STT_MODE"),
        sarvam_tts_voice=_text("SARVAM_TTS_VOICE"),
        live_demo_url=_text("LIVE_DEMO_URL", DEFAULT_LIVE_DEMO_URL),
        video_url=_text("VIDEO_URL", DEFAULT_VIDEO_URL),
        session_ttl_minutes=_number("SESSION_TTL_MINUTES", 30),
        rate_limit_per_minute=_number("RATE_LIMIT_PER_MINUTE", 30),
        daily_request_cap=_number("DAILY_REQUEST_CAP", 2000),
    )
