// Calls to our own server. The browser never talks to Sarvam or OpenRouter,
// and never sees a key.

const Api = {
  // Every call gives back {ok, status, data}. It never throws for a server
  // reply, so the page can always show plain words instead of a raw error.
  async send(method, path, body) {
    const options = { method, cache: "no-store", headers: {} };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    try {
      const reply = await fetch(path, options);
      let data = {};
      try {
        data = await reply.json();
      } catch (error) {
        data = {};
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
  start(topicText, voice) {
    return Api.send("POST", "/api/session/start", { topic_text: topicText, voice });
  },

  // The learner has answered.
  turn(sessionId, transcript, flags) {
    return Api.send("POST", "/api/session/" + sessionId + "/turn", {
      transcript,
      heard_ok: true,
      ...(flags || {}),
    });
  },
};
