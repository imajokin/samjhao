"""Tests for the API routes, with a fake judge, so they need no keys.

Run with:  python -m unittest discover -s tests -v
"""

import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from app.config import load_settings
from app.main import create_app
from app.providers.errors import ServiceDown
from app.ratelimit import RateLimiter
from app.sessions import SessionStore
from app.tutor.models import Judgement, KeyPoint, TopicPlan

LONG = "the earth spins on its axis once in a day"


class FakeJudge:
    def __init__(self, fail=False):
        self.fail = fail

    def make_key_points(self, topic, level, confirmed):
        if self.fail:
            raise ServiceDown("judging", "test")
        points = [
            KeyPoint(1, "The Earth spins.", question="Q1?", hint="H1.", explanation="E1."),
            KeyPoint(2, "One spin takes a day.", question="Q2?", hint="H2.", explanation="E2."),
        ]
        return TopicPlan("ok", "Day and night", "Class 8", key_points=points)

    def write_support(self, session, point):
        self.support_calls = getattr(self, "support_calls", 0) + 1

    def judge_turn(self, session, transcript):
        if "everything" in transcript:
            return Judgement({1: "covered", 2: "covered"}, move="done", reply="All clear.")
        if session.current_id == 2:
            return Judgement({1: "covered", 2: "missing"}, move="hint1", about_id=2,
                             reply="Think of a clock.", hint="Think of a clock.")
        return Judgement({1: "covered", 2: "missing"}, move="ask", about_id=2,
                         reply="How long?", question="How long?")


def client(judge=None, **env) -> TestClient:
    settings_env = {"OPENROUTER_API_KEY": "test-value", "SARVAM_API_KEY": "", "DEV_VIEWER": "", **env}
    with mock.patch.dict(os.environ, settings_env, clear=False):
        return TestClient(create_app(load_settings(), judge=judge or FakeJudge()))


class SessionRoutes(unittest.TestCase):
    def test_full_typed_session(self):
        api = client()
        start = api.post("/api/session/start", json={"topic_text": "Day and night, Class 8"}).json()
        self.assertEqual(start["action"], "start_explain")
        self.assertEqual(start["points_total"], 2)
        sid = start["session_id"]

        turn = api.post(f"/api/session/{sid}/turn", json={"transcript": LONG}).json()
        self.assertEqual(turn["action"], "follow_up")
        self.assertEqual(turn["text"], "How long?")
        self.assertEqual(turn["progress"], {"done": 1, "total": 2})
        self.assertNotIn("summary", turn)

        # The key points stay hidden until the end.
        self.assertEqual(api.get(f"/api/session/{sid}/summary").status_code, 409)

        done = api.post(f"/api/session/{sid}/turn", json={"transcript": "everything"}).json()
        self.assertEqual(done["action"], "done")
        self.assertEqual([p["result"] for p in done["summary"]["points"]], ["green", "green"])
        self.assertEqual(api.get(f"/api/session/{sid}/summary").json(), done["summary"])

    def test_saying_it_again_replaces_the_last_answer(self):
        api = client()
        sid = api.post("/api/session/start", json={"topic_text": "Day and night, Class 8"}).json()["session_id"]
        api.post(f"/api/session/{sid}/turn", json={"transcript": LONG})
        # A misheard answer: it misses, so a hint is given and a try is used.
        missed = api.post(f"/api/session/{sid}/turn", json={"transcript": "garbled words"}).json()
        self.assertEqual(missed["action"], "hint")
        # Said again: the miss is undone, and the point is green, not amber.
        done = api.post(
            f"/api/session/{sid}/turn", json={"transcript": "everything", "redo": True}
        ).json()
        self.assertEqual(done["action"], "done")
        self.assertEqual([p["result"] for p in done["summary"]["points"]], ["green", "green"])

    def test_speech_routes_need_the_sarvam_key(self):
        api = client()
        self.assertEqual(api.post("/api/speak", json={"text": "hello"}).json()["error"], "keys_not_set")
        reply = api.post("/api/transcribe", content=b"abc", headers={"Content-Type": "audio/webm"})
        self.assertEqual(reply.json()["error"], "keys_not_set")

    def test_unknown_session(self):
        reply = client().post("/api/session/nope/turn", json={"transcript": "hello"})
        self.assertEqual(reply.status_code, 404)
        self.assertEqual(reply.json()["error"], "session_not_found")

    def test_judge_failure_gives_plain_words_not_a_crash(self):
        reply = client(FakeJudge(fail=True)).post(
            "/api/session/start", json={"topic_text": "Day and night, Class 8"}
        )
        self.assertEqual(reply.status_code, 503)
        body = reply.json()
        self.assertEqual(body["error"], "service_down")
        self.assertIn("try again", body["text"])

    def test_female_voice_changes_the_phrase(self):
        from app.tutor.strings import say

        self.assertIn("देता", say("explain_lead", "hindi", "male"))
        self.assertIn("देती", say("explain_lead", "hindi", "female"))

    def test_rate_limit(self):
        api = client(RATE_LIMIT_PER_MINUTE="2")
        body = {"topic_text": "Day and night, Class 8"}
        self.assertEqual(api.post("/api/session/start", json=body).status_code, 200)
        self.assertEqual(api.post("/api/session/start", json=body).status_code, 200)
        reply = api.post("/api/session/start", json=body)
        self.assertEqual(reply.status_code, 429)
        self.assertEqual(reply.json()["error"], "rate_limited")

    def test_daily_cap(self):
        api = client(DAILY_REQUEST_CAP="1")
        body = {"topic_text": "Day and night, Class 8"}
        self.assertEqual(api.post("/api/session/start", json=body).status_code, 200)
        reply = api.post("/api/session/start", json=body)
        self.assertEqual(reply.json()["error"], "daily_cap")


