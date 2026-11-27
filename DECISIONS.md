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
| 27 Nov 2026 | Judging model: Claude Haiku 5.5 through OpenRouter. | Shubham picked it after the 27 Nov comparison: best at aiming the question at the real mistake, and the extra 0.7 s per turn over GPT-6 Luna does not matter to him. |
| 27 Nov 2026 | Jev is not used. | In the comparison it marked a fully correct explanation as incomplete, and its route is still alpha. |
| 27 Nov 2026 | Samjhao asks about a point the learner got wrong before a point they merely skipped. | Shubham's decision; changes HANDOVER.md 6.2 rule 3 ("first missing or wrong"). It shows the learner the app really listened. |
| 27 Nov 2026 | Total budget ceiling for the four days: $25 across all keys. | Shubham agreed. |
| 27 Nov 2026 | The judging model keeps its "thinking" step on. | Shubham's decision after seeing the speed figures (about 11 s to prepare a topic and about 7 s per turn with thinking on, against 5 s and 2.5 s with it off). |
| 27 Nov 2026 | Sarvam also provides Samjhao's spoken voice. | Shubham agreed: one speech provider, one key. |
| 27 Nov 2026 | The learner chooses a male or a female voice. Shubham picks the two voices from a shortlist of five. | Shubham's decision. |
| 27 Nov 2026 | The prototype is built for five languages: Hindi, English, Punjabi, Telugu and Kannada. Eight to ten languages is the later goal. | Shubham's decision; replaces the handover's Hindi and English focus. |
| 27 Nov 2026 | Recordings longer than 30 seconds are cut into pieces of under 30 seconds on our server and the text is joined. | Sarvam refuses longer audio; Shubham accepted the recommendation. |
| 27 Nov 2026 | Public GitHub repo imajokin/samjhao, pushed from the first day. | Shubham approved; early pushes show the work was done during the hackathon. |
| 27 Nov 2026 | Voices: "shubh" (male) and "ritu" (female), on Sarvam's bulbul:v3 model. | Shubham picked them by ear from five samples. These named voices speak all five languages. |
| 27 Nov 2026 | Long recordings are cut in the browser, not on the server: the recorder starts a new piece at a pause after about 20 seconds (28 at most), and each piece is sent for transcription while the learner is still talking. | Same idea Shubham approved (pieces under 30 seconds), but it needs no audio-conversion software in the container and the transcript is ready sooner. Proposed by Claude; tell Shubham. |
| 27 Nov 2026 | Transcript style: Sarvam's "codemix" mode. | Tested on 27 Nov: it writes Hindi in Hindi script and English words in English letters ("Plants sunlight से खाना बनाते हैं"), which is what the screen should show and what the judge reads best. The other modes wrote English words in Hindi script, or everything in English letters. |
| 27 Nov 2026 | Direction confirmed: the learner explains and Samjhao checks (option A). Samjhao is not a tutor that teaches first. | Shubham reviewed the idea again on 27 Nov: many tutors that explain already exist. |
| 27 Nov 2026 | Judging model switched to Claude Sonnet 5.5, with thinking on. | Shubham's decision. Haiku 5.5 credited "the sun goes around the Earth" in 7 of 8 runs; Sonnet was correct on every sample and about 3 s faster per turn. About $0.06 per session. Shubham will add credits. |
| 27 Nov 2026 | Each key point now gets two hints before Samjhao explains it. A miss, "I don't know", silence and the new "मुझे नहीं पता" button all count the same: a nudge to try once more, then the next hint. The second hint is stronger (an everyday example). Changes HANDOVER.md 6.2 (one hint, two tries). | Shubham tried the app on 27 Nov: learners must be able to give up, but not at the first difficulty, and the hints were not good enough. |
| 27 Nov 2026 | Hints are written fresh on every turn by the judge, starting from what the learner just said. Ready hints from the start of the session are only the backup. | Shubham found the hints too weak. |
| 27 Nov 2026 | The home screen now explains the idea in three lines before asking for a topic. | Shubham found the opening confusing ("why am I explaining?"). |
| 27 Nov 2026 | The live link will be on Shubham's own domain, 14061406.xyz, through Cloudflare. Not on Railway, which is for office work. | Shubham's decision. The exact set-up is to be confirmed with him. |
| 27 Nov 2026 | The class is chosen on the home screen (6 to 12, College, Other) before the mic can be used. Samjhao no longer asks "which class" in the conversation. | Shubham tried the app on 27 Nov: the class question wasted a turn. |
| 27 Nov 2026 | The learner says the topic and explains it in one go. If the first words already contain an explanation, it is judged at once. The "explain it like I am your younger brother" turn is removed; a topic with no explanation gets one short line asking for it. Changes HANDOVER.md 6.1 and 6.5. | Shubham: he had already explained at the top and was asked two more questions before any judging. |
| 27 Nov 2026 | The waiting line says what Samjhao is doing, in the learner's language: writing down what was said, going through the topic, thinking of a question, or thinking of a hint. It replaces the bare "सोच रहा हूँ…". | Shubham: the learner should always be able to tell what is happening. |
| 27 Nov 2026 | The model now writes each whole reply as natural speech: a reaction to what the learner said, then the question, hint or explanation in fresh words. Our code still decides which move is allowed (ask, first hint, stronger hint, explain, finish) and uses the model's reply only if it made that move. The fixed phrases remain as the backup. | Shubham on 27 Nov: the tutor sounded strict and parroted the same sentences. In the first test sessions the model's reply followed the rules in 33 of 33 turns. |
| 27 Nov 2026 | A learner who asks Samjhao something instead of answering gets an answer, and no hint is used up (twice per point at most). | Part of making it feel like a normal conversation with a teacher. |
| 27 Nov 2026 | Key points are limited to three or four essentials per topic. | Less strict: fewer things to be questioned on. |
| 27 Nov 2026 | A developer's viewer at /dev/sessions shows the conversations currently in memory. It exists only when DEV_VIEWER=on, which is set on Shubham's laptop and must never be set on the public link. Nothing is written to disk. | Shubham asked for it so Claude can see what went wrong in a session he tried. |
| 27 Nov 2026 | Changes made after an independent review of commit a6456d5: (1) the developer viewer refuses any request that arrives through a tunnel or proxy; (2) a recording that was only partly transcribed is never judged: the learner sees what was heard and can fix it or say it again, with no hint used; (3) a point is credited only if the words quoted for it are found in what the learner said, and a doubtful word is checked with "did you say X or Y?" before judging; (4) a daily cap on paid model calls, and each visitor behind a tunnel gets their own limit; (5) a failed turn puts the session back exactly as it was, and only one turn at a time is judged per session; (6) the learner's words are dropped once the summary is shown and idle sessions are forgotten on a timer; (7) the second nudge no longer says "you are getting close"; (8) with no keys, the home screen hides the controls that cannot be used. | The reviewer's ranked list. Items that need Shubham (final links, three observed learners, provider spending limits) stay open below. |
| 27 Nov 2026 | The opening of the conversation is written by the model too. Whatever the learner says first ("my ma'am told me today that...", a greeting, a broad subject), Samjhao answers like a person and reads it together with everything said so far. Fixed phrases remain only as the backup. | Shubham on 27 Nov: he said "मेरी ma'am ने मुझे आज बताया कि" and got a fixed line back; it must talk like an assistant, not follow a script. |
| 27 Nov 2026 | Recording now ends after 5 seconds of silence (was 4), and the screen counts down during a pause. An explanation may come in several parts; all of it is judged together. | The recording cut Shubham off in the middle of a sentence. Changes HANDOVER.md 6.1 (4 seconds). |
| 27 Nov 2026 | A cancel button is shown while recording. Page files carry a version stamp so a browser cannot mix old and new copies. | Shubham asked for cancel; a stale script copy then made it do nothing. |
| 27 Nov 2026 | Speed: the judge keeps full thinking for now (10 to 17 s per turn). | Shubham's decision after seeing the numbers. |
| 27 Nov 2026 | Live link: https://samjhao.14061406.xyz, served by a separate copy on Shubham's Mac Mini through its own Cloudflare tunnel (not the office tunnel), open to everyone with no login. The Mini stays on until 2 Dec. | Shubham's decisions on 27 Nov. |
| 27 Nov 2026 | The live copy has its own OpenRouter key, the developer viewer off, and a cap of 100 paid model calls a day. | Shubham's decisions; keeps public use from draining the testing key and the bill inside the budget. |
| 27 Nov 2026 | The live link is up at https://samjhao.14061406.xyz. It runs from ~/Projects/samjhao-live on the Mac Mini (port 8017, Colima), through a Cloudflare tunnel named "samjhao" with its settings in ~/.cloudflared/samjhao.yml. The tunnel and Colima start by themselves at login; the container restarts by itself. The address is written into app/config.py and the README. | Set up with Shubham on 27 Nov. To update the live copy: on the Mini, in that folder, git pull and docker compose up -d --build. |
| 27 Nov 2026 | Samjhao asks about at most three points in a session, tells the learner how many questions there are in its first question, shows "Question 2 of 3" on screen, and says when the questions are over. Points it did not get to are shown in grey as "not discussed". | Shubham on 27 Nov: the learner must know when the final explanation is coming and why they are being asked questions. |
| 27 Nov 2026 | A "show me the full explanation" button is always there during a session. It ends the questions at once; points not yet explained get no credit. | Shubham: a learner who wants to get to the point must be able to. |
| 27 Nov 2026 | The summary screen now starts with the full explanation (four to six sentences in the learner's language, with a listen button) and a diagram drawn by the model for any topic. The diagram is restricted to plain shapes and text, is shown only as an image, and carries a note that it may not be exact. Not in the original handover. | Shubham asked for diagrams in the final explanation for every topic. Tested on four topics: three good, one (Pythagoras) drawn incompletely. |
| 27 Nov 2026 | A line on the summary says a hand-picked video for the learner's class will be added later. Finding real YouTube videos is left for a later version. | Shubham's decision. |
| 27 Nov 2026 | Home screen: the voice choice sits above the class choice, there are ten example topics across subjects, and the headline says "Explain it to Samjhao". | Shubham's requests. |
| 27 Nov 2026 | The live link was opened by Shubham in Chrome on an iPhone and worked; the reply speed is acceptable to him. | His test on 27 Nov. |

## Open (waiting for Shubham)

- Video link: to go into app/config.py and README.md once the video exists.
- A test of the live link on a real Android phone (it worked on an iPhone).
- Sarvam has no spending limit except its balance (about 3,455 credits on 27 Nov). Proposed: lower the live daily request cap to 600 and limit spoken replies to 600 characters.
- Changes since commit 9668a79 are on the laptop only, by Shubham's instruction. Push to GitHub and update the live copy when he says.
- Three learners finishing a session unaided before the demo is recorded (reviewer's item 6).
- Sarvam: what balance or limit protects that key. The OpenRouter key has a $10 limit (checked 27 Nov: $2.56 used).
- Native-speaker check of the Punjabi, Telugu and Kannada phrases (Shubham is arranging it).

## Checked against live documentation (27 Nov 2026)

These replace the unverified notes in HANDOVER.md section 4.4.

- Sarvam speech-to-text: `POST https://api.sarvam.ai/speech-to-text`, header `api-subscription-key`. Regular model is `saaras:v4`. Dictate is a separate product and is not used.
- Sarvam's 30-second limit is real (longer audio is refused). Its live-streaming route does not take the audio format browsers record. So a 90-second explanation needs either cutting into pieces of under 30 seconds, or Sarvam's batch route. To be decided with Shubham at milestone 4.
- Sarvam accepts WebM (Chrome) and MP4 (Safari) recordings. To be confirmed with a real phone recording.
- Sarvam transcript modes: `transcribe`, `verbatim`, `translit`, `codemix`, `translate`. Language can be detected automatically; 23 Indian languages are listed.
- Sarvam text-to-speech: `POST https://api.sarvam.ai/text-to-speech`, models `bulbul:v4-flash` and `bulbul:v3`, up to 2,500 characters, handles Hindi mixed with English.
- Sarvam price: about ₹0.49 per minute of listening, ₹2 to ₹3 per 1,000 characters spoken, ₹100 free credit on sign-up.
- Claude Sonnet 5.5 does not allow its thinking step to be switched off through OpenRouter; the lightest setting is `reasoning: {effort: low}`.
- OpenRouter: `POST https://openrouter.ai/api/v1/chat/completions`. A spending limit can be set on each key in the key's settings ("Key limit"), with an optional daily reset.
- Jev on OpenRouter: `POST https://openrouter.ai/api/alpha/decisions`, model `typesafe/jev-1.14`. It answers yes/no, choice and score questions with probabilities. It is marked alpha, so its format may change. About $0.042 per million tokens in.
