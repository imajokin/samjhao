"""Tests for the rules of the conversation.

They use a fake judge with scripted answers, so they need no keys.
Run with:  python -m unittest discover -s tests -v
"""

import unittest

from app.tutor.engine import Tutor, new_session
from app.tutor.models import AMBER, GREEN, Judgement, KeyPoint, TopicPlan

LONG = "the moon goes around the earth and we see its lit half"


def moon_points() -> list[KeyPoint]:
    return [
        KeyPoint(1, "The moon reflects sunlight.", question="Q1?", hint="H1.", explanation="E1."),
        KeyPoint(2, "Half the moon is always lit.", question="Q2?", hint="H2.", explanation="E2."),
        KeyPoint(3, "The moon orbits the Earth.", question="Q3?", hint="H3.", explanation="E3."),
    ]


class FakeJudge:
    """Gives back the answers a test has lined up, in order."""

    def __init__(self, plans=None, turns=None):
        self.plans = list(plans or [TopicPlan("ok", "Moon phases", "Class 8", key_points=moon_points())])
        self.turns = list(turns or [])
        self.plan_calls = []

    def make_key_points(self, topic, level, language, confirmed):
        self.plan_calls.append((topic, level, confirmed))
        return self.plans.pop(0)

    def judge_turn(self, session, transcript):
        return self.turns.pop(0)


def verdict(covered=(), wrong=(), gap=None, follow_up="", **flags) -> Judgement:
    """A judgement over the three moon points."""
    statuses = {i: "missing" for i in (1, 2, 3)}
    statuses.update({i: "covered" for i in covered})
    statuses.update({i: "wrong" for i in wrong})
    return Judgement(statuses, first_gap_id=gap, follow_up=follow_up, **flags)


def started(turns):
    """A session that has reached the "explain" step."""
    tutor = Tutor(FakeJudge(turns=turns))
    session = new_session()
    reply = tutor.start(session, "Why the moon has phases, Class 8")
    assert reply["action"] == "start_explain"
    return tutor, session


def results(session):
    return [p.result for p in session.points]


class CoreFlow(unittest.TestCase):
    def test_all_points_covered_first_time(self):
        tutor, session = started([verdict(covered=(1, 2, 3))])
        reply = tutor.turn(session, LONG)
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, GREEN, GREEN])
        self.assertEqual(reply["progress"], {"done": 3, "total": 3})
        self.assertIn("शाबाश", reply["text"])
        self.assertEqual(len(reply["summary"]["points"]), 3)

    def test_one_miss_then_covered_is_green(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Where does the moon go?"),
            verdict(covered=(1, 2, 3)),
        ])
        reply = tutor.turn(session, LONG)
        self.assertEqual(reply["action"], "follow_up")
        self.assertEqual(reply["text"], "Where does the moon go?")
        self.assertEqual(reply["progress"], {"done": 2, "total": 3})
        reply = tutor.turn(session, "around the earth")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, GREEN, GREEN])

    def test_hint_then_covered_is_amber(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3, follow_up="Q again?"),
            verdict(covered=(1, 2, 3)),
        ])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "it just changes")
        self.assertEqual(reply["action"], "hint")
        self.assertIn("H3.", reply["text"])
        self.assertIn("Q?", reply["text"])
        reply = tutor.turn(session, "it goes around the earth")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, GREEN, AMBER])
        self.assertNotIn("शाबाश", reply["text"])

    def test_two_misses_then_app_explains(self):
        tutor, session = started([
            verdict(covered=(1,), gap=2, follow_up="Q2 from judge?"),
            verdict(covered=(1,), gap=2),
            verdict(covered=(1,), gap=2),
            verdict(covered=(1, 3)),
        ])
        tutor.turn(session, LONG)
        self.assertEqual(tutor.turn(session, "not sure really")["action"], "hint")
        reply = tutor.turn(session, "still a guess")
        self.assertEqual(reply["action"], "app_explains")
        self.assertIn("E2.", reply["text"])
        self.assertIn("Q3?", reply["text"])  # moves on to the next gap
        self.assertEqual(session.point(2).result, AMBER)
        reply = tutor.turn(session, "it orbits the earth")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, AMBER, GREEN])

    def test_app_explanation_is_never_counted_as_learner_knowledge(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3),
            verdict(covered=(1, 2), gap=3),
        ])
        tutor.turn(session, LONG)
        tutor.turn(session, "guess one")
        reply = tutor.turn(session, "guess two")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(session.point(3).result, AMBER)


class DontKnow(unittest.TestCase):
    def test_pata_nahi_gives_hint_and_uses_no_try(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3, dont_know=True),
        ])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "pata nahi")
        self.assertEqual(reply["action"], "hint")
        self.assertEqual(session.point(3).tries, 0)

    def test_pata_nahi_twice_makes_the_app_explain(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3, dont_know=True),
            verdict(covered=(1, 2), gap=3, dont_know=True),
        ])
        tutor.turn(session, LONG)
        tutor.turn(session, "pata nahi")
        reply = tutor.turn(session, "pata nahi")
        self.assertEqual(reply["action"], "done")
        self.assertIn("E3.", reply["text"])
        self.assertEqual(session.point(3).result, AMBER)

    def test_after_a_pata_nahi_hint_two_real_tries_remain(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3, dont_know=True),
            verdict(covered=(1, 2), gap=3),
            verdict(covered=(1, 2), gap=3),
        ])
        tutor.turn(session, LONG)
        self.assertEqual(tutor.turn(session, "pata nahi")["action"], "hint")
        reply = tutor.turn(session, "first real try")
        self.assertEqual(reply["action"], "follow_up")
        self.assertIn("थोड़ा और", reply["text"])
        self.assertEqual(tutor.turn(session, "second real try")["action"], "done")
        self.assertEqual(session.point(3).result, AMBER)

    def test_silence_after_a_question_gives_the_hint(self):
        tutor, session = started([verdict(covered=(1, 2), gap=3, follow_up="Q?")])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "", silent=True)
        self.assertEqual(reply["action"], "hint")
        self.assertEqual(session.point(3).tries, 0)


