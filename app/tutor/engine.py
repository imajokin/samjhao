"""The tutor engine: the rules of the conversation (HANDOVER.md 6.2).

The language model judges what the learner said and writes each reply in
natural, spoken words. This file decides which kind of reply is allowed
next: ask, first hint, stronger hint, explain, or finish. The model is told
the same rules, and its reply is used only if it made the same move this
file worked out. Otherwise ready phrases are used. That keeps the counting
honest and makes loops impossible:

- each key point gets two hints, the second one stronger than the first;
- "I don't know", silence, the give-up button and a missed answer all count
  the same: the learner is nudged to try once more and gets the next hint;
- only after both hints does the app explain the point and move on, so the
  learner can always give up, but never at the first difficulty;
- a point is green only if the learner explained it without a hint.
"""

import uuid

from app.tutor.language import (
    guess_language,
    is_no,
    is_yes,
    language_from_code,
    quote_is_from,
    word_count,
)
from app.tutor.models import AMBER, GREEN, Judge, Judgement, KeyPoint, Session
from app.tutor.strings import say

MIN_FIRST_EXPLANATION_WORDS = 5
MAX_HINTS = 2  # hints per key point before the app explains it
HISTORY_FOR_START = 8  # earlier lines shown to the model while the topic is settled
MAX_WORD_CHECKS = 2  # times per session we may ask "did you say X or Y?"
MAX_CLARIFIES = 2  # times per point the learner may ask us something for free
GAVE_UP = "(the learner tapped the button: I don't know)"
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
        """The learner has said something to begin: a topic, a topic with its
        explanation, or just a few words."""
        if language_code:
            session.lang = language_from_code(language_code, topic_text)
        else:
            session.lang = guess_language(topic_text)
        session.topic_text = (topic_text or "").strip()
        session.level = (level or session.level or "").strip()
        if not session.topic_text:
            session.phase = "topic"
            return self._reply(session, "retry_audio", _say(session, "not_heard"))
        # Everything said before the topic is settled counts toward the first
        # explanation, in case they started explaining straight away.
        session.first_words = _join(session.first_words, session.topic_text)
        return self._plan(session, confirmed=False)

    def _plan(self, session: Session, confirmed: bool) -> dict:
        """Asks the model what the learner wants to explain, and for the key
        points once that is clear. The model also writes what to say next;
        the fixed phrases are only the backup."""
        earlier = "\n".join(f"{who}: {text}" for who, text in session.history[-HISTORY_FOR_START:])
        session.history.append(("learner", session.topic_text))
        plan = self.judge.make_key_points(session.topic_text, session.level, confirmed, earlier)
        if plan.reply_lang:
            session.lang = plan.reply_lang
        if plan.level and not session.level:
            session.level = plan.level
        topic = plan.topic_clean or session.topic_text

        if plan.status == "confirm":
            session.phase, session.pending_topic = "confirm", topic
            text = plan.reply or _say(session, "confirm_topic", topic=topic)
            return self._reply(session, "confirm_topic", text)
        if plan.status == "too_broad":
            session.phase = "topic"
            subject = plan.narrow_subject or topic
            text = plan.reply or _say(session, "narrow_topic", subject=subject)
            return self._reply(session, "narrow_topic", text)
        if plan.status == "not_a_concept":
            session.phase = "topic"
            return self._reply(session, "narrow_topic", plan.reply or _say(session, "home_open"))
        if plan.status == "need_level":
            session.phase, session.topic_text = "level", topic
            return self._reply(session, "ask_level", plan.reply or _say(session, "ask_level"))
        if plan.status == "unsure" or not plan.key_points:
            # Never guess the key points.
            if plan.nearby_topic:
                session.phase, session.pending_topic = "confirm", plan.nearby_topic
                text = plan.reply or _say(session, "unsure_topic", nearby=plan.nearby_topic)
                return self._reply(session, "unsure_topic", text)
            session.phase = "topic"
            return self._reply(session, "narrow_topic", plan.reply or _say(session, "home_open"))

        session.topic = topic
        session.points = plan.key_points
        session.phase = "explain"
        session.current_id = None
        session.not_heard_count = 0
        session.last_question = plan.reply or _say(session, "start_explain")

        # If the learner already explained while naming the topic, judge that
        # straight away. Asking them to explain again would waste a turn.
        words, session.first_words = session.first_words, ""
        if plan.has_explanation and word_count(words) >= MIN_FIRST_EXPLANATION_WORDS:
            session.history.pop()  # turn() records these words itself
            return self.turn(session, words)
        return self._reply(session, "start_explain", session.last_question)

    # ----- every later turn -----

    def turn(
        self,
        session: Session,
        transcript: str,
        heard_ok: bool = True,
        silent: bool = False,
    ) -> dict:
        """The learner has spoken, or tapped "I don't know"."""
        transcript = (transcript or "").strip()

        if session.phase == "summary":
            return self._finish(session, "")
        if session.phase in ("topic", "level", "confirm"):
            return self._setup_turn(session, transcript)

        gave_up = silent and session.phase == "follow_up"
        if transcript and session.held_words and not gave_up:
            # They have just told us which word they meant. Judge the answer
            # that was waiting, together with that.
            transcript = f"{session.held_words}\n(Asked which word they meant, the learner said: {transcript})"
            session.held_words = ""
        if gave_up:
            transcript = GAVE_UP
        else:
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
        asked = session.point(session.current_id)

        if judgement.off_topic and not gave_up:
            written = judgement.reply if judgement.move == "off_topic" else ""
            text = written or _join(_say(session, "off_topic"), session.last_question)
            return self._reply(session, "off_topic", text, judgement)

        # The verdict hangs on one word that may have been misheard. Ask about
        # that word first, judge nothing yet, and use up no hint.
        unclear = judgement.unclear_word or {}
        heard, likely = str(unclear.get("heard", "")).strip(), str(unclear.get("likely", "")).strip()
        if heard and likely and heard != likely and not gave_up and session.word_checks < MAX_WORD_CHECKS:
            session.word_checks += 1
            session.held_words = session.history.pop()[1]  # judged on the next turn
            text = _say(session, "confirm_word", a=heard, b=likely)
            return self._reply(session, "confirm_word", text, judgement)

        self._record(session, judgement)

        # The learner asked us something instead of answering. Answer it; no
        # hint is used up. Allowed a couple of times per point.
        if (
            judgement.learner_asked
            and not gave_up
            and asked is not None
            and not asked.closed
            and asked.clarifies < MAX_CLARIFIES
        ):
            asked.clarifies += 1
            written = judgement.reply if judgement.move == "clarify" else ""
            text = written or _join(_say(session, "say_more"), session.last_question)
            return self._reply(session, "follow_up", text, judgement)

        # ----- which move do the rules allow? -----
        if session.phase == "explain" or asked is None or asked.closed:
            first = session.phase == "explain"
            session.phase = "follow_up"
            gap = self._pick_gap(session)
            move = "ask" if gap else "done"
            lead = "" if first else _say(session, "correct")
            if not gap:
                return self._finish(session, lead, self._written(judgement, move, None), judgement)
            return self._ask(session, gap, lead, self._written(judgement, move, gap), judgement)

        if len(asked.hints) < MAX_HINTS:
            move = "hint1" if not asked.hints else "hint2"
            return self._hint(session, asked, self._written(judgement, move, asked), judgement)

        # Both hints are used: explain this point and move on.
        if not asked.explanation:
            self._support(session, asked)
        asked.result = AMBER
        asked.last_status = "explained by the tutor"
        gap = self._pick_gap(session)
        written = self._written(judgement, "explain", gap)
        lead = _join(_say(session, "explain_lead"), judgement.explanation or asked.explanation)
        if not gap:
            return self._finish(session, lead, written, judgement)
        reply = self._ask(session, gap, lead, written, judgement)
        reply["action"] = "app_explains"
        return reply

    def _setup_turn(self, session: Session, transcript: str) -> dict:
        """Turns before the explanation starts: the learner is still telling
        us what they want to explain, or answering a question about it."""
        if not transcript:
            return self._reply(session, "retry_audio", _say(session, "not_heard"))
        if session.phase == "level":
            session.level = transcript
            return self._plan(session, confirmed=False)
        if session.phase == "confirm" and is_yes(transcript):
            session.topic_text = session.pending_topic
            return self._plan(session, confirmed=True)
        # Anything else is simply the next thing they said. The model reads it
        # together with the conversation so far.
        return self.start(session, transcript, session.level)

    # ----- the counting rules -----

    def _record(self, session: Session, judgement: Judgement) -> None:
        """Writes the judge's verdicts onto the key points."""
        spoken = [text for who, text in session.history if who == "learner"]
        for point in session.points:
            status = judgement.statuses.get(point.id)
            if status is None:
                continue
            # A point is credited only if the words quoted for it can be found
            # in what the learner actually said. Otherwise it stays open.
            if (
                status == "covered"
                and not point.closed
                and judgement.evidence is not None
                and not quote_is_from(judgement.evidence.get(point.id, ""), spoken)
            ):
                status = "missing"
                judgement.statuses[point.id] = "missing"
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

    def _written(self, judgement: Judgement, move: str, about: KeyPoint | None) -> str:
        """The model's own reply, but only if it made the move the rules allow
        and is talking about the right point. Otherwise an empty string."""
        same_point = judgement.about_id == (about.id if about else None)
        if judgement.move == move and same_point:
            return judgement.reply
        return ""

    def _ask(
        self, session: Session, gap: KeyPoint, lead: str, written: str, judgement: Judgement
    ) -> dict:
        """Asks about the next open point."""
        session.current_id = gap.id
        if written:
            session.last_question = judgement.question or written
            return self._reply(session, "follow_up", written, judgement)
        self._support(session, gap)
        session.last_question = gap.question or _say(session, "say_more")
        return self._reply(session, "follow_up", _join(lead, session.last_question), judgement)

    def _hint(
        self, session: Session, point: KeyPoint, written: str, judgement: Judgement
    ) -> dict:
        """A nudge to try once more, with the next hint. The learner may give
        up, but only after both hints does the app explain."""
        first = not point.hints
        if written and judgement.hint and judgement.hint not in point.hints:
            point.hints.append(judgement.hint)
            session.last_question = judgement.question or session.last_question
            return self._reply(session, "hint", written, judgement)
        # Ready phrases, if the model's reply cannot be used.
        self._support(session, point)
        hint = next(
            (h for h in ([point.hint, point.hint2] if first else [point.hint2, point.hint])
             if h and h not in point.hints),
            "",
        )
        point.hints.append(hint or "-")
        nudge = _say(session, "nudge_first" if first else "nudge_again")
        text = _join(nudge, hint, session.last_question)
        return self._reply(session, "hint", text, judgement)

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

    def _finish(
        self, session: Session, lead: str, written: str = "", judgement: Judgement | None = None
    ) -> dict:
        session.phase = "summary"
        session.current_id = None
        all_green = all(p.result == GREEN for p in session.points)
        closing = _say(session, "done" if all_green else "done_with_help")
        reply = self._reply(session, "done", written or _join(lead, closing), judgement)
        reply["summary"] = session.summary()
        return reply

    def _reply(
        self, session: Session, action: str, text: str, judgement: Judgement | None = None
    ) -> dict:
        session.history.append(("tutor", text))
        # Notes for the developer's viewer. Kept in memory only, like the session.
        session.notes.append({
            "action": action,
            "text": text,
            "model_move": judgement.move if judgement else "",
            "used_model_reply": bool(judgement and judgement.reply and text == judgement.reply),
            "meaning": judgement.meaning if judgement else "",
            "statuses": dict(judgement.statuses) if judgement else {},
        })
        return {
            "action": action,
            "text": text,
            "lang": session.lang,
            "progress": session.progress(),
        }


def _join(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())
