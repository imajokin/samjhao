// The screens and the flow: Home -> Explain -> Follow-up loop -> Summary.
// The server decides what happens next. This file only shows it.

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

const SERVICE_DOWN = "अभी थोड़ी दिक्कत आ रही है। थोड़ी देर में फिर से कोशिश करो। / Something is not working right now. Please try again in a little while.";
const SESSION_GONE = "यह session पूरा हो चुका है। नया topic शुरू करो। / This session has ended. Please start a new topic.";
const SLOW_DOWN = "थोड़ा रुको, फिर कोशिश करो। / Please wait a moment and try again.";

const state = {
  config: null,
  sessionId: null,
  lang: "hinglish",
  busy: false,
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
    byId("mic-label").textContent = "Voice is being built. Type for now.";
  }

  // Judging is all the typed flow needs.
  if (config.judging) {
    byId("home-form").hidden = false;
    byId("voice-picker").hidden = false;
    for (const chip of document.querySelectorAll(".chip")) {
      chip.disabled = false;
      chip.addEventListener("click", () => beginTopic(chip.textContent));
    }
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

function showProblem(reply) {
  const data = reply.data || {};
  let text = SERVICE_DOWN;
  if (data.error === "service_down" && data.text) text = data.text;
  if (data.error === "daily_cap") text = (data.text_hi || "") + " / " + (data.text || "");
  if (data.error === "rate_limited") text = SLOW_DOWN;
  if (data.error === "session_not_found") text = SESSION_GONE;
  if (data.error === "keys_not_set") text = NOTICES.none.hi + " / " + NOTICES.none.en;
  byId("tutor-text").textContent = text;
}

function showReply(data) {
  state.lang = data.lang || state.lang;
  if (data.action === "done") {
    showSummary(data);
    return;
  }
  byId("tutor-text").textContent = data.text;
  showProgress(data.progress);
  byId("talk-input").value = "";
  byId("talk-input").focus();
}

async function beginTopic(topicText) {
  const text = (topicText || "").trim();
  if (!text || state.busy) return;
  state.sessionId = null;
  state.lang = "hinglish";
  byId("tutor-text").textContent = "";
  byId("heard").hidden = false;
  byId("heard-text").textContent = text;
  showProgress(null);
  show("talk");
  setBusy(true);
  const reply = await Api.start(text, chosenVoice());
  setBusy(false);
  if (!reply.ok) {
    showProblem(reply);
    return;
  }
  state.sessionId = reply.data.session_id;
  showReply(reply.data);
}

async function sendAnswer(text) {
  const answer = (text || "").trim();
  if (!answer || state.busy) return;
  if (!state.sessionId) {
    // The start itself failed earlier, so treat this as a new topic.
    beginTopic(answer);
    return;
  }
  byId("heard").hidden = false;
  byId("heard-text").textContent = answer;
  setBusy(true);
  const reply = await Api.turn(state.sessionId, answer);
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
  state.sessionId = null;
  byId("home-input").value = "";
  show("home");
}

// ----- Wiring -----

byId("home-form").addEventListener("submit", (event) => {
  event.preventDefault();
  beginTopic(byId("home-input").value);
});

byId("talk-form").addEventListener("submit", (event) => {
  event.preventDefault();
  sendAnswer(byId("talk-input").value);
});

byId("new-topic").addEventListener("click", backHome);
byId("start-over").addEventListener("click", backHome);

startHome();
