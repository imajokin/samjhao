// The screens and the flow: Home -> Explain -> Follow-up loop -> Summary.
// The server decides what happens next. This file only shows it, records
// the learner, and plays the replies.

const NOTICES = {
  // No keys at all: what reviewers see on a fresh download.
  none: {
    title: "Keys are not set",
    hi: "Keys set नहीं हैं, इसलिए Samjhao अभी सुन या जवाब नहीं दे सकता।",
    en: "Keys are not set, so Samjhao cannot listen or reply yet. Try the live demo or watch the video.",
    mic: "Mic is off: keys are not set",
  },
  // Judging works, speech does not.
  noSpeech: {
    title: "Sarvam key is not set",
    hi: "Sarvam key set नहीं है, इसलिए Samjhao अभी सुन या बोल नहीं सकता। Type करके समझाओ।",
    en: "The Sarvam key (SARVAM_API_KEY) is missing, so speech is off. You can type instead.",
    mic: "Mic is off: Sarvam key is not set",
  },
  // Speech works, nothing can judge.
  noJudging: {
    title: "OpenRouter key is not set",
    hi: "OpenRouter key set नहीं है, इसलिए Samjhao अभी तुम्हारा explanation जाँच नहीं सकता।",
    en: "The OpenRouter key (OPENROUTER_API_KEY) is missing, so Samjhao cannot judge an explanation yet.",
    mic: "Mic is off: OpenRouter key is not set",
  },
  // The server did not answer.
  down: {
    title: "Something is not working",
    hi: "अभी थोड़ी दिक्कत आ रही है। थोड़ी देर में फिर से कोशिश करो।",
    en: "Something is not working right now. Please try again in a little while.",
    mic: "Mic is off",
  },
};

const TEXT = {
  serviceDown: "अभी थोड़ी दिक्कत आ रही है। थोड़ी देर में फिर से कोशिश करो। / Something is not working right now. Please try again in a little while.",
  sessionGone: "यह session पूरा हो चुका है। नया topic शुरू करो। / This session has ended. Please start a new topic.",
  slowDown: "थोड़ा रुको, फिर कोशिश करो। / Please wait a moment and try again.",
  partHeard: "तुम्हारी बात का कुछ हिस्सा सुनाई नहीं दिया। जो सुना वह नीचे लिखा है: उसे ठीक करके भेजो, या mic दबाकर फिर से बोलो। / Part of what you said was not heard. What was heard is in the box below: correct it and send, or tap the mic and say it again.",
  speechFailed: "आवाज़ अभी काम नहीं कर रही। Type करके बताओ। / Speech is not working right now. Please type instead.",
  micBlocked: "Mic की अनुमति नहीं मिली। Address bar के ताले (lock) पर tap करके Microphone को Allow करो, या नीचे type करो। / The mic is blocked. Tap the lock icon in the address bar and allow the microphone, or type below.",
};

const state = {
  config: null,
  sessionId: null,
  lang: "hinglish",
  busy: false,
  voiceOn: false, // true when the mic can be used
  where: "home", // which mic is in use: "home" or "talk"
  lastWasSpoken: false,
};

function byId(id) {
  return document.getElementById(id);
}

function show(screenId) {
  for (const id of ["home", "talk", "summary"]) {
    byId(id).hidden = id !== screenId;
  }
  window.scrollTo(0, 0);
}

// The language Samjhao should reply in when the learner picked an app language.
// Hindi speakers mix in English, so Hindi means "Hindi mixed with English".
function appReplyLanguage() {
  return Lang.current === "hindi" ? "hinglish" : Lang.current;
}

// The learner changed the app language.
function changeLanguage(language) {
  Lang.set(language);
  Lang.apply();
  if (!state.sessionId) state.lang = appReplyLanguage();
  if (state.voiceOn && !Recorder.active) {
    byId("mic-label").textContent = Lang.both("tap_to_speak");
    byId("talk-mic-label").textContent = Lang.both("tap_to_speak");
  }
}

// The class picked on the home screen, or "" if none yet.
function chosenLevel() {
  const picked = document.querySelector('input[name="level"]:checked');
  return picked ? picked.value : "";
}

// Asks for the class if it is missing. Returns true when one is chosen.
function haveLevel() {
  if (chosenLevel()) return true;
  const picker = byId("class-picker");
  picker.classList.add("needed");
  picker.scrollIntoView({ block: "center" });
  byId("mic-label").textContent = Lang.both("pick_class");
  return false;
}

