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
    this.playbackQueue = [];
    this.isPlaying = false;
    this.activeSourceNode = null;

    // Event listeners
    this.listeners = {
      start: [],
      audio: [],
      transcript: [],
      interrupted: [],
      end: [],
      error: [],
      volume: []
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

      this.ws.onopen = () => {
        this.connected = true;
        // Send initial start signaling message
        this.ws.send(JSON.stringify({
          type: "start",
          context: context
        }));
        this._setupMicrophoneCapture();
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
   * Setup microphone audio capture, downsampling to 16kHz PCM mono.
   */
  _setupMicrophoneCapture() {
    if (!this.audioContext || !this.mediaStream) return;

    this.micSource = this.audioContext.createMediaStreamSource(this.mediaStream);
    const bufferSize = 4096;
    this.scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

    this.micSource.connect(this.scriptProcessor);
    this.scriptProcessor.connect(this.audioContext.destination);

    this.scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
      if (!this.connected || this.muted) return;

      const inputBuffer = audioProcessingEvent.inputBuffer;
      const inputData = inputBuffer.getChannelData(0);

      // Calculate audio volume / level for visualizer
      let sumSq = 0;
      for (let i = 0; i < inputData.length; i++) {
        sumSq += inputData[i] * inputData[i];
      }
      const rms = Math.sqrt(sumSq / inputData.length);
      this._emit("volume", { level: Math.min(1, rms * 5) });

      // Resample to target sample rate (16000 Hz)
      const resampled = this._resamplePCM(inputData, inputBuffer.sampleRate, this.sampleRate);
      
      // Convert Float32 to Int16 PCM bytes
      const pcm16 = new Int16Array(resampled.length);
      for (let i = 0; i < resampled.length; i++) {
        let s = Math.max(-1, Math.min(1, resampled[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      // Base64 encode PCM bytes
      const bytes = new Uint8Array(pcm16.buffer);
      const base64 = this._bytesToBase64(bytes);

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: "audio",
          data: base64
        }));
      }
    };
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
        this._emit("transcript", {
          text: msg.text || "",
          final: !!msg.final
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
   * Queue incoming Base64 PCM audio chunk for seamless playback.
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

    this.playbackQueue.push(audioBuffer);
    if (!this.isPlaying) {
      this._playNextBuffer();
    }
  }

  /**
   * Play the next audio buffer from queue.
   */
  _playNextBuffer() {
    if (this.playbackQueue.length === 0 || !this.audioContext) {
      this.isPlaying = false;
      return;
    }

    this.isPlaying = true;
    const buffer = this.playbackQueue.shift();
    const source = this.audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(this.audioContext.destination);

    this.activeSourceNode = source;
    source.onended = () => {
      this.activeSourceNode = null;
      this._playNextBuffer();
    };

    source.start();
  }

  /**
   * Flush audio playback queue immediately (used during interruptions).
   */
  _flushAudioPlayback() {
    this.playbackQueue = [];
    if (this.activeSourceNode) {
      try {
        this.activeSourceNode.stop();
      } catch (e) {
        // Ignore if already stopped
      }
      this.activeSourceNode = null;
    }
    this.isPlaying = false;
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
