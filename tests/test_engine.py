"""Tests for the rules of the conversation.

They use a fake judge with scripted answers, so they need no keys.
Run with:  python -m unittest discover -s tests -v
"""

import unittest

from app.tutor.engine import GAVE_UP, Tutor, new_session
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
        self.heard = []
        self.support_calls = 0

    def make_key_points(self, topic, level, confirmed):
        self.plan_calls.append((topic, level, confirmed))
        return self.plans.pop(0)

    def write_support(self, session, point):
        self.support_calls += 1

    def judge_turn(self, session, transcript):
        self.heard.append(transcript)
        return self.turns.pop(0)


def verdict(covered=(), wrong=(), move="", about=None, reply="", **extra) -> Judgement:
    """A judgement over the three moon points, with the model's own reply."""
    statuses = {i: "missing" for i in (1, 2, 3)}
    statuses.update({i: "covered" for i in covered})
    statuses.update({i: "wrong" for i in wrong})
    return Judgement(statuses, move=move, about_id=about, reply=reply, **extra)


def ask(covered, about, reply="Model question?"):
    return verdict(covered=covered, move="ask", about=about, reply=reply, question=reply)


def hint(covered, about, number, text):
    return verdict(covered=covered, move=f"hint{number}", about=about,
                   reply=f"Model says: {text}", hint=text)


def started(turns):
    """A session that has reached the "explain" step."""
    tutor = Tutor(FakeJudge(turns=turns))
    session = new_session()
    reply = tutor.start(session, "Why the moon has phases", "Class 8")
    assert reply["action"] == "start_explain"
    return tutor, session


def results(session):
    return [p.result for p in session.points]


class CoreFlow(unittest.TestCase):
    def test_all_points_covered_first_time(self):
        tutor, session = started([verdict(covered=(1, 2, 3), move="done", reply="Lovely, all clear.")])
        reply = tutor.turn(session, LONG)
        self.assertEqual(reply["action"], "done")
        self.assertEqual(reply["text"], "Lovely, all clear.")
        self.assertEqual(results(session), [GREEN, GREEN, GREEN])
        self.assertEqual(reply["progress"], {"done": 3, "total": 3})
        self.assertEqual(len(reply["summary"]["points"]), 3)

    def test_the_models_own_reply_is_spoken_when_it_follows_the_rules(self):
        tutor, session = started([ask((1, 2), 3, "Nice. And where does the moon travel?")])
        reply = tutor.turn(session, LONG)
        self.assertEqual(reply["action"], "follow_up")
        self.assertEqual(reply["text"], "Nice. And where does the moon travel?")
        self.assertEqual(session.current_id, 3)

    def test_one_miss_then_covered_is_green(self):
        tutor, session = started([ask((1, 2), 3), verdict(covered=(1, 2, 3), move="done", reply="Done!")])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "around the earth")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, GREEN, GREEN])

    def test_hint_then_covered_is_amber(self):
        tutor, session = started([
            ask((1, 2), 3),
            hint((1, 2), 3, 1, "Think about its path."),
            verdict(covered=(1, 2, 3), move="done", reply="There you go."),
        ])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "it just changes")
        self.assertEqual(reply["action"], "hint")
        self.assertEqual(reply["text"], "Model says: Think about its path.")
        reply = tutor.turn(session, "it goes around the earth")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, GREEN, AMBER])

    def test_two_hints_then_the_explanation(self):
        tutor, session = started([
            ask((1,), 2),
            hint((1,), 2, 1, "first hint"),
            hint((1,), 2, 2, "stronger hint"),
            verdict(covered=(1,), move="explain", about=3,
                    reply="Good try. Here is the idea. Now, where does it travel?",
                    explanation="Here is the idea.", question="Now, where does it travel?"),
            verdict(covered=(1, 3), move="done", reply="Well done."),
        ])
        tutor.turn(session, LONG)
        self.assertEqual(tutor.turn(session, "not sure")["action"], "hint")
        self.assertEqual(tutor.turn(session, "a guess")["action"], "hint")
        self.assertIsNone(session.point(2).result)  # still open after two hints
        third = tutor.turn(session, "another guess")
        self.assertEqual(third["action"], "app_explains")
        self.assertIn("Here is the idea.", third["text"])
        self.assertEqual(session.point(2).result, AMBER)
        self.assertEqual(session.current_id, 3)
        reply = tutor.turn(session, "it orbits the earth")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, AMBER, GREEN])

    def test_a_point_covered_after_hints_is_amber_never_green(self):
        tutor, session = started([
            ask((1, 2), 3),
            hint((1, 2), 3, 1, "one"),
            hint((1, 2), 3, 2, "two"),
            verdict(covered=(1, 2, 3), move="done", reply="Yes, it orbits."),
        ])
        tutor.turn(session, LONG)
        tutor.turn(session, "guess one")
        tutor.turn(session, "guess two")
        reply = tutor.turn(session, "oh so it orbits")
        self.assertEqual(reply["action"], "done")
        self.assertEqual(session.point(3).result, AMBER)