function chosenVoice() {
  const picked = document.querySelector('input[name="voice"]:checked');
  return picked ? picked.value : "male";
}

// A fixed phrase from the server, in the learner's language and chosen voice.
function phrase(key, fallback) {
  const phrases = (state.config && state.config.phrases) || {};
  // During a session, use the language Samjhao is replying in. Otherwise the app language.
  const wanted = state.sessionId || state.busy ? state.lang : Lang.current;
  const lang = wanted === "hinglish" ? "hindi" : wanted;
  let text = (phrases[lang] || {})[key] || (phrases.hindi || {})[key] || fallback;
  if (Array.isArray(text)) {
    text = chosenVoice() === "female" ? text[1] : text[0];
  }
  return text;
}

// ----- Home -----

function showLink(id, url) {
  const link = byId(id);
  if (!url) {
    link.hidden = true;
    return false;
  }
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener";
  link.hidden = false;
  return true;
}

function showNotice(notice, config) {
  byId("notice-title").textContent = notice.title;
  byId("notice-hi").textContent = notice.hi;
  byId("notice-en").textContent = notice.en;
  byId("mic-label").textContent = notice.mic;

  const hasDemo = showLink("link-demo", config && config.live_demo_url);
  const hasVideo = showLink("link-video", config && config.video_url);
  byId("notice-links").hidden = !(hasDemo || hasVideo);
  byId("notice-links-pending").hidden = hasDemo || hasVideo;
  byId("notice").hidden = false;
}

function pickNotice(config) {
  if (!config.judging && !config.speech) return NOTICES.none;
  if (!config.speech) return NOTICES.noSpeech;
  if (!config.judging) return NOTICES.noJudging;
  return null;
}

async function startHome() {
  const reply = await Api.config();
  if (!reply.ok) {
    showNotice(NOTICES.down, null);
    return;
  }
  const config = reply.data;
  state.config = config;

  const notice = pickNotice(config);
  if (notice) {
    showNotice(notice, config);
  } else {
    byId("notice").hidden = true;
  }
  if (!config.judging) {
    // Nothing can be judged, so hide the controls that cannot be used. The
    // message, the links and the switched-off mic stay near the top.
    for (const id of ["class-picker", "home-prompt", "examples"]) byId(id).hidden = true;
    return;
  }

  byId("voice-picker").hidden = false;
  for (const chip of document.querySelectorAll(".chip")) {
    chip.disabled = false;
    chip.addEventListener("click", () => {
      Player.unlock();
      beginTopic(chip.textContent, "", false);
    });
  }

  state.voiceOn = Boolean(config.speech) && Recorder.supported();
  if (state.voiceOn) {
    byId("mic").disabled = false;
    byId("mic-label").textContent = Lang.both("tap_to_speak");
    byId("home-type-link").hidden = false;
    byId("talk-type-link").hidden = false;
  } else {
    // No speech: the text box is the way in.
    showTextBox(true);
    if (config.speech) byId("mic-label").textContent = TEXT.micBlocked;
  }
}

// Shows the text boxes. With `only`, the mics are hidden too.
function showTextBox(only) {
  byId("home-form").hidden = false;
  byId("talk-form").hidden = false;
  byId("home-type-link").hidden = true;
  byId("talk-type-link").hidden = true;
  if (only) byId("talk-mic-area").hidden = true;
}

// ----- Listening -----

function setMic(mode) {
  // mode: "idle", "recording" or "busy"
  for (const id of ["mic", "talk-mic"]) {
    const button = byId(id);
    button.classList.toggle("recording", mode === "recording");
    button.disabled = mode === "busy" || !state.voiceOn;
  }
  // The cancel button is there only while recording.
  byId("cancel-home").hidden = mode !== "recording";
  byId("cancel-talk").hidden = mode !== "recording";
  const label = mode === "recording" ? Lang.both("listening") : Lang.both("tap_to_speak");
  if (state.voiceOn) {
    byId("mic-label").textContent = label;
    byId("talk-mic-label").textContent = label;
  }
}

