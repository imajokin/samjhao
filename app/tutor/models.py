"""The data shapes the tutor works with."""

from dataclasses import dataclass, field
from typing import Protocol

# Result colours on the summary screen.
GREEN = "green"  # the learner explained it without a hint
AMBER = "amber"  # a hint was given, or the app explained it


@dataclass
class KeyPoint:
    """One idea a correct explanation must include. Hidden until the summary."""

    id: int
    statement: str
    common_mistake: str = ""
    # Help text in the learner's language, written when first needed:
    support_lang: str = ""  # the language the four texts below are written in
    question: str = ""  # a question that leads toward the idea
    hint: str = ""  # a gentle hint: where to look
    hint2: str = ""  # a stronger hint: an everyday example, just short of the answer
    explanation: str = ""
    # What has happened in this session:
    result: str | None = None  # None while open, then GREEN or AMBER
    last_status: str = "missing"  # the judge's latest word: covered, missing, wrong
    fresh_hint: str = ""  # the judge's newest hint, written for the learner's last words
    hints: list[str] = field(default_factory=list)  # the hints given so far (two allowed)

    @property
    def closed(self) -> bool:
        return self.result is not None


@dataclass
class TopicPlan:
    """Call A's answer: is the topic usable, and what are its key points."""

    status: str  # ok, confirm, too_broad, not_a_concept, need_level, unsure
    topic_clean: str = ""
    level: str = ""
    has_explanation: bool = False  # the learner already explained in their first words
    narrow_subject: str = ""
    nearby_topic: str = ""
    key_points: list[KeyPoint] = field(default_factory=list)


@dataclass
class Judgement:
    """Call B's answer for one learner turn."""

    statuses: dict[int, str]  # key point id -> covered, missing or wrong
    first_gap_id: int | None = None
    dont_know: bool = False
    off_topic: bool = False
    reply_lang: str = "hinglish"
    unclear_word: dict | None = None
    follow_up: str = ""
    # A hint and an explanation for the gap, in the language the learner is
    # speaking now. They replace the ones written when the session started.
    hint: str = ""
    explanation: str = ""


@dataclass
class Session:
    """One learner's conversation. Kept in memory only, then forgotten."""

    id: str
    voice: str = "male"  # the tutor's voice: male or female
    lang: str = "hinglish"  # hindi, hinglish, english, punjabi, telugu, kannada
    # topic -> level -> confirm -> explain -> follow_up -> summary
    phase: str = "topic"
    topic_text: str = ""  # what the learner said
    first_words: str = ""  # their first words in full, in case they already explained
    topic: str = ""  # tidied topic
    level: str = ""
    pending_topic: str = ""  # a topic waiting for the learner's yes
    points: list[KeyPoint] = field(default_factory=list)
    current_id: int | None = None  # the key point being asked about
    last_question: str = ""
    not_heard_count: int = 0
    history: list[tuple[str, str]] = field(default_factory=list)  # (who, text)

    def point(self, point_id: int | None) -> KeyPoint | None:
        return next((p for p in self.points if p.id == point_id), None)

    def progress(self) -> dict:
        return {
            "done": sum(1 for p in self.points if p.closed),
            "total": len(self.points),
        }

    def summary(self) -> dict:
        return {
            "points": [
                {"statement": p.statement, "result": p.result or AMBER}
                for p in self.points
            ]
        }


class Judge(Protocol):
    """Anything that can make key points and judge a turn.

    The real one calls the language model. Tests use a fake one, so they run
    with no keys.
    """

    def make_key_points(self, topic: str, level: str, confirmed: bool) -> TopicPlan: ...

    def judge_turn(self, session: Session, transcript: str) -> Judgement: ...

    def write_support(self, session: Session, point: KeyPoint) -> None:
        """Fills the point's question, hints and explanation in session.lang."""
        ...
