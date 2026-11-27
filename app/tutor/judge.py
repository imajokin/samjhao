"""The judge: asks the language model for key points and for a verdict.

All judging is done by the language model. There is no rule-based judge.
This file only fills in the prompts and tidies the answers into our shapes.
"""

import re

from app.tutor import prompts
from app.tutor.language import PROMPT_NAMES
from app.tutor.models import Judgement, KeyPoint, Session, TopicPlan

STATUSES = ("covered", "missing", "wrong")
HISTORY_LINES = 12


class LLMJudge:
    def __init__(self, llm):
        self.llm = llm  # anything with ask_json(prompt, schema, name)

    def make_key_points(
        self, topic: str, level: str, confirmed: bool, conversation: str = "",
        preferred_lang: str = "",
    ) -> TopicPlan:
        prompt = prompts.KEY_POINTS_PROMPT.format(
            topic=topic,
            level=level or "not known",
            confirmed="yes" if confirmed else "no",
            conversation=conversation or "(nothing yet; these are the learner's first words)",
            app_language=_app_language_note(preferred_lang),
            language_rules=prompts.LANGUAGE_RULES,
        )
        answer = self.llm.ask_json(prompt, prompts.KEY_POINTS_SCHEMA, "key_points")
        points = []
        for number, item in enumerate(answer.get("key_points") or [], start=1):
            if not isinstance(item, dict) or not str(item.get("statement", "")).strip():
                continue
            points.append(
                KeyPoint(
                    id=number,  # our own numbering, so ids are always 1, 2, 3...
                    statement=str(item["statement"]).strip(),
                    common_mistake=str(item.get("common_mistake", "")).strip(),
                )
            )
        return TopicPlan(
            status=str(answer.get("status", "unsure")),
            topic_clean=str(answer.get("topic_clean", "")).strip(),
            level=str(answer.get("level", "")).strip(),
            has_explanation=bool(answer.get("has_explanation")),
            reply_lang=str(answer.get("reply_lang") or "").strip(),
            reply=str(answer.get("reply") or "").strip(),
            narrow_subject=str(answer.get("narrow_subject", "")).strip(),
            nearby_topic=str(answer.get("nearby_topic", "")).strip(),
            key_points=points[:4],
        )

    def judge_turn(self, session: Session, transcript: str) -> Judgement:
        asked = session.point(session.current_id)
        # The latest learner words are passed separately, so leave them out here.
        earlier = session.history[:-1][-HISTORY_LINES:]
        conversation = "\n".join(f"{who}: {text}" for who, text in earlier)
        prompt = prompts.JUDGE_PROMPT.format(
            topic=session.topic,
            level=session.level or "not given",
            key_points=prompts.format_key_points(
                [
                    {
                        "id": p.id,
                        "statement": p.statement,
                        "common_mistake": p.common_mistake,
                        "status": p.last_status if p.closed else "open, " + p.last_status,
                    }
                    for p in session.points
                ]
            ),
            conversation=conversation or "(nothing yet)",
            asked_about=(
                f"point {asked.id}: {asked.statement}"
                if asked
                else "none; this is the learner's first explanation"
            ),
            hints_given=(
                " | ".join(asked.hints) if asked and asked.hints else "none yet"
            ),
            questions_total=session.questions_total or "3",
            questions_asked=session.questions_asked,
            questions_note=_questions_note(session),
            app_language=_app_language_note(session.preferred_lang),
            transcript=transcript,
            language_rules=prompts.LANGUAGE_RULES,
        )
        answer = self.llm.ask_json(prompt, prompts.JUDGE_SCHEMA, "judgement")

        statuses, evidence = {}, {}
        for item in answer.get("points") or []:
            if isinstance(item, dict) and item.get("status") in STATUSES:
                try:
                    statuses[int(item["id"])] = item["status"]
                    evidence[int(item["id"])] = str(item.get("evidence") or "").strip()
                except (KeyError, TypeError, ValueError):
                    continue
        about = answer.get("about_point_id")
        unclear = answer.get("unclear_word")
        return Judgement(
            statuses=statuses,
            dont_know=bool(answer.get("dont_know")),
            off_topic=bool(answer.get("off_topic")),
            learner_asked=bool(answer.get("learner_asked")),
            reply_lang=str(answer.get("reply_lang") or session.lang),
            unclear_word=unclear if isinstance(unclear, dict) else None,
            move=str(answer.get("move") or ""),
            about_id=about if isinstance(about, int) else None,
            reply=str(answer.get("reply") or "").strip(),
            question=str(answer.get("question") or "").strip(),
            hint=str(answer.get("hint") or "").strip(),
            explanation=str(answer.get("explanation") or "").strip(),
            meaning=str(answer.get("learner_meaning") or "").strip(),
            evidence=evidence,
        )

    def write_support(self, session: Session, point: KeyPoint) -> None:
        learner_lines = [text for who, text in session.history if who == "learner"]
        prompt = prompts.SUPPORT_PROMPT.format(
            topic=session.topic,
            level=session.level or "not given",
            statement=point.statement,
            common_mistake=point.common_mistake or "none listed",
            conversation="\n".join(learner_lines[-4:]) or "(nothing yet)",
            language=PROMPT_NAMES.get(session.lang, "Hindi mixed with English"),
            language_rules=prompts.LANGUAGE_RULES,
        )
        answer = self.llm.ask_json(prompt, prompts.SUPPORT_SCHEMA, "support")
        point.question = str(answer.get("question") or "").strip()
        point.hint = str(answer.get("hint") or "").strip()
        point.hint2 = str(answer.get("hint2") or "").strip()
        point.explanation = str(answer.get("explanation") or "").strip() or point.explanation

    def write_recap(self, session: Session) -> dict:
        lines = []
        for point in session.points:
            how = {
                "green": "explained it alone",
                "amber": "needed a hint or had it explained",
                "skipped": "was not asked about it",
            }.get(point.result or "", "did not reach it")
            lines.append(f"{point.id}. {point.statement} (the learner {how})")
        prompt = prompts.RECAP_PROMPT.format(
            topic=session.topic,
            level=session.level or "not given",
            key_points="\n".join(lines),
            language=PROMPT_NAMES.get(session.lang, "Hindi mixed with English"),
            language_rules=prompts.LANGUAGE_RULES,
        )
        # Writing, not judging: the lightest thinking level keeps the wait short.
        answer = self.llm.ask_json(prompt, prompts.RECAP_SCHEMA, "recap", light=True)
        return {
            "explanation": str(answer.get("explanation") or "").strip(),
            "diagram_caption": str(answer.get("diagram_caption") or "").strip(),
            "svg": safe_svg(str(answer.get("svg") or "")),
        }