// Records the learner and gives back {text, languageCode, failed}.
function listen() {
  return new Promise((resolve, reject) => {
    const pieces = [];
    Recorder.start({
      onPiece: (blob) => pieces.push(Api.transcribe(blob)),
      onQuiet: (secondsLeft) => {
        // A pause is fine. Show how long before the recording is sent.
        if (!Recorder.active) return;
        const label = secondsLeft ? Lang.both("pausing").replace(/\{n\}/g, secondsLeft) : Lang.both("listening");
        byId("mic-label").textContent = label;
        byId("talk-mic-label").textContent = label;
      },
      onStop: async (reason, heardVoice) => {
        if (reason === "cancel") {
          // The learner cancelled: forget the recording and send nothing.
          resolve({ cancelled: true });
          return;
        }
        setMic("busy");
        const writing = phrase("thinking_writing", "तुम्हारी बात लिख रहा हूँ…");
        byId("mic-label").textContent = writing;
        byId("talk-mic-label").textContent = writing;
        const replies = await Promise.all(pieces);
        const failed = replies.some((reply) => !reply.ok);
        const texts = replies.map((reply) => (reply.ok && reply.data.transcript) || "");
        const code = replies.map((reply) => reply.ok && reply.data.language_code).find(Boolean);
        // Use the words that came back whenever there are any, even if the
        // sound meter thought the room was silent.
        const text = texts.join(" ").replace(/\s+/g, " ").trim();
        resolve({ text, languageCode: code || "", failed });
      },
    })
      .then(() => setMic("recording"))
      .catch(reject);
  });
}

async function micTapped(where, redo) {
  if (where === "home" && !Recorder.active && !haveLevel()) return;
  Player.unlock();
  if (Recorder.active) {
    Recorder.stop("tap");
    return;
  }
  if (state.busy) return;
  Player.stop();
  state.where = where;

  let heard;
  try {
    heard = await listen();
  } catch (error) {
    // The mic was refused, or there is none.
    state.voiceOn = false;
    setMic("idle");
    byId("mic-label").textContent = TEXT.micBlocked;
    byId("talk-mic-label").textContent = TEXT.micBlocked;
    showTextBox(false);
    return;
  }
  setMic("idle");
  if (heard.cancelled) return;

  if (heard.failed) {
    // Part or all of the recording could not be turned into text. Never judge
    // half an explanation: show what was heard and let the learner fix it or
    // say it again. Nothing is sent, so no hint is used up.
    showTextBox(false);
    if (heard.text) {
      byId(where === "home" ? "home-input" : "talk-input").value = heard.text;
      sayLocally(TEXT.partHeard, where);
    } else {
      sayLocally(TEXT.speechFailed, where);
    }
    return;
  }
  if (where === "home") {
    if (!heard.text) {
      sayLocally(phrase("not_heard", "आवाज़ साफ़ नहीं आई। फिर से बोलो।"), where, true);
      return;
    }
    beginTopic(heard.text, heard.languageCode, true);
  } else {
    sendAnswer(heard.text, { heard_ok: Boolean(heard.text), redo: Boolean(redo) }, true);
  }
}

// Shows a line that did not come from the server, and may speak it.
function sayLocally(text, where, aloud) {
  if (where === "home") {
    byId("mic-label").textContent = text;
  } else {
    byId("tutor-text").textContent = text;
  }
  if (aloud) speak(text);
}

// ----- Speaking -----

async function speak(text) {
  if (!state.config || !state.config.speech || !text) return;
  const reply = await Api.speak(text, state.lang, chosenVoice());
  if (reply.ok && reply.data instanceof Blob && !Recorder.active) {
    await Player.play(reply.data);
  }
}

// ----- Talking -----

// A quick guess at the language of what the learner just said, so the
// waiting line is in their language even before the server has replied.
function guessLanguage(text) {
  if (/[\u0A00-\u0A7F]/.test(text)) return "punjabi";
  if (/[\u0C00-\u0C7F]/.test(text)) return "telugu";
  if (/[\u0C80-\u0CFF]/.test(text)) return "kannada";
  if (/[\u0900-\u097F]/.test(text)) return "hinglish";
  if (/\b(hai|hain|ka|ki|ke|ko|mein|aur|kya|kyunki|nahi|hota|hoti|hote|se|par|toh|isliye)\b/i.test(text)) {
    return "hinglish";
  }
  return "";
}

// While the learner waits, say exactly what Samjhao is doing:
// "writing" (turning speech into text), "topic", "question" or "hint".
function setBusy(busy, kind) {
  state.busy = busy;
  byId("thinking").hidden = !busy;
  byId("tutor-text").classList.toggle("waiting", busy);
  if (busy) {
    byId("thinking").textContent = phrase("thinking_" + (kind || "question"), "थोड़ा रुको…");
  }
  for (const button of document.querySelectorAll(".send")) {
    button.disabled = busy;
  }
  setMic(busy ? "busy" : "idle");
}

