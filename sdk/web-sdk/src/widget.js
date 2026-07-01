/**
 * Auris Voice SDK - Embeddable Web Component Widget
 * Provides a drop-in floating UI for voice agent interaction.
 */

import { AurisVoiceClient } from "./index.js";

const STYLES = `
:host {
  --auris-primary: #6366f1;
  --auris-primary-glow: rgba(99, 102, 241, 0.5);
  --auris-bg: rgba(15, 23, 42, 0.85);
  --auris-border: rgba(255, 255, 255, 0.1);
  --auris-text: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 999999;
}

.widget-container {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.call-panel {
  display: none;
  width: 320px;
  background: var(--auris-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--auris-border);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  color: var(--auris-text);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  transform: translateY(10px);
  opacity: 0;
}

.call-panel.active {
  display: flex;
  flex-direction: column;
  transform: translateY(0);
  opacity: 1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 8px #22c55e;
}

.agent-title {
  font-size: 14px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 18px;
}

.orb-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
  margin: 12px 0;
}

.orb {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  box-shadow: 0 0 24px var(--auris-primary-glow);
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.transcript-box {
  min-height: 48px;
  max-height: 100px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 10px;
  font-size: 13px;
  line-height: 1.4;
  color: #cbd5e1;
  text-align: center;
  margin-bottom: 16px;
}

.controls {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-mute {
  background: rgba(255, 255, 255, 0.1);
  color: #f8fafc;
}

.btn-mute.muted {
  background: #eab308;
  color: #000;
}

.btn-end {
  background: #ef4444;
  color: #fff;
}

.btn-end:hover {
  background: #dc2626;
}

.launcher-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  border: none;
  box-shadow: 0 10px 25px var(--auris-primary-glow);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.launcher-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 14px 30px rgba(99, 102, 241, 0.7);
}

.launcher-icon {
  width: 24px;
  height: 24px;
}
`;

export class AurisVoiceWidget extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.client = null;
    this.isCallActive = false;
    this.isMuted = false;
  }

  static get observedAttributes() {
    return ["base-url", "agent-id", "token", "agent-name"];
  }

  connectedCallback() {
    this.render();
    this.setupListeners();
  }

  render() {
    const agentName = this.getAttribute("agent-name") || "Auris AI Assistant";
    this.shadowRoot.innerHTML = `
      <style>${STYLES}</style>
      <div class="widget-container">
        <div class="call-panel" id="panel">
          <div class="panel-header">
            <div class="agent-info">
              <span class="status-dot"></span>
              <span class="agent-title">${agentName}</span>
            </div>
            <button class="close-btn" id="close-btn">&times;</button>
          </div>
          <div class="orb-container">
            <div class="orb" id="orb"></div>
          </div>
          <div class="transcript-box" id="transcript">Ready to talk...</div>
          <div class="controls">
            <button class="btn btn-mute" id="mute-btn">Mute</button>
            <button class="btn btn-end" id="end-btn">End Call</button>
          </div>
        </div>
        <button class="launcher-btn" id="launcher" aria-label="Start Voice Call">
          <svg class="launcher-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" x2="12" y1="19" y2="22"></line>
          </svg>
        </button>
      </div>
    `;
  }

  setupListeners() {
    const launcher = this.shadowRoot.getElementById("launcher");
    const closeBtn = this.shadowRoot.getElementById("close-btn");
    const endBtn = this.shadowRoot.getElementById("end-btn");
    const muteBtn = this.shadowRoot.getElementById("mute-btn");

    launcher.addEventListener("click", () => this.toggleCall());
    closeBtn.addEventListener("click", () => this.stopCall());
    endBtn.addEventListener("click", () => this.stopCall());
    muteBtn.addEventListener("click", () => this.toggleMute());
  }

  async toggleCall() {
    if (this.isCallActive) {
      this.stopCall();
    } else {
      await this.startCall();
    }
  }

  async startCall() {
    const baseUrl = this.getAttribute("base-url") || window.location.origin;
    const agentId = this.getAttribute("agent-id");
    const token = this.getAttribute("token");

    if (!agentId || !token) {
      this.updateTranscript("Missing agent-id or token attribute.");
      return;
    }

    const panel = this.shadowRoot.getElementById("panel");
    const launcher = this.shadowRoot.getElementById("launcher");
    const orb = this.shadowRoot.getElementById("orb");

    panel.classList.add("active");
    launcher.style.display = "none";
    this.updateTranscript("Connecting...");

    this.client = new AurisVoiceClient({ baseUrl, agentId, token });

    this.client.on("start", () => {
      this.isCallActive = true;
      this.updateTranscript("Listening...");
    });

    this.client.on("volume", ({ level }) => {
      const scale = 1 + level * 0.5;
      orb.style.transform = `scale(${scale})`;
    });

    this.client.on("transcript", ({ text }) => {
      if (text) this.updateTranscript(text);
    });

    this.client.on("interrupted", () => {
      this.updateTranscript("Listening...");
    });

    this.client.on("end", () => {
      this.handleCallEnded();
    });

    this.client.on("error", ({ message }) => {
      this.updateTranscript(`Error: ${message}`);
    });

    try {
      await this.client.start();
    } catch (err) {
      this.updateTranscript("Connection failed.");
    }
  }

  stopCall() {
    if (this.client) {
      this.client.stop();
      this.client = null;
    }
    this.handleCallEnded();
  }

  handleCallEnded() {
    this.isCallActive = false;
    this.isMuted = false;
    const panel = this.shadowRoot.getElementById("panel");
    const launcher = this.shadowRoot.getElementById("launcher");
    const muteBtn = this.shadowRoot.getElementById("mute-btn");

    panel.classList.remove("active");
    launcher.style.display = "flex";
    muteBtn.classList.remove("muted");
    muteBtn.textContent = "Mute";
  }

  toggleMute() {
    if (!this.client) return;
    this.isMuted = !this.isMuted;
    this.client.setMuted(this.isMuted);

    const muteBtn = this.shadowRoot.getElementById("mute-btn");
    if (this.isMuted) {
      muteBtn.classList.add("muted");
      muteBtn.textContent = "Unmute";
    } else {
      muteBtn.classList.remove("muted");
      muteBtn.textContent = "Mute";
    }
  }

  updateTranscript(text) {
    const transcriptEl = this.shadowRoot.getElementById("transcript");
    if (transcriptEl) {
      transcriptEl.textContent = text;
    }
  }
}

if (!customElements.get("auris-voice-widget")) {
  customElements.define("auris-voice-widget", AurisVoiceWidget);
}
