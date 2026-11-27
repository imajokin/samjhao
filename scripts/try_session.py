"""Plays scripted learner turns against a running Samjhao (with keys) and
prints what the tutor says. A quick end-to-end check of the typed flow.

Run:  python3 scripts/try_session.py   (the app must be up on port 8000)
"""

import json
import time
import urllib.request

BASE = "http://localhost:8000"

SCRIPTS = {
    "Opening chat: unfinished sentence, then the explanation": [
        "मेरी Ma'am ने मुझे आज बताया कि",
        "कि plants अपना खाना खुद बनाते हैं sunlight से",
        "leaves में chlorophyll होता है और वो carbon dioxide लेते हैं और oxygen छोड़ते हैं",
    ],
    "Opening chat: greeting and a broad subject": [
        "hello, kaise ho?",
        "mujhe science padhni hai",
        "achha theek hai, day and night kaise hote hain woh",
    ],

    "Newton: stuck twice, then gets it": [
        "Newton's third law, Class 11",
        "Har action ka equal aur opposite reaction hota hai, isliye dono cancel ho jaate hain aur cheez move nahi karti.",
        "pata nahi",
        "Shayad dono forces usi cheez par lagte hain jisko dhakka diya?",
        "Achha, ek force deewar par lagta hai aur doosra mere haath par, alag alag cheezon par.",
    ],
    "Compound interest: gives up three times on one point": [
        "Compound interest, Class 8",
        "Compound interest mein har saal same interest milta hai principal par, bas rate zyada hota hai.",
        "pata nahi",
        "nahi pata yaar",
        "mujhe nahi aata, bata do",
    ],
    "Moon phases in Hindi script, shadow idea": [
        "चाँद के phases क्यों होते हैं, Class 8",
        "चाँद के phases इसलिए होते हैं क्योंकि Earth की shadow चाँद पर पड़ती है, तो कभी आधा दिखता है कभी पूरा।",
        "शायद बादल की वजह से?",
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
    import os

    only = os.environ.get("ONLY", "")
    for name, turns in SCRIPTS.items():
        if only and only.lower() not in name.lower():
            continue
        print("\n" + "=" * 70 + "\n" + name)
        print("LEARNER:", turns[0])
        reply, seconds = post("/api/session/start", {"topic_text": turns[0], "level": "Class 8"})
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
        else:
            if name.startswith("Opening"):
                continue
            # Finish with the give-up button, to see the hints and the explanation.
            for _ in range(12):
                if reply.get("action") == "done" or not session:
                    break
                time.sleep(2.5)  # a person does not tap faster than this
                print("LEARNER: [taps: I don't know]")
                reply, seconds = post(f"/api/session/{session}/turn", {"transcript": "", "silent": True})
                progress = reply.get("progress") or {}
                print(f"TUTOR ({reply.get('action')}, {seconds:.1f}s, {progress.get('done')}/{progress.get('total')}): {reply.get('text')}")
            for point in (reply.get("summary") or {}).get("points", []):
                print(f"   [{point['result']}] {point['statement']}")


if __name__ == "__main__":
    main()
