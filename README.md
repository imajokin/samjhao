# Samjhao

"Samjhao" is Hindi for "explain it to me". It is a voice tutor that listens.

Most learning apps talk and the student listens. Samjhao does the opposite: the learner explains a topic aloud, in Hindi, English or a mix, and Samjhao asks one short question about the part that was skipped or wrong. It does not give the answer.

Built for Build for Bharat (India Runs on Voice), Round 2, between 27 and 30 November 2026.

## Run it

```
docker compose up
```

Then open http://localhost:8000 in Chrome.

## With no keys

The app starts with no keys and no `.env` file. The home screen appears and says clearly that keys are not set. The tutor itself needs two keys, so it does not listen or reply until they are added.

## Add keys

Copy `.env.example` to `.env`, fill in the two keys, and start again:

- `OPENROUTER_API_KEY` turns on judging (a language model reached through OpenRouter).
- `SARVAM_API_KEY` turns on speech in and out (Sarvam).

Keys stay on the server. They are never sent to the browser.

## Tests

```
docker compose run --rm samjhao python -m unittest discover -s tests -v
```

The tests need no keys.

## Status

Work in progress. See `HANDOVER.md` for the plan and `DECISIONS.md` for the choices made so far.
