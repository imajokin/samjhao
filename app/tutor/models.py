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
    question: str = ""  # a ready question that leads toward the idea
    hint: str = ""
    explanation: str = ""
    # What has happened in this session:
    result: str | None = None  # None while open, then GREEN or AMBER
    last_status: str = "missing"  # the judge's latest word: covered, missing, wrong
    tries: int = 0  # real tries used on the follow-up question (two allowed)
    hint_given: bool = False

    @property
    def closed(self) -> bool:
        return self.result is not None


@dataclass
class TopicPlan:
    """Call A's answer: is the topic usable, and what are its key points."""

    status: str  # ok, confirm, too_broad, not_a_concept, need_level, unsure
    topic_clean: str = ""
    level: str = ""
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


@dataclass
class Session:
    """One learner's conversation. Kept in memory only, then forgotten."""

    id: str
    lang: str = "hinglish"
    # topic -> level -> confirm -> explain -> follow_up -> summary
    phase: str = "topic"
    topic_text: str = ""  # what the learner said
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

    def make_key_points(
        self, topic: str, level: str, language: str, confirmed: bool
    ) -> TopicPlan: ...

    def judge_turn(self, session: Session, transcript: str) -> Judgement: ...
