"""Speech to text with Sarvam's regular model (not Sarvam Dictate).

Sarvam accepts up to 30 seconds per request, so the browser sends long
explanations in pieces. The audio is passed straight through and never
stored. The key is sent only to Sarvam and is never logged.
"""

import httpx

from app.config import Settings
from app.providers.errors import ServiceDown

STT_URL = "https://api.sarvam.ai/speech-to-text"
TIMEOUT_SECONDS = 45

# File names help Sarvam recognise the format the browser recorded.
_EXTENSIONS = {
    "audio/webm": "webm",
    "video/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "mp4",
    "audio/x-m4a": "m4a",
    "audio/aac": "aac",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
}


def transcribe(settings: Settings, audio: bytes, content_type: str) -> dict:
    """{"transcript": text, "language_code": "hi-IN" or ""} for one piece of audio."""
    kind = (content_type or "audio/webm").split(";")[0].strip().lower()
    extension = _EXTENSIONS.get(kind, "webm")
    files = {"file": (f"speech.{extension}", audio, kind)}
    data = {"model": settings.sarvam_stt_model, "mode": settings.sarvam_stt_mode}
    headers = {"api-subscription-key": settings.sarvam_api_key}

    detail = ""
    for _attempt in (1, 2):
        try:
            reply = httpx.post(STT_URL, files=files, data=data, headers=headers,
                               timeout=TIMEOUT_SECONDS)
        except httpx.HTTPError as error:
            detail = type(error).__name__
            continue
        if reply.status_code == 200:
            try:
                body = reply.json()
                return {
                    "transcript": str(body.get("transcript") or "").strip(),
                    "language_code": str(body.get("language_code") or ""),
                }
            except (ValueError, AttributeError):
                detail = "unreadable reply"
                continue
        if reply.status_code == 400 and "read the file" in reply.text:
            # An empty or broken recording: the same as hearing nothing.
            return {"transcript": "", "language_code": ""}
        detail = f"HTTP {reply.status_code}"
        if reply.status_code in (400, 401, 402, 403):
            break  # trying again will not help
    raise ServiceDown("speech", detail)
