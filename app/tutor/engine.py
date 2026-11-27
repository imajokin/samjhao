"""The tutor engine: the rules of the conversation (HANDOVER.md 6.2).

The language model only judges what the learner said and words the question.
This file decides what happens next: ask, hint, explain, move on or finish.
That keeps the counting honest and makes loops impossible:

- each key point gets two hints, the second one stronger than the first;
- "I don't know", silence, the give-up button and a missed answer all count
  the same: the learner is nudged to try once more and gets the next hint;
- only after both hints does the app explain the point and move on, so the
  learner can always give up, but never at the first difficulty;
- a point is green only if the learner explained it without a hint.
"""

import uuid

from app.tutor.language import guess_language, is_no, is_yes, language_from_code, word_count
from app.tutor.models import AMBER, GREEN, Judge, Judgement, KeyPoint, Session
from app.tutor.strings import say

MIN_FIRST_EXPLANATION_WORDS = 5
MAX_HINTS = 2  # hints per key point before the app explains it
NOT_HEARD_BEFORE_TEXT_BOX = 2


def new_session(voice: str = "male") -> Session:
    return Session(id=uuid.uuid4().hex, voice="female" if voice == "female" else "male")


def _say(session: Session, key: str, **values: str) -> str:
    """A fixed phrase in this learner's language and the chosen voice."""
    return say(key, session.lang, session.voice, **values)