class GapOrder(unittest.TestCase):
    def test_a_wrong_point_is_asked_before_a_skipped_one(self):
        tutor, session = started([
            verdict(wrong=(3,), gap=3, follow_up="You said shadow. What makes it?"),
        ])
        reply = tutor.turn(session, LONG)
        self.assertEqual(session.current_id, 3)
        self.assertEqual(reply["text"], "You said shadow. What makes it?")

    def test_ready_question_is_used_when_the_judge_asked_about_another_point(self):
        tutor, session = started([
            verdict(wrong=(3,), gap=1, follow_up="Question about point one?"),
        ])
        reply = tutor.turn(session, LONG)
        self.assertEqual(session.current_id, 3)
        self.assertEqual(reply["text"], "Q3?")

    def test_other_points_covered_in_a_follow_up_answer_get_credit(self):
        tutor, session = started([
            verdict(gap=1, follow_up="Q?"),
            verdict(covered=(1, 2, 3)),
        ])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, LONG)
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, GREEN, GREEN])

    def test_progress_never_reveals_key_points(self):
        tutor, session = started([verdict(covered=(1,), gap=2, follow_up="Q?")])
        reply = tutor.turn(session, LONG)
        self.assertNotIn("summary", reply)
        self.assertNotIn("Half the moon", str(reply))


class HearingProblems(unittest.TestCase):
    def test_short_first_explanation_counts_as_not_heard(self):
        tutor, session = started([])
        reply = tutor.turn(session, "moon changes")
        self.assertEqual(reply["action"], "retry_audio")

    def test_two_failed_tries_show_the_text_box(self):
        tutor, session = started([])
        tutor.turn(session, "", heard_ok=False)
        self.assertEqual(tutor.turn(session, "")["action"], "show_text_box")

    def test_short_follow_up_answer_is_fine(self):
        tutor, session = started([
            verdict(covered=(2, 3), gap=1, follow_up="Q?"),
            verdict(covered=(1, 2, 3)),
        ])
        tutor.turn(session, LONG)
        self.assertEqual(tutor.turn(session, "sooraj se")["action"], "done")

    def test_off_topic_repeats_the_question_and_uses_no_try(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3, off_topic=True),
        ])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "what is for lunch today")
        self.assertEqual(reply["action"], "off_topic")
        self.assertIn("Q?", reply["text"])
        self.assertEqual(session.point(3).tries, 0)


class StartingATopic(unittest.TestCase):
    def run_start(self, plans, text="physics"):
        judge = FakeJudge(plans=plans)
        tutor, session = Tutor(judge), new_session()
        return tutor, session, judge, tutor.start(session, text)

    def test_too_broad_asks_to_narrow(self):
        _, _, _, reply = self.run_start([TopicPlan("too_broad", "Physics", narrow_subject="Physics")])
        self.assertEqual(reply["action"], "narrow_topic")
        self.assertIn("Physics", reply["text"])

    def test_no_level_asks_for_it_then_starts(self):
        ok = TopicPlan("ok", "Compound interest", "Class 8", key_points=moon_points())
        tutor, session, judge, reply = self.run_start(
            [TopicPlan("need_level", "Compound interest"), ok], "compound interest"
        )
        self.assertEqual(reply["action"], "ask_level")
        reply = tutor.turn(session, "class 8")
        self.assertEqual(reply["action"], "start_explain")
        self.assertEqual(judge.plan_calls[-1][1], "class 8")

    def test_unclear_topic_is_confirmed_before_starting(self):
        ok = TopicPlan("ok", "Photosynthesis", "Class 8", key_points=moon_points())
        tutor, session, judge, reply = self.run_start(
            [TopicPlan("confirm", "Photosynthesis"), ok], "foto sin thesis class 8"
        )
        self.assertEqual(reply["action"], "confirm_topic")
        reply = tutor.turn(session, "haan")
        self.assertEqual(reply["action"], "start_explain")
        self.assertEqual(judge.plan_calls[-1], ("Photosynthesis", "", True))

    def test_saying_no_to_the_confirmation_goes_back_to_the_topic(self):
        tutor, session, _, _ = self.run_start([TopicPlan("confirm", "Photosynthesis")])
        reply = tutor.turn(session, "nahi")
        self.assertEqual(reply["action"], "narrow_topic")
        self.assertEqual(session.phase, "topic")

    def test_unsure_topic_offers_a_nearby_one_and_never_guesses(self):
        _, session, _, reply = self.run_start(
            [TopicPlan("unsure", "Some rare thing", nearby_topic="Ohm's law")]
        )
        self.assertEqual(reply["action"], "unsure_topic")
        self.assertIn("Ohm's law", reply["text"])
        self.assertEqual(session.points, [])

    def test_english_topic_gets_english_phrases(self):
        _, _, _, reply = self.run_start(
            [TopicPlan("ok", "Moon", "Class 8", key_points=moon_points())],
            "Why the moon has phases, Class 8",
        )
        self.assertIn("younger brother", reply["text"])


if __name__ == "__main__":
    unittest.main()