// "Question 2 of 3": the learner always knows how much is left.
function showProgress(progress) {
  const label = byId("question-label");
  if (!progress || !progress.questions || !progress.question) {
    label.hidden = true;
    return;
  }
  label.textContent = phrase("question_label", "सवाल {n} / {total}")
    .replace("{n}", progress.question)
    .replace("{total}", progress.questions);
  label.hidden = false;
}

function showHeard(text, spoken) {
  byId("heard").hidden = !text;
  byId("heard-text").textContent = text;
  state.lastWasSpoken = Boolean(spoken && text);
  const again = byId("rerecord");
  again.textContent = phrase("rerecord_button", "गलत सुना? फिर से बोलो");
  // Only a spoken answer inside a session can be said again.
  again.hidden = !(state.lastWasSpoken && state.sessionId);
}

function showProblem(reply) {
  const data = reply.data || {};
  let text = TEXT.serviceDown;
  if (data.error === "service_down" && data.text) text = data.text;
  if (data.error === "daily_cap") text = (data.text_hi || "") + " / " + (data.text || "");
  if (data.error === "rate_limited" || data.error === "busy") text = TEXT.slowDown;
  if (data.error === "session_not_found") text = TEXT.sessionGone;
  if (data.error === "keys_not_set") text = NOTICES.none.hi + " / " + NOTICES.none.en;
  byId("tutor-text").textContent = text;
}

// The learner says "I don't know" with a tap. Samjhao nudges and gives the
// next hint; only after both hints does it explain.
async function giveUp() {
  if (!state.sessionId || state.busy || Recorder.active) return;
  Player.unlock();
  Player.stop();
  setBusy(true, "hint");
  const reply = await Api.turn(state.sessionId, "", { silent: true });
  setBusy(false);
  if (!reply.ok) {
    showProblem(reply);
    return;
  }
  showReply(reply.data);
}

// The learner wants the full explanation now, without more questions.
async function jumpToExplanation() {
  if (!state.sessionId || state.busy) return;
  if (Recorder.active) Recorder.cancel();
  Player.unlock();
  Player.stop();
  setBusy(true, "topic");
  const reply = await Api.finish(state.sessionId);
  setBusy(false);
  if (!reply.ok) {
    showProblem(reply);
    return;
  }
  showReply(reply.data);
}

function showReply(data) {
  state.lang = data.lang || state.lang;
  // The give-up button only makes sense while a question is open.
  const asking = ["follow_up", "hint", "app_explains", "off_topic"].includes(data.action);
  byId("give-up").hidden = !asking;
  byId("give-up").textContent = phrase("give_up_button", "मुझे नहीं पता");
  // Jumping to the full explanation is possible once the topic is settled.
  const inSession = asking || data.action === "start_explain" || data.action === "confirm_word";
  byId("jump").hidden = !inSession;
  byId("jump").textContent = phrase("jump_button", "सीधे पूरा explanation दिखाओ");
  if (data.action === "show_text_box") showTextBox(false);
  if (data.action === "done") {
    showSummary(data);
  } else {
    byId("tutor-text").textContent = data.text;
    showProgress(data.progress);
    byId("talk-input").value = "";
  }
  speak(data.text); // everything shown is also spoken
}

async function beginTopic(topicText, languageCode, spoken) {
  const text = (topicText || "").trim();
  if (!text || state.busy || !haveLevel()) return;
  state.sessionId = null;
  // The app language the learner picked wins; otherwise go by their words.
  state.lang = Lang.chosen ? appReplyLanguage() : guessLanguage(text) || "hinglish";
  byId("tutor-text").textContent = "";
  byId("give-up").hidden = true;
  byId("jump").hidden = true;
  showHeard(text, false);
  showProgress(null);
  show("talk");
  setBusy(true, "topic");
  const reply = await Api.start(text, chosenVoice(), languageCode, chosenLevel(), Lang.chosen ? appReplyLanguage() : "");
  setBusy(false);
  if (!reply.ok) {
    showProblem(reply);
    return;
  }
  state.sessionId = reply.data.session_id;
  showReply(reply.data);
}

async function sendAnswer(text, flags, spoken) {
  const answer = (text || "").trim();
  const notHeard = flags && flags.heard_ok === false;
  if ((!answer && !notHeard) || state.busy) return;
  if (!state.sessionId) {
    // The start itself failed earlier, so treat this as a new topic.
    if (answer) beginTopic(answer, "", spoken);
    return;
  }
  if (answer) showHeard(answer, spoken);
  if (!Lang.chosen) state.lang = guessLanguage(answer) || state.lang;
  setBusy(true, "question");
  const reply = await Api.turn(state.sessionId, answer, flags);
  setBusy(false);
  if (!reply.ok) {
    showProblem(reply);
    return;
  }
  showReply(reply.data);
}

