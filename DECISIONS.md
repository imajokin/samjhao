# Samjhao decisions

One line per decision, with the date and the reason. Nothing is decided until Shubham says so.

| Date | Decision | Why |
|---|---|---|
| 27 Nov 2026 | All judging is done by a language model with a key. No rule-based or keyless judge. | Shubham's instruction; matches HANDOVER.md version 2, section 4.1. |
| 27 Nov 2026 | Speech-to-text uses Sarvam's regular model, not Sarvam Dictate. | Shubham's instruction; Dictate may tidy away the mistakes we need to hear. |
| 27 Nov 2026 | A new OpenRouter key and a Sarvam key, used only for this project, live only in .env. | Shubham's instruction; no key from any other project is used. |
| 27 Nov 2026 | HANDOVER.md version 2 (from Downloads, with sections 4.2 and 4.4) is the current handover. | Shubham pointed to it at the start of the build session. |
| 27 Nov 2026 | No login and no database. | Shubham's instruction and HANDOVER.md 13.1. |
| 27 Nov 2026 | Built as a Python server (FastAPI) with a plain HTML, CSS and JavaScript page, in one Docker container. | Shubham approved the handover proposal; fewest parts that can fail when reviewers start it. |
| 27 Nov 2026 | Colima (free, no account) runs Docker on the laptop for testing. | Shubham approved; no Docker runner was installed. |
| 27 Nov 2026 | Jev (TypeSafe AI, through OpenRouter) joins the judging comparison as "Jev gives the verdict, a regular model writes the key points and the question". | Shubham asked for it; Jev does not write text, so it can only do the verdict half. It stays only if it catches every planted mistake. |
| 27 Nov 2026 | The live demo and video links on the no-keys screen are written into the code (app/config.py), with .env able to override them. | Reviewers start with no .env, so links kept only in .env would not appear. Proposed by Claude; tell Shubham if he objects. |

## Open (waiting for Shubham)

- The new OpenRouter key in .env, with a credit limit (suggested $10).
- The regular models to compare (proposed: Claude Haiku 5.5, GPT-6 Luna, GPT-6.1 Terra, Claude Fable 5.2 as the benchmark, plus Jev).
- What matters most if models disagree (proposed: catching every mistake, then speed, then cost).
- Total budget for the four days (proposed: $25 ceiling).

## Checked against live documentation (27 Nov 2026)

These replace the unverified notes in HANDOVER.md section 4.4.

- Sarvam speech-to-text: `POST https://api.sarvam.ai/speech-to-text`, header `api-subscription-key`. Regular model is `saaras:v4`. Dictate is a separate product and is not used.
- Sarvam's 30-second limit is real (longer audio is refused). Its live-streaming route does not take the audio format browsers record. So a 90-second explanation needs either cutting into pieces of under 30 seconds, or Sarvam's batch route. To be decided with Shubham at milestone 4.
- Sarvam accepts WebM (Chrome) and MP4 (Safari) recordings. To be confirmed with a real phone recording.
- Sarvam transcript modes: `transcribe`, `verbatim`, `translit`, `codemix`, `translate`. Language can be detected automatically; 23 Indian languages are listed.
- Sarvam text-to-speech: `POST https://api.sarvam.ai/text-to-speech`, models `bulbul:v4-flash` and `bulbul:v3`, up to 2,500 characters, handles Hindi mixed with English.
- Sarvam price: about ₹0.49 per minute of listening, ₹2 to ₹3 per 1,000 characters spoken, ₹100 free credit on sign-up.
- OpenRouter: `POST https://openrouter.ai/api/v1/chat/completions`. A spending limit can be set on each key in the key's settings ("Key limit"), with an optional daily reset.
- Jev on OpenRouter: `POST https://openrouter.ai/api/alpha/decisions`, model `typesafe/jev-1.14`. It answers yes/no, choice and score questions with probabilities. It is marked alpha, so its format may change. About $0.042 per million tokens in.
