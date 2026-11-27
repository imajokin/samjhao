// Calls to our own server. The browser never talks to Sarvam or OpenRouter,
// and never sees a key.

const Api = {
  // Every call gives back {ok, status, data}. It never throws for a server
  // reply, so the page can always show plain words instead of a raw error.
  async send(method, path, body) {
    const options = { method, cache: "no-store", headers: {} };
    if (body instanceof Blob) {
      options.headers["Content-Type"] = body.type || "audio/webm";
      options.body = body;
    } else if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    try {
      const reply = await fetch(path, options);
      const type = reply.headers.get("content-type") || "";
      let data = {};
      if (type.startsWith("audio/")) {
        data = await reply.blob();
      } else {
        try {
          data = await reply.json();
        } catch (error) {
          data = {};
        }
      }
      return { ok: reply.ok, status: reply.status, data };
    } catch (error) {
      return { ok: false, status: 0, data: { error: "network" } };
    }
  },

  // Which features are on: {judging, speech, live_demo_url, video_url, phrases}
  config() {
    return Api.send("GET", "/api/config");
  },

  // The learner has said a topic.
  start(topicText, voice, languageCode, level) {
    return Api.send("POST", "/api/session/start", {
      topic_text: topicText,
      level: level || "",
      voice,
      language_code: languageCode || "",
    });
  },

  // The learner has answered. flags: {heard_ok, silent, redo}
  turn(sessionId, transcript, flags) {
    return Api.send("POST", "/api/session/" + sessionId + "/turn", {
      transcript,
      heard_ok: true,
      ...(flags || {}),
    });
  },

  // The learner asked to jump straight to the full explanation.
  finish(sessionId) {
    return Api.send("POST", "/api/session/" + sessionId + "/finish", {});
  },

  // The full explanation and diagram, once the session has finished.
  recap(sessionId) {
    return Api.send("GET", "/api/session/" + sessionId + "/recap");
  },

  // One piece of recorded audio -> {transcript, language_code}
  transcribe(blob) {
    return Api.send("POST", "/api/transcribe", blob);
  },

  // Text -> spoken audio (a Blob)
  speak(text, lang, voice) {
    return Api.send("POST", "/api/speak", { text, lang, voice });
  },
};
