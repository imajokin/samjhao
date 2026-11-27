"""The hackathon's hard gate: the app must start and show the home screen
with no keys set, and nothing may crash or leak a key.

Run with:  python -m unittest discover -s tests -v
"""

import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from app.config import load_settings
from app.main import create_app

KEY_NAMES = ("OPENROUTER_API_KEY", "SARVAM_API_KEY")


def client_with(env: dict) -> TestClient:
    """A test client whose settings come only from `env`."""
    clean = {k: v for k, v in os.environ.items() if k not in KEY_NAMES}
    clean.update(env)
    with mock.patch.dict(os.environ, clean, clear=True):
        return TestClient(create_app(load_settings()))


class KeylessStart(unittest.TestCase):
    def setUp(self):
        self.client = client_with({})

    def test_health_check(self):
        reply = self.client.get("/healthz")
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(reply.json(), {"ok": True})

    def test_home_screen_loads(self):
        reply = self.client.get("/")
        self.assertEqual(reply.status_code, 200)
        self.assertIn("Samjhao", reply.text)
        self.assertIn('id="notice"', reply.text)

    def test_browser_cannot_mix_old_and_new_page_files(self):
        home = self.client.get("/")
        for name in ("styles.css", "api.js", "audio.js", "app.js"):
            self.assertRegex(home.text, name.replace(".", r"\.") + r"\?v=[0-9a-f]{10}")
        self.assertEqual(home.headers["cache-control"], "no-cache")
        self.assertEqual(self.client.get("/audio.js").headers["cache-control"], "no-cache")

    def test_page_files_load(self):
        for name in ("styles.css", "app.js", "api.js", "audio.js"):
            self.assertEqual(self.client.get("/" + name).status_code, 200, name)

    def test_keys_missing_message_is_in_the_page_code(self):
        self.assertIn("Keys are not set", self.client.get("/app.js").text)

    def test_config_says_nothing_is_on(self):
        config = self.client.get("/api/config").json()
        self.assertEqual(config["judging"], False)
        self.assertEqual(config["speech"], False)
        self.assertEqual(
            set(config), {"judging", "speech", "live_demo_url", "video_url", "phrases"}
        )

    def test_key_routes_answer_cleanly(self):
        paths = ("/api/session/start", "/api/session/abc/turn", "/api/transcribe", "/api/speak")
        for path in paths:
            reply = self.client.post(path, json={})
            self.assertEqual(reply.status_code, 503, path)
            body = reply.json()
            self.assertEqual(body["error"], "keys_not_set", path)
            self.assertTrue(body["missing"], path)


class PartialKeys(unittest.TestCase):
    def test_openrouter_only(self):
        config = client_with({"OPENROUTER_API_KEY": "test-value"}).get("/api/config").json()
        self.assertEqual((config["judging"], config["speech"]), (True, False))

    def test_sarvam_only(self):
        config = client_with({"SARVAM_API_KEY": "test-value"}).get("/api/config").json()
        self.assertEqual((config["judging"], config["speech"]), (False, True))

    def test_blank_key_counts_as_not_set(self):
        config = client_with({"OPENROUTER_API_KEY": "   "}).get("/api/config").json()
        self.assertEqual(config["judging"], False)

    def test_config_never_returns_a_key(self):
        client = client_with(
            {"OPENROUTER_API_KEY": "secret-one", "SARVAM_API_KEY": "secret-two"}
        )
        text = client.get("/api/config").text
        self.assertNotIn("secret-one", text)
        self.assertNotIn("secret-two", text)

    def test_bad_number_setting_does_not_crash(self):
        client = client_with({"SESSION_TTL_MINUTES": "abc"})
        self.assertEqual(client.get("/healthz").status_code, 200)


if __name__ == "__main__":
    unittest.main()