class TheRulesWin(unittest.TestCase):
    """The model writes the words, but it cannot change the move."""

    def test_model_cannot_explain_before_both_hints(self):
        early = verdict(covered=(1, 2), move="explain", about=None,
                        reply="The answer is: it orbits the Earth.")
        tutor, session = started([ask((1, 2), 3), early])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "pata nahi")
        self.assertEqual(reply["action"], "hint")
        self.assertNotIn("orbits the Earth", reply["text"])
        self.assertIn("H3.", reply["text"])  # the ready hint is used instead
        self.assertIsNone(session.point(3).result)

    def test_model_cannot_ask_about_the_wrong_point(self):
        tutor, session = started([verdict(wrong=(3,), move="ask", about=1, reply="About point one?")])
        reply = tutor.turn(session, LONG)
        self.assertEqual(session.current_id, 3)  # a wrong point comes first
        self.assertEqual(reply["text"], "Q3?")

    def test_model_cannot_finish_while_a_point_is_open(self):
        tutor, session = started([verdict(covered=(1, 2), move="done", reply="All done!")])
        reply = tutor.turn(session, LONG)
        self.assertEqual(reply["action"], "follow_up")
        self.assertNotEqual(reply["text"], "All done!")

    def test_the_same_hint_is_never_given_twice(self):
        tutor, session = started([
            ask((1, 2), 3),
            hint((1, 2), 3, 1, "same hint"),
            hint((1, 2), 3, 2, "same hint"),
        ])
        tutor.turn(session, LONG)
        tutor.turn(session, "guess")
        reply = tutor.turn(session, "guess again")
        self.assertEqual(reply["action"], "hint")
        self.assertEqual(session.point(3).hints, ["same hint", "H3 stronger."])


class GivingUp(unittest.TestCase):
    """The learner may give up, but is nudged to try twice first."""

    def test_pata_nahi_gets_a_hint_not_the_answer(self):
        tutor, session = started([ask((1, 2), 3), hint((1, 2), 3, 1, "small pointer")])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "pata nahi")
        self.assertEqual(reply["action"], "hint")
        self.assertIsNone(session.point(3).result)

    def test_give_up_button_goes_to_the_judge_and_takes_three_taps(self):
        tutor, session = started([
            ask((1, 2), 3),
            hint((1, 2), 3, 1, "one"),
            hint((1, 2), 3, 2, "two"),
            verdict(covered=(1, 2), move="explain", reply="Good effort. It orbits the Earth."),
        ])
        tutor.turn(session, LONG)
        self.assertEqual(tutor.turn(session, "", silent=True)["action"], "hint")
        self.assertEqual(tutor.judge.heard[-1], GAVE_UP)
        self.assertEqual(tutor.turn(session, "", silent=True)["action"], "hint")
        third = tutor.turn(session, "", silent=True)
        self.assertEqual(third["action"], "done")
        self.assertEqual(third["text"], "Good effort. It orbits the Earth.")
        self.assertEqual(session.point(3).result, AMBER)

    def test_ready_phrases_nudge_when_the_model_reply_cannot_be_used(self):
        blank = verdict(covered=(1, 2))  # the model gave no usable move
        tutor, session = started([ask((1, 2), 3), blank, blank, blank])
        tutor.turn(session, LONG)
        first = tutor.turn(session, "", silent=True)
        self.assertIn("H3.", first["text"])
        self.assertIn("कोशिश", first["text"])
        second = tutor.turn(session, "", silent=True)
        self.assertIn("H3 stronger.", second["text"])
        self.assertIn("हार मत मानो", second["text"])
        third = tutor.turn(session, "", silent=True)
        self.assertEqual(third["action"], "done")
        self.assertIn("E3.", third["text"])

    def test_asking_the_tutor_something_uses_no_hint(self):
        question = verdict(covered=(1, 2), move="clarify", about=3, learner_asked=True,
                           reply="I mean its journey in space. Where does it go?")
        tutor, session = started([ask((1, 2), 3), question])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "what do you mean by travel?")
        self.assertEqual(reply["action"], "follow_up")
        self.assertEqual(reply["text"], "I mean its journey in space. Where does it go?")
        self.assertEqual(session.point(3).hints, [])

    def test_asking_again_and_again_does_not_loop_forever(self):
        question = verdict(covered=(1, 2), move="clarify", about=3, learner_asked=True, reply="R?")
        tutor, session = started([ask((1, 2), 3), question, question, question])
        tutor.turn(session, LONG)
        tutor.turn(session, "what?")
        tutor.turn(session, "what?")
        third = tutor.turn(session, "what?")
        self.assertEqual(third["action"], "hint")  # after two free questions, hints start


