class KidsVoiceChat {
  constructor() {
    this.character = "doro";
    this.language  = "english";
    this.recording = false;
    this.mediaRec  = null;
    this.chunks    = [];
    this.stream    = null;
    this.audio     = new Audio();
    this.busy      = false;
    this.init();
  }

  init() {
    this.injectUI();
    this.setCharacter("doro");
  }

  injectUI() {
    const container = document.createElement("div");
    container.id = "kids-voice-ui";
    container.innerHTML = `
      <style>
        #kids-voice-ui {
          position: fixed; bottom: 0; left: 0; right: 0;
          background: #fff; border-top: 2px solid #f0f0f0;
          padding: 16px 20px 24px;
          box-shadow: 0 -4px 24px rgba(0,0,0,0.08);
          z-index: 999;
          font-family: sans-serif;
        }
        #kv-lang-row {
          display: flex; gap: 8px; justify-content: center;
          margin-bottom: 14px; flex-wrap: wrap;
        }
        .kv-lang-btn {
          padding: 5px 14px; border-radius: 20px;
          border: 2px solid #e0e0e0; background: #fafafa;
          font-size: 13px; cursor: pointer; font-weight: 600;
        }
        .kv-lang-btn.active { background: #667EEA; color: #fff; border-color: #667EEA; }
        #kv-transcript {
          min-height: 48px; background: #f8f8ff;
          border-radius: 16px; padding: 10px 16px;
          font-size: 15px; color: #444; margin-bottom: 14px;
          text-align: center; border: 1.5px solid #e8e8ff;
        }
        #kv-mic-row { display: flex; justify-content: center; }
        #kv-mic-btn {
          width: 80px; height: 80px; border-radius: 50%;
          border: none; cursor: pointer; font-size: 36px;
          display: flex; align-items: center; justify-content: center;
          box-shadow: 0 4px 16px rgba(0,0,0,0.15);
          background: linear-gradient(135deg, #667EEA, #764BA2);
          color: white;
        }
        #kv-mic-btn.recording {
          background: linear-gradient(135deg, #f7971e, #ffd200);
          animation: pulse 0.8s infinite;
        }
        #kv-mic-btn.thinking { background: #aaa; }
        #kv-mic-btn.speaking { background: linear-gradient(135deg, #11998e, #38ef7d); }
        @keyframes pulse {
          0%,100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
        #kv-hint { text-align: center; font-size: 13px; color: #999; margin-top: 8px; }
        #kv-log {
          max-height: 120px; overflow-y: auto;
          margin-bottom: 12px; display: flex;
          flex-direction: column; gap: 8px;
        }
        .kv-bubble {
          padding: 8px 14px; border-radius: 16px;
          font-size: 14px; max-width: 85%;
        }
        .kv-bubble.kid { background: #EEF0FF; align-self: flex-end; }
        .kv-bubble.ai  { background: #E8FDF5; align-self: flex-start; }
      </style>

      <div id="kv-log"></div>
      <div id="kv-lang-row">
        <button class="kv-lang-btn active" data-lang="english">English</button>
        <button class="kv-lang-btn" data-lang="hindi">हिंदी</button>
        <button class="kv-lang-btn" data-lang="telugu">తెలుగు</button>
        <button class="kv-lang-btn" data-lang="tamil">தமிழ்</button>
      </div>
      <div id="kv-transcript">Click mic to start talking! 🎙️</div>
      <div id="kv-mic-row">
        <button id="kv-mic-btn">🎙️</button>
      </div>
      <p id="kv-hint">Click once to START · Click again to STOP</p>
    `;
    document.body.appendChild(container);

    document.querySelectorAll(".kv-lang-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".kv-lang-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.language = btn.dataset.lang;
      });
    });

    document.getElementById("kv-mic-btn").addEventListener("click", () => {
      if (this.busy) return;
      if (!this.recording) {
        this.startRecording();
      } else {
        this.stopRecording();
      }
    });
  }

  async startRecording() {
    try {
      this.stream  = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/mp4";
      this.mediaRec = new MediaRecorder(this.stream, { mimeType });
      this.chunks   = [];
      this.mediaRec.ondataavailable = e => { if (e.data.size > 0) this.chunks.push(e.data); };
      this.mediaRec.onstop = () => this.sendAudio();
      this.mediaRec.start();
      this.recording = true;
      this.setMicState("recording");
      this.setTranscript("🔴 Listening... Click mic to stop!");
      this.setHint("Click mic to STOP recording");
    } catch(err) {
      alert("Please allow microphone access!");
    }
  }

  stopRecording() {
    if (this.mediaRec && this.recording) {
      this.mediaRec.stop();
      this.stream?.getTracks().forEach(t => t.stop());
      this.recording = false;
    }
  }

  async sendAudio() {
    if (this.chunks.length === 0) return;
    this.busy = true;
    const mimeType = this.mediaRec.mimeType;
    const blob = new Blob(this.chunks, { type: mimeType });
    const filename = mimeType.includes("webm") ? "recording.webm" : "recording.mp4";
    const formData = new FormData();
    formData.append("audio", blob, filename);
    formData.append("character", this.character);
    formData.append("language", this.language);

    this.setMicState("thinking");
    this.setTranscript("🤔 Thinking...");
    this.setHint("Please wait...");

    try {
      const response = await fetch("/api/kids/converse", { method: "POST", body: formData });
      if (!response.ok) throw new Error("Server error");

      const kidSaid   = decodeURIComponent(response.headers.get("X-Kid-Said") || "");
      const aiReplied = decodeURIComponent(response.headers.get("X-AI-Replied") || "");

      if (kidSaid)   this.addBubble(kidSaid, "kid");
      if (aiReplied) this.addBubble(aiReplied, "ai");
      this.setTranscript(aiReplied || "✨");

      const audioBlob = await response.blob();
      const audioUrl  = URL.createObjectURL(audioBlob);
      this.audio.src  = audioUrl;
      this.setMicState("speaking");
      this.setHint("🔊 Speaking...");
      await this.audio.play();
      this.audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        this.setMicState("idle");
        this.setHint("Click once to START · Click again to STOP");
        this.busy = false;
      };
    } catch(err) {
      console.error(err);
      this.setTranscript("Oops! Something went wrong. Try again! 😅");
      this.setMicState("idle");
      this.setHint("Click once to START · Click again to STOP");
      this.busy = false;
    }
  }

  setMicState(state) {
    const btn = document.getElementById("kv-mic-btn");
    const icons = { idle: "🎙️", recording: "🔴", thinking: "⏳", speaking: "🔊" };
    btn.className = state;
    btn.textContent = icons[state] || "🎙️";
  }

  setTranscript(text) { document.getElementById("kv-transcript").textContent = text; }
  setHint(text)       { document.getElementById("kv-hint").textContent = text; }

  addBubble(text, who) {
    const log = document.getElementById("kv-log");
    const div = document.createElement("div");
    div.className = `kv-bubble ${who}`;
    div.textContent = text;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }

  setCharacter(char) {
    this.character = char;
    const avatars = { doro: "🤖", chintu: "😄", bheemu: "💪" };
    this.setTranscript(`${avatars[char]} Ready! Click mic to talk!`);
    document.getElementById("kv-log").innerHTML = "";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  window.kidsVoice = new KidsVoiceChat();
  document.querySelectorAll(".char-card").forEach(card => {
    card.addEventListener("click", () => {
      window.kidsVoice.setCharacter(card.dataset.character);
    });
  });
});