// ----- Summary -----

function showSummary(data) {
  byId("summary-text").textContent = data.text;
  const list = byId("points");
  list.textContent = "";
  const marks = {
    green: ["mark green", "✓", "Explained on your own"],
    amber: ["mark amber", "●", "Needed help"],
    skipped: ["mark skipped", "–", "Not discussed"],
  };
  for (const point of (data.summary && data.summary.points) || []) {
    const item = document.createElement("li");
    const mark = document.createElement("span");
    const [className, symbol, label] = marks[point.result] || marks.amber;
    mark.className = className;
    mark.textContent = symbol;
    mark.setAttribute("aria-label", label);
    const text = document.createElement("span");
    text.textContent = point.statement;
    item.appendChild(mark);
    item.appendChild(text);
    list.appendChild(item);
  }
  byId("new-topic").textContent = phrase("new_topic_button", "नया topic");
  show("summary");
  loadRecap(state.sessionId);
}

// The full explanation and its diagram arrive a few seconds after the summary.
async function loadRecap(sessionId) {
  byId("recap-title").textContent = phrase("recap_title", "पूरा explanation");
  byId("recap-loading").textContent = phrase("recap_loading", "पूरा explanation बना रहा हूँ…");
  byId("recap-loading").hidden = false;
  byId("recap-text").hidden = true;
  byId("recap-listen").hidden = true;
  byId("diagram").hidden = true;
  byId("video-soon").textContent = phrase("video_soon", "Video जल्द जोड़ा जाएगा।");
  if (!sessionId) {
    byId("recap-loading").hidden = true;
    return;
  }
  const reply = await Api.recap(sessionId);
  if (state.sessionId !== sessionId) return; // the learner has moved on
  byId("recap-loading").hidden = true;
  if (!reply.ok || !reply.data.explanation) {
    byId("recap-text").textContent = TEXT.serviceDown;
    byId("recap-text").hidden = false;
    return;
  }
  const recap = reply.data;
  byId("recap-text").textContent = recap.explanation;
  byId("recap-text").hidden = false;
  if (state.config && state.config.speech) {
    const listen = byId("recap-listen");
    listen.textContent = "🔊 " + phrase("listen_button", "सुनो");
    listen.onclick = () => speak(recap.explanation);
    listen.hidden = false;
  }
  if (recap.svg) {
    // Shown as a picture, never run as code.
    byId("diagram-image").src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(recap.svg);
    byId("diagram-image").alt = recap.diagram_caption || "Diagram";
    byId("diagram-caption").textContent = recap.diagram_caption || "";
    byId("diagram").hidden = false;
  }
}

function backHome() {
  Player.stop();
  if (Recorder.active) Recorder.stop("tap");
  state.sessionId = null;
  byId("home-input").value = "";
  if (state.voiceOn) byId("mic-label").textContent = Lang.both("tap_to_speak");
  show("home");
}

// ----- Wiring -----

byId("mic").addEventListener("click", () => micTapped("home", false));
byId("talk-mic").addEventListener("click", () => micTapped("talk", false));
byId("rerecord").addEventListener("click", () => micTapped("talk", true));

byId("home-form").addEventListener("submit", (event) => {
  event.preventDefault();
  Player.unlock();
  beginTopic(byId("home-input").value, "", false);
});

byId("talk-form").addEventListener("submit", (event) => {
  event.preventDefault();
  Player.unlock();
  sendAnswer(byId("talk-input").value, {}, false);
});

byId("language").addEventListener("change", (event) => changeLanguage(event.target.value));
byId("give-up").addEventListener("click", giveUp);
byId("jump").addEventListener("click", jumpToExplanation);
byId("cancel-home").addEventListener("click", () => Recorder.cancel());
byId("cancel-talk").addEventListener("click", () => Recorder.cancel());
byId("class-picker").addEventListener("change", () => {
  byId("class-picker").classList.remove("needed");
  if (state.voiceOn) byId("mic-label").textContent = Lang.both("tap_to_speak");
});
byId("home-type-link").addEventListener("click", () => showTextBox(false));
byId("talk-type-link").addEventListener("click", () => showTextBox(false));
byId("new-topic").addEventListener("click", backHome);
byId("start-over").addEventListener("click", backHome);

Lang.load();
byId("language").value = Lang.current;
Lang.apply();
if (Lang.chosen) state.lang = appReplyLanguage();
startHome();
