"""Makes one short sample of each shortlisted Sarvam voice, so Shubham can
pick a male and a female voice by ear.

Run from the project folder:   python3 scripts/try_voices.py
It reads SARVAM_API_KEY from .env and never prints it.
Samples go to scripts/out/voices/ (not committed).
"""

import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TTS_URL = "https://api.sarvam.ai/text-to-speech"
MODEL = "bulbul:v3"  # its named speakers work in all five of our languages

SHORTLIST = [
    ("shubh", "male"),
    ("rahul", "male"),
    ("aditya", "male"),
    ("ritu", "female"),
    ("priya", "female"),
]

# The same lines Samjhao says at the start, in each voice's own gender.
TEXT = {
    "male": "आज क्या समझाओगे? Topic बोलो, और अपनी class बताओ। मुझे यह ऐसे समझाओ जैसे मैं तुम्हारा छोटा भाई हूँ। तुमने कहा दोनों forces cancel हो जाते हैं। ये दोनों forces किस पर लगते हैं?",
    "female": "आज क्या समझाओगे? Topic बोलो, और अपनी class बताओ। मुझे यह ऐसे समझाओ जैसे मैं तुम्हारी छोटी बहन हूँ। तुमने कहा दोनों forces cancel हो जाते हैं। ये दोनों forces किस पर लगते हैं?",
}


def read_key() -> str:
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("SARVAM_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def speak(key: str, text: str, speaker: str, language_code: str = "hi-IN") -> bytes:
    body = {"text": text, "language_code": language_code, "model": MODEL, "speaker": speaker}
    request = urllib.request.Request(
        TTS_URL,
        data=json.dumps(body).encode(),
        headers={"api-subscription-key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as reply:
            data = json.loads(reply.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"HTTP {error.code}: {error.read().decode(errors='replace')[:300]}") from None
    return base64.b64decode(data["audios"][0])


def main() -> None:
    key = read_key()
    if not key:
        print("SARVAM_API_KEY is not set in .env. Nothing was run.")
        sys.exit(1)
    out_dir = ROOT / "scripts" / "out" / "voices"
    out_dir.mkdir(parents=True, exist_ok=True)
    for number, (speaker, gender) in enumerate(SHORTLIST, start=1):
        try:
            audio = speak(key, TEXT[gender], speaker)
        except RuntimeError as error:
            print(f"{speaker}: FAILED {error}")
            continue
        path = out_dir / f"{number}-{gender}-{speaker}.wav"
        path.write_bytes(audio)
        print(f"{speaker} ({gender}): saved {path.name}, {len(audio) // 1024} KB")


if __name__ == "__main__":
    main()
