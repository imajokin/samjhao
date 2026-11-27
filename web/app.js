// Home screen. Asks the server which keys are set and shows the right message.

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

function byId(id) {
  return document.getElementById(id);
}

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
  let config;
  try {
    config = await Api.config();
  } catch (error) {
    showNotice(NOTICES.down, null);
    return;
  }

  const notice = pickNotice(config);
  if (notice) {
    showNotice(notice, config);
    return;
  }

  // Both keys are set. The talking part is built in the next milestones.
  byId("notice").hidden = true;
  byId("mic-label").textContent = "Keys are set. The tutor is being built.";
}

startHome();