class FailsOnce(FakeJudge):
    """Judges fine, except that the first follow-up answer fails once."""

    def __init__(self):
        super().__init__()
        self.failed = False

    def judge_turn(self, session, transcript):
        if session.current_id == 2 and not self.failed:
            self.failed = True
            # Simulate a failure after the session was already changed.
            session.point(2).hints.append("half-applied")
            raise ServiceDown("judging", "test")
        return super().judge_turn(session, transcript)


class Safeguards(unittest.TestCase):
    def test_a_failed_turn_leaves_the_session_exactly_as_it_was(self):
        api = client(FailsOnce())
        sid = api.post("/api/session/start", json={"topic_text": "Day and night, Class 8"}).json()["session_id"]
        api.post(f"/api/session/{sid}/turn", json={"transcript": LONG})
        failed = api.post(f"/api/session/{sid}/turn", json={"transcript": "everything"})
        self.assertEqual(failed.json()["error"], "service_down")
        # The same answer again: judged as if the failure never happened.
        done = api.post(f"/api/session/{sid}/turn", json={"transcript": "everything"}).json()
        self.assertEqual(done["action"], "done")
        self.assertEqual([p["result"] for p in done["summary"]["points"]], ["green", "green"])

    def test_each_visitor_behind_a_tunnel_gets_their_own_limit(self):
        api = client(RATE_LIMIT_PER_MINUTE="1")
        body = {"topic_text": "Day and night, Class 8"}
        first = api.post("/api/session/start", json=body, headers={"CF-Connecting-IP": "1.1.1.1"})
        other = api.post("/api/session/start", json=body, headers={"CF-Connecting-IP": "2.2.2.2"})
        again = api.post("/api/session/start", json=body, headers={"CF-Connecting-IP": "1.1.1.1"})
        self.assertEqual((first.status_code, other.status_code, again.status_code), (200, 200, 429))

    def test_model_call_cap(self):
        from app.providers.errors import DailyCap
        from app.providers.llm_openrouter import OpenRouter

        with mock.patch.dict(os.environ, {"DAILY_MODEL_CALL_CAP": "2"}):
            llm = OpenRouter(load_settings())
        llm._count_call()
        llm._count_call()
        with self.assertRaises(DailyCap):
            llm._count_call()

    def test_one_turn_at_a_time(self):
        store = SessionStore()
        session = store.create()
        self.assertTrue(store.begin_turn(session.id))
        self.assertFalse(store.begin_turn(session.id))
        store.end_turn(session.id)
        self.assertTrue(store.begin_turn(session.id))

    def test_words_are_forgotten_once_the_summary_is_shown(self):
        store = SessionStore()
        session = store.create()
        session.history.append(("learner", "my words"))
        session.topic_text = session.first_words = "my topic"
        store.remember(session)
        store.forget_words(session)
        self.assertEqual((session.history, session.topic_text, session.first_words), ([], "", ""))
        session.history.append(("learner", "later"))
        store.rewind(session)  # nothing kept to go back to
        self.assertEqual(session.history, [("learner", "later")])


class DeveloperViewer(unittest.TestCase):
    def test_viewer_is_off_unless_switched_on(self):
        self.assertEqual(client().get("/dev/sessions").status_code, 404)

    def test_viewer_shows_the_conversation_when_switched_on(self):
        api = client(DEV_VIEWER="on")
        sid = api.post("/api/session/start", json={"topic_text": "Day and night, Class 8"}).json()["session_id"]
        api.post(f"/api/session/{sid}/turn", json={"transcript": LONG})
        page = api.get("/dev/sessions")
        self.assertEqual(page.status_code, 200)
        self.assertIn(LONG, page.text)
        self.assertIn("How long?", page.text)
        data = api.get("/dev/sessions.json").json()
        self.assertEqual(data[0]["history"][-1], ["tutor", "How long?"])

    def test_viewer_never_answers_through_a_tunnel_or_proxy(self):
        api = client(DEV_VIEWER="on")
        for header in ({"CF-Connecting-IP": "1.2.3.4"}, {"X-Forwarded-For": "1.2.3.4"}, {"CF-Ray": "abc"}):
            self.assertEqual(api.get("/dev/sessions", headers=header).status_code, 404, header)
            self.assertEqual(api.get("/dev/sessions.json", headers=header).status_code, 404, header)


class StoreAndLimiter(unittest.TestCase):
    def test_sessions_expire(self):
        store = SessionStore(ttl_minutes=30)
        session = store.create()
        self.assertIs(store.get(session.id), session)
        store.ttl_seconds = -1
        self.assertIsNone(store.get(session.id))

    def test_limiter_counts_per_visitor(self):
        limiter = RateLimiter(per_minute=1, daily_cap=10)
        self.assertIsNone(limiter.check("a"))
        self.assertEqual(limiter.check("a"), "rate_limited")
        self.assertIsNone(limiter.check("b"))


if __name__ == "__main__":
    unittest.main()