def _app_language_note(preferred_lang: str) -> str:
    """Tells the model which language the learner picked in the app, if any."""
    if not preferred_lang:
        return "none chosen. Use the language the learner speaks."
    name = PROMPT_NAMES.get(preferred_lang, preferred_lang)
    return (
        f"{name}. The learner chose this language in the app. Set reply_lang to "
        f'"{preferred_lang}" and write your reply in it, even if they mix in other languages.'
    )


def _questions_note(session: Session) -> str:
    """Tells the model where the learner is in the session."""
    total = session.questions_total
    asked = session.questions_asked
    if not total:
        return (
            "This is the first explanation: count the points that are not covered, "
            "and you will ask about that many, but never more than 3."
        )
    if asked >= total:
        return "You have asked about the maximum number of points. Ask about no new point."
    if asked == total - 1:
        return "The next point you ask about is the LAST one."
    return f"You may ask about {total - asked} more."


_SVG_ALLOWED = {
    "svg", "g", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "path", "text", "tspan", "defs", "marker", "title",
}


def safe_svg(svg: str) -> str:
    """The diagram, or an empty string if it contains anything beyond plain
    shapes and text. The page also shows it only as an image, never as code."""
    svg = svg.strip()
    start, end = svg.find("<svg"), svg.rfind("</svg>")
    if start < 0 or end < 0:
        return ""
    svg = svg[start : end + len("</svg>")]
    if len(svg) > 30000:
        return ""
    lowered = svg.lower()
    if re.search(r"\bon[a-z]+\s*=|javascript:|<!|<\?|href\s*=|url\(\s*['\"]?\s*(?!#)", lowered):
        return ""
    for tag in re.findall(r"<\s*/?\s*([a-zA-Z][\w:-]*)", svg):
        if tag not in _SVG_ALLOWED:
            return ""
    return svg
