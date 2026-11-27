// Calls to our own server. The browser never talks to Sarvam or OpenRouter,
// and never sees a key.

const Api = {
  // Which features are on: {judging, speech, live_demo_url, video_url}
  async config() {
    const reply = await fetch("/api/config", { cache: "no-store" });
    if (!reply.ok) {
      throw new Error("config failed: " + reply.status);
    }
    return reply.json();
  },
};
