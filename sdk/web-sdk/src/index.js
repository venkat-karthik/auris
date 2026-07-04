/**
 * Auris Voice SDK - Client Library
 * Handles real-time bidirectional voice communication with Auris backend via WebSockets.
 */

export class AurisVoiceClient {
  /**
   * @param {Object} options
   * @param {string} options.baseUrl - Backend base URL (e.g. "wss://api.auris.ai" or "ws://localhost:8000")
   * @param {number|string} options.agentId - ID of the Auris Virtual Agent
   * @param {string} options.token - Authentication JWT token
   * @param {string} [options.callerNumber] - Optional caller phone or identifier
   * @param {number} [options.sampleRate=16000] - Target PCM audio sample rate (default 16000 Hz)
   */
  constructor({ baseUrl, agentId, token, callerNumber = null, sampleRate = 16000 }) {
    this.baseUrl = baseUrl.replace(/^http/, 'ws').replace(/\/$/, '');
    this.agentId = agentId;
    this.token = token;
    this.callerNumber = callerNumber;
    this.sampleRate = sampleRate;

    this.ws = null;
    this.audioContext = null;
    this.mediaStream = null;
    this.micSource = null;
    this.scriptProcessor = null;

    // Audio playback state
    this.activeSources = new Set();
    this.isPlaying = false;
    this.nextPlayTime = 0;

    // Transcript history buffer (keeps last 10 turns)
    this.transcriptHistory = [];

    // Event listeners
    this.listeners = {
      start: [],
      audio: [],
      transcript: [],
      interrupted: [],
      end: [],
      error: [],
      volume: [],
      agent_start_talking: [],
      agent_stop_talking: []
    };

    this.connected = false;
    this.muted = false;
  }

