"""Plays scripted learner turns against a running Samjhao (with keys) and
prints what the tutor says. A quick end-to-end check of the typed flow.

Run:  python3 scripts/try_session.py   (the app must be up on port 8000)
"""

import json
import time
import urllib.request

BASE = "http://localhost:8000"

SCRIPTS = {
    "Newton, Hinglish, wrong then fixed": [
        "Newton's third law, Class 11",
        "Har action ka equal aur opposite reaction hota hai, isliye dono cancel ho jaate hain aur cheez move nahi karti.",
        "pata nahi",
        "Achha, dono forces alag alag bodies par lagte hain, isliye cancel nahi hote.",
        "Dono forces ek hi time par lagte hain aur same type ke hote hain, aur hamesha pair mein aate hain.",
    ],
    "Too broad": ["physics"],
    "No class given": ["Compound interest", "Class 8"],
    "Punjabi": [
        "ਦਿਨ ਅਤੇ ਰਾਤ ਕਿਉਂ ਹੁੰਦੇ ਹਨ, Class 8",
        "ਧਰਤੀ ਆਪਣੀ axis ਉੱਤੇ ਘੁੰਮਦੀ ਹੈ, ਇਸ ਲਈ ਦਿਨ ਅਤੇ ਰਾਤ ਹੁੰਦੇ ਹਨ।",
    ],
    "Telugu": [
        "మొక్కలు ఆహారం ఎలా తయారు చేసుకుంటాయి, Class 8",
        "మొక్కలు sunlight తో ఆహారం తయారు చేసుకుంటాయి, అవి oxygen తీసుకుని carbon dioxide వదులుతాయి.",
    ],
    "Kannada": [
        "ಚಂದ್ರನಿಗೆ phases ಏಕೆ ಇವೆ, Class 8",
        "ಭೂಮಿಯ ನೆರಳು ಚಂದ್ರನ ಮೇಲೆ ಬೀಳುತ್ತದೆ, ಅದಕ್ಕೆ ಚಂದ್ರ ಕೆಲವೊಮ್ಮೆ ಅರ್ಧ ಕಾಣುತ್ತಾನೆ.",
    ],
}


def post(path: str, body: dict) -> tuple[dict, float]:
    request = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=180) as reply:
            data = json.loads(reply.read())
    except urllib.error.HTTPError as error:
        data = json.loads(error.read())
    return data, time.monotonic() - started


def main() -> None:
    for name, turns in SCRIPTS.items():
        print("\n" + "=" * 70 + "\n" + name)
        print("LEARNER:", turns[0])
        reply, seconds = post("/api/session/start", {"topic_text": turns[0]})
        print(f"TUTOR ({reply.get('action')}, {reply.get('lang')}, {seconds:.1f}s): {reply.get('text')}")
        session = reply.get("session_id")
        for said in turns[1:]:
            print("LEARNER:", said)
            reply, seconds = post(f"/api/session/{session}/turn", {"transcript": said})
            progress = reply.get("progress") or {}
            print(
                f"TUTOR ({reply.get('action')}, {reply.get('lang')}, {seconds:.1f}s,"
                f" {progress.get('done')}/{progress.get('total')}): {reply.get('text')}"
            )
            if reply.get("summary"):
                for point in reply["summary"]["points"]:
                    print(f"   [{point['result']}] {point['statement']}")
                break


if __name__ == "__main__":
    main()
