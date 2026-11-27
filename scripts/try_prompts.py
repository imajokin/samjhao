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
DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"

# Regular models: each does both jobs (key points, then verdict + question).
MODELS = [
    "anthropic/claude-haiku-5.5",
    "openai/gpt-6-luna",
    "openai/gpt-6.1-terra",
]
# Jev only gives the verdict. This model writes the key points and the question.
JEV_MODEL = "typesafe/jev-1.14"
JEV_WRITER = "anthropic/claude-haiku-5.5"

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
        "level": "not given",
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
]


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


def ask_model(key: str, model: str, prompt: str, schema: dict, name: str) -> dict:
    """Asks a regular model for JSON. Retries once without the strict schema."""
    body = {
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


def ask_jev(key: str, sample: dict, points: list[dict]) -> dict:
    """Asks Jev for a verdict on each key point."""
    questions = {}
    for point in points:
        questions[f"point_{point['id']}"] = {
            "type": "choice",
            "instructions": (
                "A learner is explaining the topic aloud. Judge by meaning, not wording, "
                "and be strict about facts. Did the learner's own words cover this key point: "
                f"{point['statement']}"
            ),
            "criteria": {
                "covered": "The learner clearly and correctly said this idea in their own words.",
                "missing": "The learner did not say this idea.",
                "wrong": "The learner said something that contradicts this idea, or stated the usual wrong idea: "
                + (point.get("common_mistake") or "none listed"),
            },
        }
    questions["dont_know"] = {
        "type": "noul",
        "instructions": "Did the learner say that they do not know?",
    }
    questions["off_topic"] = {
        "type": "noul",
        "instructions": "Did the learner talk about something other than the topic?",
    }
    body = {
        "model": JEV_MODEL,
        "state": {
            "topic": sample["topic"],
            "level": sample["level"],
            "learner_said": sample["said"],
        },
        "questions": questions,
    }
    data, seconds = post(DECISIONS_URL, key, body)
    usage = data.get("usage") or {}
    return {"answers": data.get("answers") or {}, "seconds": seconds, "cost": usage.get("cost") or 0.0}


def key_points_prompt(sample: dict) -> str:
    return prompts.KEY_POINTS_PROMPT.format(
        topic=sample["topic"], level=sample["level"], language="Hindi mixed with English"
    )


def run_regular(key: str, model: str, sample: dict) -> dict:
    """One model does both jobs for one sample."""
    made = ask_model(key, model, key_points_prompt(sample), prompts.KEY_POINTS_SCHEMA, "key_points")
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
        ),
        prompts.JUDGE_SCHEMA,
        "judgement",
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


def run_jev(key: str, sample: dict) -> dict:
    """Jev gives the verdict; a regular model writes key points and the question."""
    made = ask_model(key, JEV_WRITER, key_points_prompt(sample), prompts.KEY_POINTS_SCHEMA, "key_points")
    points = made["answer"].get("key_points", [])
    verdict = ask_jev(key, sample, points)
    answers = verdict["answers"]

    judged_points, first_gap = [], None
    for point in points:
        answer = answers.get(f"point_{point['id']}") or {}
        status = answer.get("choice", "no answer")
        judged_points.append(
            {"id": point["id"], "status": status, "confidence": answer.get("confidence")}
        )
        if first_gap is None and status != "covered":
            first_gap = point

    seconds, cost, follow_up, lang = verdict["seconds"], verdict["cost"], "", ""
    if first_gap is not None:
        status = next(p["status"] for p in judged_points if p["id"] == first_gap["id"])
        written = ask_model(
            key,
            JEV_WRITER,
            prompts.FOLLOW_UP_PROMPT.format(
                topic=sample["topic"],
                level=sample["level"],
                statement=first_gap["statement"],
                status=status,
                transcript=sample["said"],
            ),
            prompts.FOLLOW_UP_SCHEMA,
            "follow_up",
        )
        seconds += written["seconds"]
        cost += written["cost"]
        follow_up = written["answer"].get("follow_up", "")
        lang = written["answer"].get("reply_lang", "")

    return {
        "key_points_status": made["answer"].get("status"),
        "key_points": points,
        "judgement": {
            "points": judged_points,
            "first_gap_id": first_gap["id"] if first_gap else None,
            "dont_know": (answers.get("dont_know") or {}).get("noul"),
            "off_topic": (answers.get("off_topic") or {}).get("noul"),
            "reply_lang": lang,
            "follow_up": follow_up,
        },
        "setup_seconds": round(made["seconds"], 2),
        "turn_seconds": round(seconds, 2),
        "setup_cost": made["cost"],
        "turn_cost": cost,
    }


def run_one(key: str, arm: str, sample: dict) -> dict:
    try:
        result = run_jev(key, sample) if arm == "jev" else run_regular(key, arm, sample)
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
                confidence = judged.get("confidence")
                extra = f" (confidence {confidence})" if confidence is not None else ""
                print(f"  [{judged.get('status', '?'):>7}]{extra} {point['statement']}")
            print(f"  First gap: point {judgement.get('first_gap_id')}")
            print(f"  Question:  {judgement.get('follow_up')}")
            print(
                f"  Time: setup {result['setup_seconds']}s, turn {result['turn_seconds']}s"
                f" | Cost: setup ${result['setup_cost']:.5f}, turn ${result['turn_cost']:.5f}"
            )


def main() -> None:
    key = read_key()
    if not key:
        print("OPENROUTER_API_KEY is not set in .env. Nothing was run.")
        sys.exit(1)

    arms = MODELS + ["jev"]
    jobs = [(arm, sample) for sample in SAMPLES for arm in arms]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda job: run_one(key, *job), jobs))

    out_dir = ROOT / "scripts" / "out"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"judge-comparison-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    print_report(results)
    total = sum(r.get("setup_cost", 0) + r.get("turn_cost", 0) for r in results)
    print(f"\nTotal spent on this run: ${total:.4f}")
    print(f"Full results saved to {out_file}")


if __name__ == "__main__":
    main()