class GapOrder(unittest.TestCase):
    def test_a_wrong_point_is_asked_before_a_skipped_one(self):
        tutor, session = started([
            verdict(wrong=(3,), move="ask", about=3, reply="Shadow? Tell me more."),
        ])
        reply = tutor.turn(session, LONG)
        self.assertEqual(session.current_id, 3)
        self.assertEqual(reply["text"], "Shadow? Tell me more.")

    def test_other_points_covered_in_a_follow_up_answer_get_credit(self):
        tutor, session = started([ask((), 1), verdict(covered=(1, 2, 3), move="done", reply="Yes!")])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, LONG)
        self.assertEqual(reply["action"], "done")
        self.assertEqual(results(session), [GREEN, GREEN, GREEN])

    def test_progress_never_reveals_key_points(self):
        tutor, session = started([ask((1,), 2)])
        reply = tutor.turn(session, LONG)
        self.assertNotIn("summary", reply)
        self.assertNotIn("Half the moon", str(reply))


class HelpText(unittest.TestCase):
    def test_help_text_is_written_once_per_point_and_language(self):
        blank = verdict(covered=(1, 2))
        tutor, session = started([ask((1, 2), 3), blank, blank])
        tutor.turn(session, LONG)
        tutor.turn(session, "", silent=True)
        tutor.turn(session, "", silent=True)
        self.assertEqual(tutor.judge.support_calls, 1)
        self.assertEqual(session.point(3).support_lang, session.lang)

    def test_no_help_text_is_fetched_when_the_model_reply_is_used(self):
        tutor, session = started([ask((1, 2), 3), hint((1, 2), 3, 1, "pointer")])
        tutor.turn(session, LONG)
        tutor.turn(session, "guess")
        self.assertEqual(tutor.judge.support_calls, 0)


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
        tutor, session = started([ask((2, 3), 1), verdict(covered=(1, 2, 3), move="done", reply="Yes.")])
        tutor.turn(session, LONG)
        self.assertEqual(tutor.turn(session, "sooraj se")["action"], "done")

    def test_off_topic_uses_no_hint(self):
        away = verdict(covered=(1, 2), off_topic=True, move="off_topic", about=3,
                       reply="Ha, lunch later. Back to the moon: where does it go?")
        tutor, session = started([ask((1, 2), 3), away])
        tutor.turn(session, LONG)
        reply = tutor.turn(session, "what is for lunch today")
        self.assertEqual(reply["action"], "off_topic")
        self.assertIn("Back to the moon", reply["text"])
        self.assertEqual(session.point(3).hints, [])


class StartingATopic(unittest.TestCase):
    def run_start(self, plans, text="physics", level=""):
        judge = FakeJudge(plans=plans)
        tutor, session = Tutor(judge), new_session()
        return tutor, session, judge, tutor.start(session, text, level)

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
            [TopicPlan("confirm", "Photosynthesis"), ok], "foto sin thesis", "Class 8"
        )
        self.assertEqual(reply["action"], "confirm_topic")
        reply = tutor.turn(session, "haan")
        self.assertEqual(reply["action"], "start_explain")
        self.assertEqual(judge.plan_calls[-1], ("Photosynthesis", "Class 8", True))

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
            "Why the moon has phases", "Class 8",
        )
        self.assertIn("explain it in your own words", reply["text"])

    def test_explanation_given_with_the_topic_is_judged_at_once(self):
        plan = TopicPlan("ok", "Moon", "Class 8", has_explanation=True, key_points=moon_points())
        judge = FakeJudge(plans=[plan], turns=[ask((1, 2), 3, "Q?")])
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
