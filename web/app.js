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
  tapToSpeak: "Mic दबाओ और बोलो · Tap the mic and speak",
  listening: "सुन रहा हूँ… रुकने के लिए फिर दबाओ · Listening… tap again to stop",
  speechFailed: "आवाज़ अभी काम नहीं कर रही। Type करके बताओ। / Speech is not working right now. Please type instead.",
  pickClass: "पहले अपनी class चुनो · Choose your class first",
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
  byId("mic-label").textContent = TEXT.pickClass;
  return false;
}

function chosenVoice() {
  const picked = document.querySelector('input[name="voice"]:checked');
  return picked ? picked.value : "male";
}

// A fixed phrase from the server, in the learner's language and chosen voice.
function phrase(key, fallback) {
  const phrases = (state.config && state.config.phrases) || {};
  const lang = state.lang === "hinglish" ? "hindi" : state.lang;
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
  if (!config.judging) return; // nothing can be judged, so nothing to start

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
    byId("mic-label").textContent = TEXT.tapToSpeak;
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
  const label = mode === "recording" ? TEXT.listening : TEXT.tapToSpeak;
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
      onStop: async (reason, heardVoice) => {
        setMic("busy");
        const replies = await Promise.all(pieces);
        const failed = replies.some((reply) => !reply.ok);
        const texts = replies.map((reply) => (reply.ok && reply.data.transcript) || "");
        const code = replies.map((reply) => reply.ok && reply.data.language_code).find(Boolean);
        const text = heardVoice ? texts.join(" ").replace(/\s+/g, " ").trim() : "";
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

  if (heard.failed && !heard.text) {
    // The speech service failed: offer the text box.
    showTextBox(false);
    sayLocally(TEXT.speechFailed, where);
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

function setBusy(busy) {
  state.busy = busy;
  byId("thinking").hidden = !busy;
  byId("thinking").textContent = phrase("thinking", "सोच रहा हूँ…");
  for (const button of document.querySelectorAll(".send")) {
    button.disabled = busy;
  }
  setMic(busy ? "busy" : "idle");
}

function showProgress(progress) {
  const row = byId("progress");
  row.textContent = "";
  if (!progress || !progress.total) {
    row.hidden = true;
    return;
  }
  // Dots only: how many points are done, never what they are.
  for (let i = 0; i < progress.total; i += 1) {
    const dot = document.createElement("span");
    dot.className = i < progress.done ? "dot done" : "dot";
    row.appendChild(dot);
  }
  row.setAttribute("aria-label", progress.done + " of " + progress.total + " points done");
  row.hidden = false;
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
  if (data.error === "rate_limited") text = TEXT.slowDown;
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
  setBusy(true);
  const reply = await Api.turn(state.sessionId, "", { silent: true });
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
  state.lang = "hinglish";
  byId("tutor-text").textContent = "";
  byId("give-up").hidden = true;
  showHeard(text, false);
  showProgress(null);
  show("talk");
  setBusy(true);
  const reply = await Api.start(text, chosenVoice(), languageCode, chosenLevel());
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
  setBusy(true);
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
  for (const point of (data.summary && data.summary.points) || []) {
    const item = document.createElement("li");
    const mark = document.createElement("span");
    const green = point.result === "green";
    mark.className = green ? "mark green" : "mark amber";
    mark.textContent = green ? "✓" : "●";
    mark.setAttribute("aria-label", green ? "Explained on your own" : "Needed help");
    const text = document.createElement("span");
    text.textContent = point.statement;
    item.appendChild(mark);
    item.appendChild(text);
    list.appendChild(item);
  }
  byId("new-topic").textContent = phrase("new_topic_button", "नया topic");
  show("summary");
}

function backHome() {
  Player.stop();
  if (Recorder.active) Recorder.stop("tap");
  state.sessionId = null;
  byId("home-input").value = "";
  if (state.voiceOn) byId("mic-label").textContent = TEXT.tapToSpeak;
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

byId("give-up").addEventListener("click", giveUp);
byId("class-picker").addEventListener("change", () => {
  byId("class-picker").classList.remove("needed");
  if (state.voiceOn) byId("mic-label").textContent = TEXT.tapToSpeak;
});
byId("home-type-link").addEventListener("click", () => showTextBox(false));
byId("talk-type-link").addEventListener("click", () => showTextBox(false));
byId("new-topic").addEventListener("click", backHome);
byId("start-over").addEventListener("click", backHome);

startHome();