  /**
   * Register event listener.
   * @param {string} event - Event name ('start', 'audio', 'transcript', 'interrupted', 'end', 'error', 'volume')
   * @param {Function} callback - Handler function
   */
  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
    return this;
  }

  /**
   * Emit event to registered listeners.
   */
  _emit(event, payload) {
    if (this.listeners[event]) {
      this.listeners[event].forEach((cb) => {
        try {
          cb(payload);
        } catch (err) {
          console.error(`Error in handler for event '${event}':`, err);
        }
      });
    }
  }

  /**
   * Start the voice call. Requests microphone permission and opens WebSocket.
   */
  async start(context = {}) {
    if (this.connected) {
      throw new Error("Call is already active.");
    }

    try {
      // Initialize AudioContext
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();

      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      // Connect WebSocket
      const query = new URLSearchParams({ token: this.token });
      if (this.callerNumber) {
        query.set("caller_number", this.callerNumber);
      }
      const wsUrl = `${this.baseUrl}/api/v1/calls/ws/${this.agentId}?${query.toString()}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = async () => {
        this.connected = true;
        // Send initial start signaling message
        this.ws.send(JSON.stringify({
          type: "start",
          context: context
        }));
        await this._setupMicrophoneCapture();
        this._emit("start", { agentId: this.agentId });
      };

      this.ws.onmessage = async (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          this._handleServerMessage(msg);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      this.ws.onerror = (err) => {
        this._emit("error", { message: "WebSocket connection error", error: err });
      };

      this.ws.onclose = (evt) => {
        this.stop();
      };
    } catch (err) {
      this._emit("error", { message: "Failed to start call", error: err });
      this.stop();
      throw err;
    }
  }

  /**
   * Setup microphone audio capture using modern AudioWorkletNode (with fallback to ScriptProcessorNode).
   */
  async _setupMicrophoneCapture() {
    if (!this.audioContext || !this.mediaStream) return;

    this.micSource = this.audioContext.createMediaStreamSource(this.mediaStream);

    try {
      if (this.audioContext.audioWorklet) {
        const workletCode = `
          class AurisAudioProcessor extends AudioWorkletProcessor {
            constructor() {
              super();
              this.bufferSize = 4096;
              this.buffer = new Float32Array(this.bufferSize);
              this.bytesWritten = 0;
            }
            process(inputs, outputs, parameters) {
              const input = inputs[0];
              if (!input || !input.length || !input[0].length) return true;
              const channelData = input[0];
              let sumSq = 0;
              for (let i = 0; i < channelData.length; i++) {
                sumSq += channelData[i] * channelData[i];
                this.buffer[this.bytesWritten++] = channelData[i];
                if (this.bytesWritten >= this.bufferSize) {
                  this.port.postMessage({
                    type: 'audio_chunk',
                    data: this.buffer.slice(0),
                    rms: Math.sqrt(sumSq / channelData.length)
                  });
                  this.bytesWritten = 0;
                  sumSq = 0;
                }
              }
              return true;
            }
          }
          registerProcessor('auris-audio-processor', AurisAudioProcessor);
        `;
        const blob = new Blob([workletCode], { type: 'application/javascript' });
        const workletUrl = URL.createObjectURL(blob);
        await this.audioContext.audioWorklet.addModule(workletUrl);
        URL.revokeObjectURL(workletUrl);

        this.workletNode = new AudioWorkletNode(this.audioContext, 'auris-audio-processor');
        this.workletNode.port.onmessage = (event) => {
          if (!this.connected || this.muted) return;
          const { data, rms } = event.data;
          this._emit("volume", { level: Math.min(1, rms * 5) });
          this._processAndSendAudio(data, this.audioContext.sampleRate);
        };

        this.micSource.connect(this.workletNode);
        this.workletNode.connect(this.audioContext.destination);
        return;
      }
    } catch (err) {
      console.warn("AudioWorklet initialization failed, falling back to ScriptProcessorNode:", err);
    }

    // Fallback to ScriptProcessorNode for older browser support
    const bufferSize = 4096;
    this.scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
    this.micSource.connect(this.scriptProcessor);
    this.scriptProcessor.connect(this.audioContext.destination);

    this.scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
      if (!this.connected || this.muted) return;

      const inputBuffer = audioProcessingEvent.inputBuffer;
      const inputData = inputBuffer.getChannelData(0);

      let sumSq = 0;
      for (let i = 0; i < inputData.length; i++) {
        sumSq += inputData[i] * inputData[i];
      }
      const rms = Math.sqrt(sumSq / inputData.length);
      this._emit("volume", { level: Math.min(1, rms * 5) });

      this._processAndSendAudio(inputData, inputBuffer.sampleRate);
    };
  }

  /**
   * Helper to resample, encode to Int16 PCM base64, and transmit over WebSocket.
   */
  _processAndSendAudio(inputData, sampleRate) {
    const resampled = this._resamplePCM(inputData, sampleRate, this.sampleRate);
    const pcm16 = new Int16Array(resampled.length);
    for (let i = 0; i < resampled.length; i++) {
      let s = Math.max(-1, Math.min(1, resampled[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    const bytes = new Uint8Array(pcm16.buffer);
    const base64 = this._bytesToBase64(bytes);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "audio",
        data: base64
      }));
    }
  }

  /**
   * Handle incoming messages from Auris backend.
   */
  async _handleServerMessage(msg) {
    switch (msg.type) {
      case "audio":
        if (msg.data) {
          this._queueAudioPlayback(msg.data);
          this._emit("audio", { length: msg.data.length });
        }
        break;

      case "transcript":
        const role = msg.role || "agent";
        const entry = {
          id: msg.id || Date.now().toString() + "-" + Math.random().toString(36).substr(2, 4),
          role: role,
          text: msg.text || "",
          final: !!msg.final,
          timestamp: new Date().toISOString()
        };

        if (entry.final) {
          this.transcriptHistory.push(entry);
          if (this.transcriptHistory.length > 10) {
            this.transcriptHistory.shift();
          }
        }

        this._emit("transcript", {
          ...entry,
          history: [...this.transcriptHistory]
        });
        break;

      case "interrupted":
        // User interrupted agent TTS; flush playback queue immediately
        this._flushAudioPlayback();
        this._emit("interrupted", {});
        break;

      case "end":
        this.stop();
        break;

      case "error":
        this._emit("error", { message: msg.message || "Unknown server error" });
        break;
    }
  }

  /**
   * Queue incoming Base64 PCM audio chunk for gapless playback scheduling.
   */
  _queueAudioPlayback(base64Data) {
    const bytes = this._base64ToBytes(base64Data);
    const int16 = new Int16Array(bytes.buffer);
    const float32 = new Float32Array(int16.length);

    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / (int16[i] < 0 ? 0x8000 : 0x7FFF);
    }

    if (!this.audioContext) return;

    const audioBuffer = this.audioContext.createBuffer(1, float32.length, this.sampleRate);
    audioBuffer.getChannelData(0).set(float32);

    this._scheduleBuffer(audioBuffer);
  }

  /**
   * Schedule audio buffer using precise AudioContext.currentTime timestamps for gapless playback.
   */
  _scheduleBuffer(audioBuffer) {
    if (!this.audioContext) return;

    if (!this.isPlaying) {
      this.isPlaying = true;
      this._emit("agent_start_talking", {});
    }

    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);

    const currentTime = this.audioContext.currentTime;
    if (this.nextPlayTime < currentTime) {
      this.nextPlayTime = currentTime;
    }

    source.start(this.nextPlayTime);
    this.nextPlayTime += audioBuffer.duration;

    this.activeSources.add(source);

    source.onended = () => {
      this.activeSources.delete(source);
      if (this.activeSources.size === 0) {
        this.isPlaying = false;
        this._emit("agent_stop_talking", {});
      }
    };
  }

  /**
   * Flush audio playback queue immediately (used during interruptions).
   */
  _flushAudioPlayback() {
    this.nextPlayTime = 0;
    if (this.activeSources && this.activeSources.size > 0) {
      this.activeSources.forEach(source => {
        try {
          source.onended = null; // Prevent onended from firing during flush
          source.stop();
        } catch (e) {
          // Ignore if already stopped
        }
      });
      this.activeSources.clear();
    }
    if (this.isPlaying) {
      this.isPlaying = false;
      this._emit("agent_stop_talking", {});
    }
  }

  /**
   * Mute or unmute the microphone.
   */
  setMuted(muted) {
    this.muted = !!muted;
    if (this.mediaStream) {
      this.mediaStream.getAudioTracks().forEach(track => {
        track.enabled = !this.muted;
      });
    }
  }

  /**
   * Send a DTMF digit to the agent.
   */
  sendDTMF(digit) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "dtmf",
        digit: String(digit)
      }));
    }
  }

  /**
   * Stop the call and clean up audio resources.
   */
  stop() {
    const wasConnected = this.connected;
    this.connected = false;

    this._flushAudioPlayback();

    if (this.workletNode) {
      this.workletNode.disconnect();
      this.workletNode = null;
    }
    if (this.scriptProcessor) {
      this.scriptProcessor.disconnect();
      this.scriptProcessor = null;
    }
    if (this.micSource) {
      this.micSource.disconnect();
      this.micSource = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      this.ws.send(JSON.stringify({ type: "end" }));
      this.ws.close();
      this.ws = null;
    }

    if (wasConnected) {
      this._emit("end", {});
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  _resamplePCM(audioData, origSampleRate, targetSampleRate) {
    if (origSampleRate === targetSampleRate) {
      return audioData;
    }
    const ratio = origSampleRate / targetSampleRate;
    const newLen = Math.round(audioData.length / ratio);
    const result = new Float32Array(newLen);
    for (let i = 0; i < newLen; i++) {
      result[i] = audioData[Math.floor(i * ratio)];
    }
    return result;
  }

  _bytesToBase64(bytes) {
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  _base64ToBytes(base64) {
    const binary = atob(base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }
}
