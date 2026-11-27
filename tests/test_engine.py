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
        KeyPoint(1, "The moon reflects sunlight.", question="Q1?", hint="H1.",
                 hint2="H1 stronger.", explanation="E1."),
        KeyPoint(2, "Half the moon is always lit.", question="Q2?", hint="H2.",
                 hint2="H2 stronger.", explanation="E2."),
        KeyPoint(3, "The moon orbits the Earth.", question="Q3?", hint="H3.",
                 hint2="H3 stronger.", explanation="E3."),
    ]


class FakeJudge:
    """Gives back the answers a test has lined up, in order."""

    def __init__(self, plans=None, turns=None):
        self.plans = list(plans or [TopicPlan("ok", "Moon phases", "Class 8", key_points=moon_points())])
        self.turns = list(turns or [])
        self.plan_calls = []

    def make_key_points(self, topic, level, confirmed):
        self.plan_calls.append((topic, level, confirmed))
        return self.plans.pop(0)

    def write_support(self, session, point):
        self.support_calls = getattr(self, "support_calls", 0) + 1

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
        self.assertIn("कोशिश", reply["text"])  # the nudge to try
        reply = tutor.turn(session, "it goes around the earth")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, GREEN, AMBER])
        self.assertNotIn("शाबाश", reply["text"])

    def test_two_hints_then_the_app_explains(self):
        tutor, session = started([
            verdict(covered=(1,), gap=2, follow_up="Q2 from judge?"),
            verdict(covered=(1,), gap=2),
            verdict(covered=(1,), gap=2),
            verdict(covered=(1,), gap=2),
            verdict(covered=(1, 3)),
        ])
        tutor.turn(session, LONG)
        first = tutor.turn(session, "not sure really")
        self.assertEqual(first["action"], "hint")
        self.assertIn("H2.", first["text"])  # the gentle hint
        second = tutor.turn(session, "still a guess")
        self.assertEqual(second["action"], "hint")
        self.assertIn("H2 stronger.", second["text"])  # the stronger hint
        self.assertIn("हार मत मानो", second["text"])  # do not give up yet
        self.assertIsNone(session.point(2).result)  # still open
        third = tutor.turn(session, "another guess")
        self.assertEqual(third["action"], "app_explains")
        self.assertIn("E2.", third["text"])
        self.assertIn("Q3?", third["text"])  # moves on to the next gap
        self.assertEqual(session.point(2).result, AMBER)
        reply = tutor.turn(session, "it orbits the earth")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, AMBER, GREEN])

    def test_app_explanation_is_never_counted_as_learner_knowledge(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3),
            verdict(covered=(1, 2), gap=3),
            verdict(covered=(1, 2), gap=3),
        ])
        tutor.turn(session, LONG)
        tutor.turn(session, "guess one")
        tutor.turn(session, "guess two")
        reply = tutor.turn(session, "guess three")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(session.point(3).result, AMBER)


class GivingUp(unittest.TestCase):
    """The learner may give up, but is nudged to try twice first."""

    def test_pata_nahi_gets_a_nudge_and_a_hint_not_the_answer(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3, dont_know=True),
        ])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "pata nahi")
        self.assertEqual(reply["action"], "hint")
        self.assertNotIn("E3.", reply["text"])
        self.assertIsNone(session.point(3).result)

    def test_pata_nahi_three_times_makes_the_app_explain(self):
        tutor, session = started([
            verdict(covered=(1, 2), gap=3, follow_up="Q?"),
            verdict(covered=(1, 2), gap=3, dont_know=True),
            verdict(covered=(1, 2), gap=3, dont_know=True),
            verdict(covered=(1, 2), gap=3, dont_know=True),
        ])
        tutor.turn(session, LONG)
        self.assertEqual(tutor.turn(session, "pata nahi")["action"], "hint")
        second = tutor.turn(session, "pata nahi")
        self.assertEqual(second["action"], "hint")
        self.assertIn("हार मत मानो", second["text"])
        reply = tutor.turn(session, "pata nahi")
        self.assertEqual(reply["action"], "done")
        self.assertIn("E3.", reply["text"])
        self.assertIn("अच्छी कोशिश", reply["text"])
        self.assertEqual(session.point(3).result, AMBER)

    def test_give_up_button_works_like_pata_nahi_without_the_judge(self):
        tutor, session = started([verdict(covered=(1, 2), gap=3, follow_up="Q?")])
        tutor.turn(session, LONG)
        first = tutor.turn(session, "", silent=True)
        self.assertEqual(first["action"], "hint")
        self.assertIn("H3.", first["text"])
        second = tutor.turn(session, "", silent=True)
        self.assertEqual(second["action"], "hint")
        self.assertIn("H3 stronger.", second["text"])
        third = tutor.turn(session, "", silent=True)
        self.assertEqual(third["action"], "done")
        self.assertEqual(session.point(3).result, AMBER)

    def test_the_same_hint_is_never_given_twice(self):
        again = verdict(covered=(1, 2), gap=3)
        again.hint = "H3."  # the judge repeats the hint already given
        tutor, session = started([verdict(covered=(1, 2), gap=3, follow_up="Q?"), again])
        tutor.turn(session, LONG)
        tutor.turn(session, "", silent=True)  # gives "H3."
        reply = tutor.turn(session, "a guess")
        self.assertIn("H3 stronger.", reply["text"])
        self.assertEqual(session.point(3).hints, ["H3.", "H3 stronger."])


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


class HintLanguage(unittest.TestCase):
    def test_help_text_is_written_once_per_point_and_language(self):
        tutor, session = started([verdict(covered=(1, 2), gap=3, follow_up="Q?")])
        tutor.turn(session, LONG)
        tutor.turn(session, "", silent=True)
        tutor.turn(session, "", silent=True)
        self.assertEqual(tutor.judge.support_calls, 1)
        self.assertEqual(session.point(3).support_lang, session.lang)

    def test_hint_from_the_latest_turn_replaces_the_starting_one(self):
        first = verdict(covered=(1, 2), gap=3, follow_up="Q?")
        first.hint, first.explanation = "नया hint.", "नई explanation."
        tutor, session = started([first, verdict(covered=(1, 2), gap=3, dont_know=True)])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "pata nahi")
        self.assertIn("नया hint.", reply["text"])
        self.assertNotIn("H3.", reply["text"])


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
        self.assertEqual(session.point(3).hints, [])


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
        self.assertIn("explain it in your own words", reply["text"])

    def test_explanation_given_with_the_topic_is_judged_at_once(self):
        plan = TopicPlan("ok", "Moon", "Class 8", has_explanation=True, key_points=moon_points())
        judge = FakeJudge(plans=[plan], turns=[verdict(covered=(1, 2), gap=3, follow_up="Q?")])
        tutor, session = Tutor(judge), new_session()
        reply = tutor.start(session, "Moon phases: " + LONG, "Class 8")
        # No "now explain it" turn: the first reply is already the question.
        self.assertEqual(reply["action"], "follow_up")
        self.assertEqual(reply["text"], "Q?")
        self.assertEqual(reply["progress"], {"done": 2, "total": 3})

    def test_class_from_the_home_screen_is_passed_on(self):
        judge = FakeJudge()
        Tutor(judge).start(new_session(), "Why the moon has phases", "Class 9")
        self.assertEqual(judge.plan_calls[-1][1], "Class 9")


if __name__ == "__main__":
    unittest.main()
