"""Runs sample explanations through each candidate judging model.

Each sample has a known flaw (HANDOVER.md section 9.3), plus one fully correct
explanation. For each model we record what it marked, the follow-up question
it wrote, how long it took and what it cost.

Run from the project folder:   python3 scripts/try_prompts.py
It reads OPENROUTER_API_KEY from .env and never prints it.
Results go to scripts/out/ (not committed).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.tutor import prompts  # noqa: E402

CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# The judging model Shubham picked on 27 Nov 2026. To compare others, run with
# MODELS=model-one,model-two python3 scripts/try_prompts.py
MODELS = [
    m.strip()
    for m in os.environ.get("MODELS", "anthropic/claude-sonnet-5.5").split(",")
    if m.strip()
]
RUNS = int(os.environ.get("RUNS", "1"))
# Whether the model "thinks" before answering. Off is about twice as fast.
THINK_SETUP = os.environ.get("THINK_SETUP", "on") == "on"
THINK_TURN = os.environ.get("THINK_TURN", "on") == "on"

SAMPLES = [
    {
        "id": 1,
        "topic": "Why the moon has phases",
        "level": "Class 8",
        "said": "Chand ke phases isliye hote hain kyunki Earth ki shadow chand par padti hai, toh kabhi aadha dikhta hai kabhi poora.",
        "must_catch": "Shadow idea is wrong. Reflection and orbit are missing.",
    },
    {
        "id": 2,
        "topic": "Why we see lightning before we hear thunder",
        "level": "Class 8",
        "said": "Bijli pehle dikhti hai kyunki light bahut fast hoti hai.",
        "must_catch": "Nothing about sound being slower, or both starting together.",
    },
    {
        "id": 3,
        "topic": "How plants make food (photosynthesis)",
        "level": "Class 8",
        "said": "Plants sunlight se khana banate hain, leaves mein chlorophyll hota hai, aur woh oxygen lete hain aur carbon dioxide chhodte hain.",
        "must_catch": "Gases are swapped. Water is missing.",
    },
    {
        "id": 4,
        "topic": "Newton's third law",
        "level": "Class 11",
        "said": "Har action ka equal aur opposite reaction hota hai, isliye dono cancel ho jaate hain aur cheez move nahi karti.",
        "must_catch": "The two forces act on different bodies, so they do not cancel.",
    },
    {
        "id": 5,
        "topic": "Compound interest",
        "level": "Class 8",
        "said": "Compound interest mein har saal same interest milta hai principal par, bas rate zyada hota hai.",
        "must_catch": "Interest is earned on earlier interest too.",
    },
    {
        "id": 6,
        "topic": "Why we have day and night",
        "level": "Class 8",
        "said": "Earth apni axis par ghoomti hai, ek poora chakkar lagbhag 24 ghante mein hota hai. Sooraj ki roshni ek time par sirf aadhi Earth par padti hai, jo hissa sooraj ke saamne hai wahan din hota hai aur doosri taraf raat. Jaise jaise Earth ghoomti hai, hamari jagah dheere dheere roshni mein aati hai toh din ho jaata hai, aur phir ghoom kar roshni se bahar chali jaati hai toh raat ho jaati hai.",
        "must_catch": "NOTHING. This one is fully correct and must be approved with no invented gap.",
    },
    {
        "id": 7,
        "topic": "Why we have day and night",
        "level": "Class 8",
        "said": "Sooraj Earth ke chaaron taraf ghoomta hai isliye din aur raat hote hain, jahan sooraj hota hai wahan din.",
        "must_catch": "The sun does not go around the Earth. The Earth's own spin is missing and must NOT be credited.",
    },
    {
        "id": 8,
        "topic": "Why we have day and night",
        "level": "Class 8",
        "said": "सूरज Earth के चारों तरफ़ घूमता है इसलिए दिन और रात होते हैं, जहाँ सूरज होता है वहाँ दिन।",
        "must_catch": "Same as sample 7, written in Hindi script as the speech service would write it.",
    },
]
# To run only some samples: ONLY=7 or ONLY=1,4
if os.environ.get("ONLY"):
    SAMPLES = [s for s in SAMPLES if str(s["id"]) in os.environ["ONLY"].split(",")]


def read_key() -> str:
    """The OpenRouter key from .env or the environment. Never printed."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key


def post(url: str, key: str, body: dict) -> tuple[dict, float]:
    """One request. Returns the reply and the seconds it took."""
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "Samjhao",
        },
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=120) as reply:
            data = json.loads(reply.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:400]
        raise RuntimeError(f"HTTP {error.code}: {detail}") from None
    return data, time.monotonic() - started


def parse_json(text: str) -> dict:
    """The JSON inside a model reply, even if wrapped in a code fence."""
    text = (text or "").strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1])