class Tutor:
    def __init__(self, judge: Judge):
        self.judge = judge

    # ----- starting: topic, level, confirmation -----

    def start(
        self, session: Session, topic_text: str, level: str = "", language_code: str = ""
    ) -> dict:
        """The learner has said a topic, and maybe a level."""
        if language_code:
            session.lang = language_from_code(language_code, topic_text)
        else:
            session.lang = guess_language(topic_text)
        session.topic_text = (topic_text or "").strip()
        session.level = (level or "").strip()
        if not session.topic_text:
            session.phase = "topic"
            return self._reply(session, "retry_audio", _say(session, "not_heard"))
        return self._plan(session, confirmed=False)

    def _plan(self, session: Session, confirmed: bool) -> dict:
        """Asks the judge for the key points and acts on its answer."""
        plan = self.judge.make_key_points(session.topic_text, session.level, confirmed)
        if plan.level and not session.level:
            session.level = plan.level
        topic = plan.topic_clean or session.topic_text

        if plan.status == "confirm":
            session.phase, session.pending_topic = "confirm", topic
            return self._reply(session, "confirm_topic", _say(session, "confirm_topic", topic=topic))
        if plan.status == "too_broad":
            session.phase = "topic"
            subject = plan.narrow_subject or topic
            return self._reply(session, "narrow_topic", _say(session, "narrow_topic", subject=subject))
        if plan.status == "not_a_concept":
            session.phase = "topic"
            return self._reply(session, "narrow_topic", _say(session, "home_open"))
        if plan.status == "need_level":
            session.phase, session.topic_text = "level", topic
            return self._reply(session, "ask_level", _say(session, "ask_level"))
        if plan.status == "unsure" or not plan.key_points:
            # Never guess the key points.
            if plan.nearby_topic:
                session.phase, session.pending_topic = "confirm", plan.nearby_topic
                return self._reply(
                    session, "unsure_topic", _say(session, "unsure_topic", nearby=plan.nearby_topic)
                )
            session.phase = "topic"
            return self._reply(session, "narrow_topic", _say(session, "home_open"))

        session.topic = topic
        session.points = plan.key_points
        session.phase = "explain"
        session.current_id = None
        session.not_heard_count = 0
        session.last_question = _say(session, "start_explain")
        return self._reply(session, "start_explain", session.last_question)

    # ----- every later turn -----

    def turn(
        self,
        session: Session,
        transcript: str,
        heard_ok: bool = True,
        silent: bool = False,
    ) -> dict:
        """The learner has spoken (or stayed silent after a question)."""
        transcript = (transcript or "").strip()

        if session.phase == "summary":
            return self._finish(session, "")
        if session.phase in ("topic", "level", "confirm"):
            return self._setup_turn(session, transcript)

        # Silence after a question, or the give-up button: "I do not know".
        if silent and session.phase == "follow_up":
            return self._stuck(session, session.point(session.current_id))

        too_short = (
            session.phase == "explain"
            and word_count(transcript) < MIN_FIRST_EXPLANATION_WORDS
        )
        if not heard_ok or not transcript or too_short:
            return self._not_heard(session)
        session.not_heard_count = 0

        session.history.append(("learner", transcript))
        judgement = self.judge.judge_turn(session, transcript)
        session.lang = judgement.reply_lang or session.lang

        if judgement.off_topic:
            text = _say(session, "off_topic") + " " + session.last_question
            return self._reply(session, "off_topic", text)

        asked = session.point(session.current_id)
        self._record(session, judgement)

        if session.phase == "explain":
            session.phase = "follow_up"
            return self._next_gap(session, judgement, lead="")

        if asked is None or asked.closed:
            # The point just asked about is now covered.
            return self._next_gap(session, judgement, lead=_say(session, "correct"))
        # Not covered: a miss and "I don't know" are treated the same way.
        return self._stuck(session, asked)

    def _setup_turn(self, session: Session, transcript: str) -> dict:
        """Turns before the explanation: a new topic, a level, or a yes/no."""
        if not transcript:
            return self._reply(session, "retry_audio", _say(session, "not_heard"))
        if session.phase == "level":
            session.level = transcript
            return self._plan(session, confirmed=False)
        if session.phase == "confirm":
            if is_yes(transcript):
                session.topic_text = session.pending_topic
                return self._plan(session, confirmed=True)
            if is_no(transcript):
                session.phase, session.level = "topic", ""
                return self._reply(session, "narrow_topic", _say(session, "home_open"))
            # Neither yes nor no: treat what they said as the topic itself.
        return self.start(session, transcript, session.level if session.phase == "confirm" else "")

    # ----- the counting rules -----

    def _record(self, session: Session, judgement: Judgement) -> None:
        """Writes the judge's verdicts onto the key points."""
        # The judge writes a fresh hint that answers what the learner just
        # said, in the language they are speaking now.
        gap = session.point(judgement.first_gap_id)
        if gap is not None and not gap.closed:
            gap.fresh_hint = judgement.hint or gap.fresh_hint
            gap.explanation = judgement.explanation or gap.explanation
        for point in session.points:
            status = judgement.statuses.get(point.id)
            if status is None:
                continue
            if point.closed:
                # A point the learner explained can reopen only if they now
                # contradict it. A point the app explained stays closed.
                learner_covered = point.last_status == "covered"
                if status == "wrong" and learner_covered and len(point.hints) < MAX_HINTS:
                    point.result = None
                    point.last_status = "wrong"
                continue
            point.last_status = status
            if status == "covered":
                # Green only when no hint was needed for this point.
                point.result = AMBER if point.hints else GREEN

    def _pick_gap(self, session: Session) -> KeyPoint | None:
        """A point the learner got wrong comes before one they skipped."""
        open_points = [p for p in session.points if not p.closed]
        wrong = [p for p in open_points if p.last_status == "wrong"]
        return (wrong or open_points or [None])[0]

    def _next_gap(self, session: Session, judgement: Judgement | None, lead: str) -> dict:
        """Moves to the next open point, or finishes."""
        gap = self._pick_gap(session)
        if gap is None:
            return self._finish(session, lead)
        session.current_id = gap.id
        # Use the judge's question when it is about the same point. Otherwise
        # use the ready question that was written with the key points.
        question = ""
        if judgement and judgement.first_gap_id == gap.id:
            question = judgement.follow_up.strip()
        if not question:
            self._support(session, gap)
        session.last_question = question or gap.question or _say(session, "say_more")
        return self._reply(session, "follow_up", _join(lead, session.last_question))

    def _stuck(self, session: Session, point: KeyPoint | None) -> dict:
        """The learner missed the point, said "I don't know", stayed silent or
        tapped the give-up button. Nudge them and give the next hint. Only
        when the hints are used up does the app explain."""
        if point is None:
            return self._next_gap(session, None, "")
        if len(point.hints) >= MAX_HINTS:
            return self._app_explains(session, point)
        if not point.fresh_hint:
            self._support(session, point)
        hint = _next_hint(point)
        if not hint:
            return self._app_explains(session, point)
        nudge = _say(session, "nudge_first" if not point.hints else "nudge_again")
        point.hints.append(hint)
        point.fresh_hint = ""
        text = _join(nudge, _say(session, "hint_prefix"), hint, session.last_question)
        return self._reply(session, "hint", text)

    def _app_explains(self, session: Session, point: KeyPoint) -> dict:
        """The app explains the point in two sentences and moves on.
        This is never counted as the learner's knowledge."""
        if not point.explanation:
            self._support(session, point)
        point.result = AMBER
        point.last_status = "explained by the tutor"
        lead = _join(_say(session, "explain_lead"), point.explanation)
        reply = self._next_gap(session, None, lead=lead)
        if reply["action"] == "follow_up":
            reply["action"] = "app_explains"
        return reply

    def _support(self, session: Session, point: KeyPoint) -> None:
        """Makes sure the point has a question, hints and an explanation in the
        language the learner is using now. Written once, when first needed."""
        if point.support_lang == session.lang:
            return
        self.judge.write_support(session, point)
        point.support_lang = session.lang

    def _not_heard(self, session: Session) -> dict:
        """Nothing usable was heard. Earlier progress is kept."""
        session.not_heard_count += 1
        text = _say(session, "not_heard")
        if session.not_heard_count >= NOT_HEARD_BEFORE_TEXT_BOX:
            return self._reply(session, "show_text_box", text)
        return self._reply(session, "retry_audio", text)

    def _finish(self, session: Session, lead: str) -> dict:
        session.phase = "summary"
        session.current_id = None
        all_green = all(p.result == GREEN for p in session.points)
        closing = _say(session, "done" if all_green else "done_with_help")
        reply = self._reply(session, "done", _join(lead, closing))
        reply["summary"] = session.summary()
        return reply

    def _reply(self, session: Session, action: str, text: str) -> dict:
        session.history.append(("tutor", text))
        return {
            "action": action,
            "text": text,
            "lang": session.lang,
            "progress": session.progress(),
        }


def _next_hint(point: KeyPoint) -> str:
    """The next hint for this point that has not been given yet. The judge's
    fresh hint comes first. The ready ones are the backup: the gentle one
    first, the stronger one second."""
    ready = [point.hint, point.hint2] if not point.hints else [point.hint2, point.hint]
    for hint in [point.fresh_hint, *ready]:
        if hint and hint not in point.hints:
            return hint
    return ""


def _join(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())
