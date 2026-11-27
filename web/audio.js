// The recorder and the player.
//
// Recorder: records the learner's voice and hands it over in pieces. The
// speech service takes at most 30 seconds at a time, so a new piece starts at
// a pause after about 20 seconds (28 at the latest). Each piece is a complete
// little recording that can be transcribed while the learner keeps talking.
//
// Recording stops on a second tap, after 4 seconds of silence once the
// learner has spoken, or after 90 seconds.

const Recorder = {
  active: false,
  _stream: null,
  _context: null,
  _recorder: null,
  _timer: null,
  _options: null,
  _state: null,

  supported() {
    return Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
  },

  // The recording format this browser can make. Chrome makes WebM, Safari MP4.
  _mimeType() {
    const choices = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
    return choices.find((type) => MediaRecorder.isTypeSupported(type)) || "";
  },

  // options: {onPiece(blob), onStop(reason, heardVoice), onLevel(0..1),
  //           maxSeconds, silenceSeconds}
  // Throws if the mic is refused or missing.
  async start(options) {
    if (this.active) return;
    this._options = { maxSeconds: 90, silenceSeconds: 4, ...options };
    this._stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 },
    });
    this.active = true;

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this._context = new AudioContextClass();
    if (this._context.state === "suspended") {
      // Some phones start the sound meter paused.
      await this._context.resume().catch(() => {});
    }
    const analyser = this._context.createAnalyser();
    analyser.fftSize = 1024;
    this._context.createMediaStreamSource(this._stream).connect(analyser);
    const samples = new Float32Array(analyser.fftSize);

    const now = performance.now();
    this._state = {
      startedAt: now,
      pieceStartedAt: now,
      lastVoiceAt: now,
      heardVoice: false,
      meterWorks: false, // becomes true once the sound meter shows any signal
      noiseFloor: 0.01,
      reason: "",
    };
    this._startPiece();

    this._timer = setInterval(() => {
      analyser.getFloatTimeDomainData(samples);
      let sum = 0;
      for (const value of samples) sum += value * value;
      const level = Math.sqrt(sum / samples.length);
      this._tick(level);
    }, 100);
  },

  _tick(level) {
    const state = this._state;
    const options = this._options;
    const now = performance.now();

    // Learn the room's background noise in the first half second.
    if (now - state.startedAt < 500) {
      state.noiseFloor = Math.max(state.noiseFloor, level);
    }
    if (level > 0) state.meterWorks = true;
    const speaking = level > Math.max(0.015, state.noiseFloor * 2.5);
    if (speaking) {
      state.lastVoiceAt = now;
      state.heardVoice = true;
    }
    if (options.onLevel) options.onLevel(Math.min(1, level * 8));

    const quietFor = (now - state.lastVoiceAt) / 1000;
    const total = (now - state.startedAt) / 1000;
    if (state.heardVoice && quietFor >= options.silenceSeconds) return this.stop("silence");
    // If the meter reads nothing at all, it is broken on this device. Then we
    // cannot detect silence, so keep recording until the learner taps again.
    if (!state.heardVoice && state.meterWorks && total >= 8) return this.stop("nothing");
    if (total >= options.maxSeconds) return this.stop("max");

    // Start a new piece at a pause, so words are not cut in half.
    const pieceAge = (now - state.pieceStartedAt) / 1000;
    const atPause = quietFor >= 0.35;
    if ((pieceAge >= 20 && atPause) || pieceAge >= 28) {
      this._recorder.stop(); // its onstop starts the next piece
    }
    return undefined;
  },

  _startPiece() {
    const mimeType = this._mimeType();
    const recorder = new MediaRecorder(this._stream, mimeType ? { mimeType } : undefined);
    const chunks = [];
    recorder.ondataavailable = (event) => {
      if (event.data && event.data.size) chunks.push(event.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: recorder.mimeType || mimeType || "audio/webm" });
      if (blob.size && this._options.onPiece) this._options.onPiece(blob);
      if (this.active) {
        this._startPiece();
      } else {
        this._finish();
      }
    };
    this._recorder = recorder;
    this._state.pieceStartedAt = performance.now();
    recorder.start();
  },

  stop(reason) {
    if (!this.active) return;
    this.active = false;
    this._state.reason = reason || "tap";
    clearInterval(this._timer);
    if (this._recorder && this._recorder.state !== "inactive") {
      this._recorder.stop(); // onstop hands over the last piece, then finishes
    } else {
      this._finish();
    }
  },

  _finish() {
    for (const track of this._stream.getTracks()) track.stop();
    if (this._context) this._context.close();
    const { reason, heardVoice, meterWorks } = this._state;
    // With a broken meter, let the transcript decide whether anything was said.
    if (this._options.onStop) this._options.onStop(reason, heardVoice || !meterWorks);
  },
};

// Player: plays the tutor's spoken replies. Phones only allow sound after a
// tap, so the one audio element is "unlocked" on the learner's first tap.
const Player = {
  _audio: new Audio(),
  _unlocked: false,
  _url: null,

  unlock() {
    if (this._unlocked) return;
    this._unlocked = true;
    // A tiny silent clip, so later replies are allowed to play.
    this._audio.src =
      "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA=";
    this._audio.play().catch(() => {});
  },

  // Plays the audio and resolves when it ends (or cannot play).
  play(blob) {
    this.stop();
    this._url = URL.createObjectURL(blob);
    this._audio.src = this._url;
    return new Promise((resolve) => {
      this._audio.onended = resolve;
      this._audio.onerror = resolve;
      this._audio.play().catch(resolve);
    });
  },

  stop() {
    this._audio.pause();
    if (this._url) {
      URL.revokeObjectURL(this._url);
      this._url = null;
    }
  },
};
