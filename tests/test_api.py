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

    def make_key_points(self, topic, level, language, confirmed):
        if self.fail:
            raise ServiceDown("judging", "test")
        points = [
            KeyPoint(1, "The Earth spins.", question="Q1?", hint="H1.", explanation="E1."),
            KeyPoint(2, "One spin takes a day.", question="Q2?", hint="H2.", explanation="E2."),
        ]
        return TopicPlan("ok", "Day and night", "Class 8", key_points=points)

    def judge_turn(self, session, transcript):
        if "everything" in transcript:
            return Judgement({1: "covered", 2: "covered"})
        return Judgement({1: "covered", 2: "missing"}, first_gap_id=2, follow_up="How long?")


def client(judge=None, **env) -> TestClient:
    settings_env = {"OPENROUTER_API_KEY": "test-value", "SARVAM_API_KEY": "", **env}
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
        reply = client().post(
            "/api/session/start", json={"topic_text": "Day and night, Class 8", "voice": "female"}
        ).json()
        self.assertIn("younger sister", reply["text"])

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
