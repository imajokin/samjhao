# Samjhao

"Samjhao" is Hindi for "explain it to me". It is a voice tutor that listens.

Most learning apps talk and the student listens. Samjhao does the opposite. The learner picks a class, says a topic and explains it aloud. Samjhao finds the part that was wrong or skipped and asks one short question about it. It does not give the answer.

- If the learner is stuck, they get a gentle hint, then a stronger one, each with a nudge to try once more. Only after both hints does Samjhao explain that point and move on.
- At the end, a summary shows which points the learner explained on their own and which needed help.
- It works in Hindi, English, Punjabi, Telugu and Kannada, and when any of them is mixed with English.

Built for Build for Bharat (India Runs on Voice), Round 2, between 27 and 30 November 2026.

## Live demo and video

- Live demo: to be added before submission
- Video (3 minutes): to be added before submission

The tutor needs two paid keys, so the live demo and the video are where you can see it working.

## Run it

```
docker compose up
```

Then open http://localhost:8000 in Chrome.

If port 8000 is already in use on your machine, pick another one: `PORT=8080 docker compose up`, then open http://localhost:8080.

## With no keys

The app starts with no keys and no `.env` file. The home screen appears and says clearly that keys are not set, with the mic switched off. The tutor itself does not listen or reply until the keys are added.

## Add keys

Copy `.env.example` to `.env`, fill in the two keys, and start again:

- `OPENROUTER_API_KEY` turns on judging. A language model reached through OpenRouter judges the explanation and writes each reply.
- `SARVAM_API_KEY` turns on speech in and out, through Sarvam.

Keys stay on the server. They are never sent to the browser, and they are not in this repository.

## How it is built

- One small Python server (FastAPI) that also serves a plain HTML, CSS and JavaScript page. One Docker container, no build step.
- `app/tutor/engine.py` holds the rules of the conversation. The language model writes the words, but the engine decides which move is allowed (ask, first hint, stronger hint, explain, finish) and discards a reply that makes a different move.
- A point is marked as explained only if the words quoted for it can be found in what the learner said.
- No login, no database, no analytics.

## Privacy

- Nothing a learner says is saved to disk or written to a log.
- While a session is running, the conversation is held in the server's memory. The words are dropped when the summary is shown, and an idle session is forgotten after 30 minutes.
- To work, the recorded audio is sent to Sarvam and the text is sent to OpenRouter. Their own handling of that data is outside this app.
- `DEV_VIEWER=on` adds a developer page that shows conversations in memory. It is off by default, refuses any request that arrives through a proxy or tunnel, and must never be set on a public link.

## Limits that protect a public link

A per-visitor request limit, a daily request cap and a daily cap on paid model calls are built in (see `.env.example`). The spending limit set on each key at the provider is the real guard.

## Tests

```
docker compose run --rm samjhao python -m unittest discover -s tests -v
```

The tests use a fake judge and need no keys.

## Known limits

- The tutor can judge wrongly: it may mishear a learner or misread an explanation. It always shows what it heard, and a "heard it wrong? say it again" button undoes the last answer.
- The Punjabi, Telugu and Kannada fixed phrases were written with AI help and are being checked by native speakers.
- Replies take a few seconds, because speech and judging are done by outside services.

See `HANDOVER.md` for the original plan and `DECISIONS.md` for what was decided since, with reasons.
