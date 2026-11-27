"""The prompt texts for the judge, and the shape of the answers we ask for.

Call A makes the hidden list of key points, once per session.
Call B judges one learner turn and writes the follow-up question.
The engine, not the model, decides what happens next.
"""

KEY_POINTS_PROMPT = """You are preparing a hidden checklist for a tutor that listens to a learner explain a concept aloud.
Topic: {topic}
Level: {level}
Learner's language: {language}

Decide the status first:
- "too_broad" if this is a whole subject or chapter, not one concept. Give narrow_subject.
- "not_a_concept" if there is nothing to explain.
- "unsure" if you are not confident you can list the key points correctly at this level. Give one nearby_topic you are confident about.
- "ok" otherwise.

If "ok", write 3 to 5 key points that a correct explanation at this level must include, in the order a good explanation would say them. Each must be checkable from speech. No trivia, no extra facts beyond the level.

For each key point give:
- statement: one sentence, in English.
- common_mistake: the usual wrong idea, or an empty string.
- hint: one short sentence in the learner's language that points toward the idea without stating it.
- explanation: two short sentences in the learner's language.

Write Hindi in Devanagari and keep technical terms in English.
If the status is not "ok", return an empty key_points list.
Return JSON only."""

KEY_POINTS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["ok", "too_broad", "not_a_concept", "unsure"],
        },
        "topic_clean": {"type": "string"},
        "narrow_subject": {"type": "string"},
        "nearby_topic": {"type": "string"},
        "key_points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "statement": {"type": "string"},
                    "common_mistake": {"type": "string"},
                    "hint": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["id", "statement", "common_mistake", "hint", "explanation"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["status", "topic_clean", "narrow_subject", "nearby_topic", "key_points"],
    "additionalProperties": False,
}

JUDGE_PROMPT = """You are judging what a learner just said while explaining a concept aloud.
Topic: {topic}
Level: {level}

The key points a correct explanation must include, with their status so far:
{key_points}

The conversation so far:
{conversation}

The key point the tutor just asked about: {asked_about}

The learner's latest words (a speech transcript, so spelling may be rough):
\"\"\"{transcript}\"\"\"

For each key point, decide: "covered", "missing" or "wrong".
Rules:
- Judge by meaning, not wording. Accept any pronunciation, spelling or transliteration of a term, and its Hindi name.
- Be lenient about grammar and fluency. Be strict about facts: a wrong statement must be marked "wrong", never "covered".
- Mark "covered" only if you can quote the learner's words as evidence. Put that quote in evidence. For "missing", evidence is an empty string. For "wrong", quote the wrong words.
- Do not count anything the tutor said (hints, explanations) as the learner's knowledge.
- A point already covered earlier stays covered unless the learner now contradicts it.

Then find the first key point, in order, that is missing or wrong. Put its id in first_gap_id, or null if every point is covered.

Write ONE follow-up question about that point only: under 20 words, does not reveal the answer, in the language the learner used most in their latest words. Hindi in Devanagari, technical terms in English. Warm tone, like a friendly older sibling. Never use the words "wrong" or "galat". If every point is covered, follow_up is an empty string.

Also report:
- dont_know: true if the learner said they do not know.
- off_topic: true if the learner talked about something else.
- reply_lang: "hindi", "english" or "hinglish", the language the learner used most in their latest words.
- unclear_word: if your judgement of a point depends on one word that may have been misheard, give the word heard and the likely alternative. Otherwise null.
Return JSON only."""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "status": {"type": "string", "enum": ["covered", "missing", "wrong"]},
                    "evidence": {"type": "string"},
                },
                "required": ["id", "status", "evidence"],
                "additionalProperties": False,
            },
        },
        "first_gap_id": {"type": ["integer", "null"]},
        "dont_know": {"type": "boolean"},
        "off_topic": {"type": "boolean"},
        "reply_lang": {"type": "string", "enum": ["hindi", "english", "hinglish"]},
        "unclear_word": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "properties": {
                        "heard": {"type": "string"},
                        "likely": {"type": "string"},
                    },
                    "required": ["heard", "likely"],
                    "additionalProperties": False,
                },
            ]
        },
        "follow_up": {"type": "string"},
    },
    "required": [
        "points",
        "first_gap_id",
        "dont_know",
        "off_topic",
        "reply_lang",
        "unclear_word",
        "follow_up",
    ],
    "additionalProperties": False,
}

# Used only when a verdict model that cannot write (Jev) does the judging.
# A regular model then writes the question for the gap that was found.
FOLLOW_UP_PROMPT = """A learner is explaining a concept aloud. A judge has found the first point they missed or got wrong.
Topic: {topic}
Level: {level}
The point: {statement}
The judge's verdict on it: {status}
The learner's latest words:
\"\"\"{transcript}\"\"\"

Write ONE follow-up question about that point only: under 20 words, does not reveal the answer, in the language the learner used most. Hindi in Devanagari, technical terms in English. Warm tone, like a friendly older sibling. Never use the words "wrong" or "galat".
Return JSON only."""

FOLLOW_UP_SCHEMA = {
    "type": "object",
    "properties": {
        "reply_lang": {"type": "string", "enum": ["hindi", "english", "hinglish"]},
        "follow_up": {"type": "string"},
    },
    "required": ["reply_lang", "follow_up"],
    "additionalProperties": False,
}


def format_key_points(points: list[dict]) -> str:
    """The key points as numbered lines for the judge prompt."""
    lines = []
    for point in points:
        status = point.get("status", "not yet judged")
        mistake = point.get("common_mistake") or "none listed"
        lines.append(
            f"{point['id']}. {point['statement']} "
            f"(status so far: {status}; usual wrong idea: {mistake})"
        )
    return "\n".join(lines)
