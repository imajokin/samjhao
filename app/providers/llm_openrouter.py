"""Talks to the language model through OpenRouter.

One job: send a prompt, get back JSON in the shape we asked for. If the
reply is malformed or the call fails, it retries once, then raises
ServiceDown. The key is sent only to OpenRouter and is never logged.
"""

import json

import httpx

from app.config import Settings
from app.providers.errors import ServiceDown

TIMEOUT_SECONDS = 60


class OpenRouter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.url = settings.llm_base_url.rstrip("/") + "/chat/completions"

    def ask_json(self, prompt: str, schema: dict, name: str) -> dict:
        """The model's answer as a dictionary that matches `schema`."""
        body = {
            "model": self.settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 6000,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": name, "strict": True, "schema": schema},
            },
        }
        if not self.settings.llm_thinking:
            # The model thinks before answering unless told not to.
            body["reasoning"] = {"enabled": False}
        headers = {
            "Authorization": "Bearer " + self.settings.openrouter_api_key,
            "X-OpenRouter-Title": "Samjhao",
        }

        detail = ""
        for _attempt in (1, 2):
            try:
                reply = httpx.post(self.url, json=body, headers=headers, timeout=TIMEOUT_SECONDS)
                if reply.status_code != 200:
                    detail = f"HTTP {reply.status_code}"
                    continue
                answer = _parse(reply.json()["choices"][0]["message"]["content"])
                _check_required(answer, schema)
                return answer
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
                detail = type(error).__name__
        raise ServiceDown("judging", detail)


def _parse(text: str) -> dict:
    """The JSON object inside a reply, even if wrapped in a code fence."""
    text = (text or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("no JSON object in the reply")
    answer = json.loads(text[start : end + 1])
    if not isinstance(answer, dict):
        raise ValueError("the reply is not a JSON object")
    return answer


def _check_required(answer: dict, schema: dict) -> None:
    missing = [name for name in schema.get("required", []) if name not in answer]
    if missing:
        raise ValueError("the reply is missing: " + ", ".join(missing))
