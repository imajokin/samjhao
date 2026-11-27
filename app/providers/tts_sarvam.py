"""Text to speech with Sarvam, in the male or female voice the learner chose.

Hindi and the other Indian languages must be sent in their own script;
Sarvam reads Latin-letter Hindi badly. The key is never logged.
"""

import base64

import httpx

from app.config import Settings
from app.providers.errors import ServiceDown
from app.tutor.language import SPEECH_CODES

TTS_URL = "https://api.sarvam.ai/text-to-speech"
TIMEOUT_SECONDS = 45


def trim_to_sentences(text: str, limit: int) -> str:
    """The text cut to at most `limit` characters, ending on a whole sentence
    where possible, so the voice never stops in the middle of a word."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    last_stop = max(cut.rfind(mark) for mark in ("।", ".", "?", "!", "…"))
    if last_stop >= limit // 2:
        return cut[: last_stop + 1]
    return cut.rsplit(" ", 1)[0]


def speak(settings: Settings, text: str, lang: str, voice: str) -> bytes:
    """The text as spoken audio (MP3)."""
    speaker = (
        settings.sarvam_tts_voice_female if voice == "female" else settings.sarvam_tts_voice_male
    )
    body = {
        # Our own ceiling, well under Sarvam's 2,500, to keep the cost of
        # each spoken reply small on a public link.
        "text": trim_to_sentences(text, settings.speak_max_chars),
        "language_code": SPEECH_CODES.get(lang, "hi-IN"),
        "model": settings.sarvam_tts_model,
        "speaker": speaker,
        "output_audio_codec": "mp3",
    }
    headers = {"api-subscription-key": settings.sarvam_api_key}

    detail = ""
    for _attempt in (1, 2):
        try:
            reply = httpx.post(TTS_URL, json=body, headers=headers, timeout=TIMEOUT_SECONDS)
            if reply.status_code == 200:
                return base64.b64decode(reply.json()["audios"][0])
            detail = f"HTTP {reply.status_code}"
            if reply.status_code in (400, 401, 402, 403):
                break
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            detail = type(error).__name__
    raise ServiceDown("speech", detail)
