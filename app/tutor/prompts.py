"""The prompt texts for the judge, and the shape of the answers we ask for.

Call A makes the hidden list of key points, once per session.
Call B judges one learner turn and writes the follow-up question.
The engine, not the model, decides what happens next.
"""

LANGUAGE_RULES = """Samjhao works in Hindi, English, Punjabi, Telugu and Kannada. Learners often mix their language with English.
- Write every word of an Indian language in that language's own script (Devanagari for Hindi, Gurmukhi for Punjabi, Telugu script for Telugu, Kannada script for Kannada), never in Latin letters, even if the transcript is in Latin letters.
- Keep English and technical words in Latin letters, as textbooks do (write "discharge", not "डिस्चार्ज").
- Speak like a friendly older sibling, using the informal "you" of that language (in Hindi "तुम", not "आप")."""

KEY_POINTS_PROMPT = """You are preparing a hidden checklist for a tutor that listens to a learner explain a concept aloud.
What the learner said they will explain (from speech, so spelling may be rough): {topic}
Level they gave separately: {level}
Learner's language: {language}
Topic already confirmed by the learner: {confirmed}

Decide the status first, in this order:
- "confirm" if the topic text looks garbled by speech recognition and you are guessing what was meant. Put your best guess in topic_clean. Never use this status if the topic is already confirmed.
- "too_broad" if this is a whole subject or chapter, not one concept (for example "physics"). Put the subject in narrow_subject.
- "not_a_concept" if there is nothing to explain.
- "need_level" if no class or level was given, in the topic text or separately. An adult may give "college" or "general".
- "unsure" if you are not confident you can list the key points correctly at this level. Give one nearby_topic you are confident about.
- "ok" otherwise.

Always fill topic_clean (the topic, tidied) and level (the class or level you found, or an empty string).

If "ok", write 3 to 5 key points that a correct explanation at this level must include, in the order a good explanation would say them.
- Each key point is one positive idea that can be checked from speech: something a good explanation says.
- Never write a key point that denies a wrong idea ("X is not true", "it is not caused by X", "X does not do Y"). Put the usual wrong idea in common_mistake of the key point it contradicts.
  Bad key point: "The Sun does not move around the Earth." Good: the key point "The Earth spins on its own axis." with common_mistake "The Sun goes around the Earth."
- The key point that learners most often get wrong must be in the list.
- A learner who gives a complete, correct explanation at this level must cover every key point without being asked.
- No examples as key points, no trivia, no side facts, no numbers or values, and no formula unless this level cannot explain the concept without it.

For each key point give:
- statement: one sentence, in English.
- common_mistake: the usual wrong idea, or an empty string.
- question: one short question (under 20 words) in the learner's language that leads toward this idea. It must not state the idea, and must not offer the answer as one of two options ("X या Y?").
- hint: one short sentence in the learner's language that points the learner where to look. It must not state the idea or the answer.
- explanation: two short sentences in the learner's language that state the idea plainly.

Language rules for question, hint and explanation:
{language_rules}
If the status is not "ok", return an empty key_points list.
Return JSON only."""

KEY_POINTS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["ok", "confirm", "too_broad", "not_a_concept", "need_level", "unsure"],
        },
        "topic_clean": {"type": "string"},
        "level": {"type": "string"},
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
                    "question": {"type": "string"},
                    "hint": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": [
                    "id",
                    "statement",
                    "common_mistake",
                    "question",
                    "hint",
                    "explanation",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "status",
        "topic_clean",
        "level",
        "narrow_subject",
        "nearby_topic",
        "key_points",
    ],
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

First fill learner_meaning: a faithful English translation of the learner's latest words. Keep exactly who or what does each action ("the Sun goes around the Earth" is not "the Earth turns"). Do not correct their mistakes and do not add anything. Judge from this meaning.

For each key point, decide: "covered", "missing" or "wrong".
Rules:
- Judge by meaning, not wording. Accept any pronunciation, spelling or transliteration of a term, and its Hindi name.
- Be lenient about grammar and fluency. Be strict about facts: a wrong statement must be marked "wrong", never "covered".
- Mark "covered" only if you can quote the learner's words as evidence. Put that quote in evidence. The quote must be a whole clause with its subject, and that clause must say the same thing as the key point about the same subject.
- If the learner states the usual wrong idea listed for a point, that point is "wrong", even if some of the same words appear.
- When the question refers to what the learner said, repeat it faithfully. Never put words in their mouth. For "missing", evidence is an empty string. For "wrong", quote the wrong words.
- "wrong" means the learner said something that contradicts the point. If they simply did not mention it, it is "missing".
- Do not ask for more detail than the key point states. If the learner said the idea, it is covered.
- If the learner's explanation is complete and correct, mark every point covered. Never invent a gap.
- Do not count anything the tutor said (hints, explanations) as the learner's knowledge.
- A point already covered earlier stays covered unless the learner now contradicts it.
- A point marked "explained by the tutor" is closed. Repeat its last status and never choose it as the gap.

Then choose the gap to ask about, among the points that are still open:
- If any point is "wrong", choose the first wrong one, in order.
- Otherwise choose the first "missing" one, in order.
Put its id in first_gap_id, or null if every point is covered or closed.

Before writing the question, fill must_not_say: the few words that are the answer to that point (the words the learner has to come up with). The question must contain none of them.

Write ONE follow-up question about that point only. If every point is covered or closed, follow_up and must_not_say are empty strings.
- Exactly one question, with one question mark. Never join two questions with "और" or "and".
- Under 20 words.
- It must not reveal the answer or name the missing idea. Never offer the answer as one of two options ("X या Y?").
- If the point is "wrong", point at what the learner said, so they can rethink it.
- Use the language the learner used most in their latest words. Language rules:
{language_rules}
- No praise before the question.
Examples for the point "Action and reaction act on two different bodies" when the learner said the forces cancel:
  Bad (gives options): "ये forces एक ही body पर लगते हैं या अलग-अलग bodies पर?"
  Bad (reveals): "ये forces किन दो अलग-अलग bodies पर लगते हैं?"
  Bad (two questions): "ये forces कहाँ लगते हैं, और cancel क्यों नहीं होते?"
  Good: "तुमने कहा दोनों forces cancel हो जाते हैं। ये forces किस पर लगते हैं?"
- Warm tone. Never use the words "wrong" or "galat" or "गलत", or their equivalents in any language.

For the same chosen point, also write, in the same language as the question:
- hint: one short sentence that points the learner where to look. It must not state the idea or the answer.
- explanation: two short sentences that state the idea plainly.
If every point is covered or closed, both are empty strings.

Also report:
- dont_know: true if the learner said they do not know ("pata nahi", "I don't know").
- off_topic: true if the learner talked about something else.
- reply_lang: the language the learner used most in their latest words: "hindi", "hinglish" (Hindi mixed with English), "english", "punjabi", "telugu" or "kannada".
- unclear_word: if your judgement of a point depends on one word that may have been misheard, give the word heard and the likely alternative. Otherwise null.
Return JSON only."""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "learner_meaning": {"type": "string"},
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
        "reply_lang": {
            "type": "string",
            "enum": ["hindi", "hinglish", "english", "punjabi", "telugu", "kannada"],
        },
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
        "must_not_say": {"type": "string"},
        "follow_up": {"type": "string"},
        "hint": {"type": "string"},
        "explanation": {"type": "string"},
    },
    "required": [
        "learner_meaning",
        "points",
        "first_gap_id",
        "dont_know",
        "off_topic",
        "reply_lang",
        "unclear_word",
        "must_not_say",
        "follow_up",
        "hint",
        "explanation",
    ],
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