def ask_model(
    key: str, model: str, prompt: str, schema: dict, name: str, think: bool = False
) -> dict:
    """Asks a regular model for JSON. Retries once without the strict schema."""
    body = {
        "reasoning": {"enabled": think},
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": name, "strict": True, "schema": schema},
        },
    }
    seconds = 0.0
    last_error = None
    for attempt in (1, 2):
        try:
            data, took = post(CHAT_URL, key, body)
            seconds += took
            answer = parse_json(data["choices"][0]["message"]["content"])
            usage = data.get("usage") or {}
            return {"answer": answer, "seconds": seconds, "cost": usage.get("cost") or 0.0}
        except Exception as error:  # noqa: BLE001 - report any failure in the table
            last_error = error
            body.pop("response_format", None)
    raise RuntimeError(f"{model}: {last_error}")


def key_points_prompt(sample: dict) -> str:
    return prompts.KEY_POINTS_PROMPT.format(
        topic=sample["topic"],
        level=sample["level"],
        confirmed="yes",
    )


def run_regular(key: str, model: str, sample: dict) -> dict:
    """One model does both jobs for one sample."""
    made = ask_model(key, model, key_points_prompt(sample), prompts.KEY_POINTS_SCHEMA, "key_points", THINK_SETUP)
    points = made["answer"].get("key_points", [])
    judged = ask_model(
        key,
        model,
        prompts.JUDGE_PROMPT.format(
            topic=sample["topic"],
            level=sample["level"],
            key_points=prompts.format_key_points(points),
            conversation="(nothing yet; this is the learner's first explanation)",
            asked_about="none; this is the first explanation",
            transcript=sample["said"],
            language_rules=prompts.LANGUAGE_RULES,
        ),
        prompts.JUDGE_SCHEMA,
        "judgement",
        THINK_TURN,
    )
    return {
        "key_points_status": made["answer"].get("status"),
        "key_points": points,
        "judgement": judged["answer"],
        "setup_seconds": round(made["seconds"], 2),
        "turn_seconds": round(judged["seconds"], 2),
        "setup_cost": made["cost"],
        "turn_cost": judged["cost"],
    }


def run_one(key: str, arm: str, sample: dict) -> dict:
    try:
        result = run_regular(key, arm, sample)
    except Exception as error:  # noqa: BLE001 - one failure must not stop the rest
        result = {"error": str(error)}
    return {"arm": arm, "sample": sample["id"], **result}


def print_report(results: list[dict]) -> None:
    for sample in SAMPLES:
        print("\n" + "=" * 78)
        print(f"Sample {sample['id']}: {sample['topic']} ({sample['level']})")
        print(f"Learner said: {sample['said']}")
        print(f"Must catch:   {sample['must_catch']}")
        for result in (r for r in results if r["sample"] == sample["id"]):
            print("\n--- " + result["arm"])
            if "error" in result:
                print("  FAILED: " + result["error"])
                continue
            judgement = result["judgement"]
            status_by_id = {p["id"]: p for p in judgement.get("points", [])}
            for point in result["key_points"]:
                judged = status_by_id.get(point["id"], {})
                print(f"  [{judged.get('status', '?'):>7}] {point['statement']}")
                if judged.get("status") == "covered":
                    print(f"            evidence: {judged.get('evidence')}")
            print(f"  First gap: point {judgement.get('first_gap_id')}")
            print(f"  Question:  {judgement.get('follow_up')}")
            gap = next((p for p in result["key_points"] if p["id"] == judgement.get("first_gap_id")), None)
            print(f"  Hint:      {judgement.get('hint')}")
            print(
                f"  Time: setup {result['setup_seconds']}s, turn {result['turn_seconds']}s"
                f" | Cost: setup ${result['setup_cost']:.5f}, turn ${result['turn_cost']:.5f}"
            )


def main() -> None:
    key = read_key()
    if not key:
        print("OPENROUTER_API_KEY is not set in .env. Nothing was run.")
        sys.exit(1)

    jobs = [(arm, sample) for sample in SAMPLES for arm in MODELS for _ in range(RUNS)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda job: run_one(key, *job), jobs))

    out_dir = ROOT / "scripts" / "out"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"judge-comparison-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    print_report(results)
    total = sum(r.get("setup_cost", 0) + r.get("turn_cost", 0) for r in results)
    ok = [r for r in results if "error" not in r]
    if ok:
        print(
            f"\nThinking: setup {'on' if THINK_SETUP else 'off'}, turn {'on' if THINK_TURN else 'off'}"
            f" | average setup {sum(r['setup_seconds'] for r in ok) / len(ok):.1f}s,"
            f" average turn {sum(r['turn_seconds'] for r in ok) / len(ok):.1f}s"
        )
    print(f"\nTotal spent on this run: ${total:.4f}")
    print(f"Full results saved to {out_file}")


if __name__ == "__main__":
    main()
