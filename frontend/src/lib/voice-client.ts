/**
 * Auris Voice SDK - TypeScript Client Library
 * Handles real-time bidirectional voice communication with Auris backend via WebSockets.
 */

export interface TranscriptEntry {
  id: string;
  role: 'user' | 'agent';
  text: string;
  final: boolean;
  timestamp: string;
}

export class AurisVoiceClient {
  baseUrl: string;
  agentId: number | string;
  token: string;
  callerNumber: string | null;
  sampleRate: number;

  ws: WebSocket | null = null;
  audioContext: AudioContext | null = null;
  mediaStream: MediaStream | null = null;
  micSource: MediaStreamAudioSourceNode | null = null;
  scriptProcessor: ScriptProcessorNode | null = null;
  workletNode: AudioWorkletNode | null = null;

  activeSources: Set<AudioBufferSourceNode> = new Set();
  isPlaying: boolean = false;
  nextPlayTime: number = 0;
  transcriptHistory: TranscriptEntry[] = [];
  listeners: { [key: string]: Function[] } = {
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
  connected: boolean = false;
  muted: boolean = false;

  constructor(options: {
    baseUrl: string;
    agentId: number | string;
    token: string;
    callerNumber?: string | null;
    sampleRate?: number;
  }) {
    this.baseUrl = options.baseUrl.replace(/^http/, 'ws').replace(/\/$/, '');
    this.agentId = options.agentId;
    this.token = options.token;
    this.callerNumber = options.callerNumber || null;
    this.sampleRate = options.sampleRate || 16000;
  }

  on(event: string, callback: Function): this {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
    return this;
  }

  _emit(event: string, payload: any) {
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

  async start(context: any = {}) {
    if (this.connected) {
      throw new Error('Call is already active.');
    }

    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioCtx();

      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      const query = new URLSearchParams({ token: this.token });
      if (this.callerNumber) {
        query.set('caller_number', this.callerNumber);
      }
      const wsUrl = `${this.baseUrl}/api/v1/calls/ws/${this.agentId}?${query.toString()}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = async () => {
        this.connected = true;
        this.ws?.send(
          JSON.stringify({
            type: 'start',
            context: context
          })
        );
        await this._setupMicrophoneCapture();
        this._emit('start', { agentId: this.agentId });
      };

      this.ws.onmessage = async (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          this._handleServerMessage(msg);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      this.ws.onerror = (err) => {
        this._emit('error', { message: 'WebSocket connection error', error: err });
      };

      this.ws.onclose = () => {
        this.stop();
      };
    } catch (err) {
      this._emit('error', { message: 'Failed to start call', error: err });
      this.stop();
      throw err;
    }
  }

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
          if (!this.connected || this.muted || !this.audioContext) return;
          const { data, rms } = event.data;
          this._emit('volume', { level: Math.min(1, rms * 5) });
          this._processAndSendAudio(data, this.audioContext.sampleRate);
        };

        this.micSource.connect(this.workletNode);
        this.workletNode.connect(this.audioContext.destination);
        return;
      }
    } catch (err) {
      console.warn('AudioWorklet initialization failed, falling back to ScriptProcessorNode:', err);
    }

    const bufferSize = 4096;
    this.scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
    this.micSource.connect(this.scriptProcessor);
    this.scriptProcessor.connect(this.audioContext.destination);

    this.scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
      if (!this.connected || this.muted || !this.audioContext) return;

      const inputBuffer = audioProcessingEvent.inputBuffer;
      const inputData = inputBuffer.getChannelData(0);

      let sumSq = 0;
      for (let i = 0; i < inputData.length; i++) {
        sumSq += inputData[i] * inputData[i];
      }
      const rms = Math.sqrt(sumSq / inputData.length);
      this._emit('volume', { level: Math.min(1, rms * 5) });

      this._processAndSendAudio(inputData, inputBuffer.sampleRate);
    };
  }

  _processAndSendAudio(inputData: Float32Array, sampleRate: number) {
    const resampled = this._resamplePCM(inputData, sampleRate, this.sampleRate);
    const pcm16 = new Int16Array(resampled.length);
    for (let i = 0; i < resampled.length; i++) {
      let s = Math.max(-1, Math.min(1, resampled[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    const bytes = new Uint8Array(pcm16.buffer);
    const base64 = this._bytesToBase64(bytes);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: 'audio',
          data: base64
        })
      );
    }
  }

  async _handleServerMessage(msg: any) {
    switch (msg.type) {
      case 'audio':
        if (msg.data) {
          this._queueAudioPlayback(msg.data);
          this._emit('audio', { length: msg.data.length });
        }
        break;

      case 'transcript':
        const role = msg.role || 'agent';
        const entry: TranscriptEntry = {
          id: msg.id || Date.now().toString() + '-' + Math.random().toString(36).substr(2, 4),
          role: role,
          text: msg.text || '',
          final: !!msg.final,
          timestamp: new Date().toISOString()
        };

        if (entry.final) {
          this.transcriptHistory.push(entry);
          if (this.transcriptHistory.length > 10) {
            this.transcriptHistory.shift();
          }
        }

        this._emit('transcript', {
          ...entry,
          history: [...this.transcriptHistory]
        });
        break;

      case 'interrupted':
        this._flushAudioPlayback();
        this._emit('interrupted', {});
        break;

      case 'end':
        this.stop();
        break;

      case 'error':
        this._emit('error', { message: msg.message || 'Unknown server error' });
        break;
    }
  }

  _queueAudioPlayback(base64Data: string) {
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

  _scheduleBuffer(audioBuffer: AudioBuffer) {
    if (!this.audioContext) return;

    if (!this.isPlaying) {
      this.isPlaying = true;
      this._emit('agent_start_talking', {});
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
        this._emit('agent_stop_talking', {});
      }
    };
  }

  _flushAudioPlayback() {
    this.nextPlayTime = 0;
    if (this.activeSources && this.activeSources.size > 0) {
      this.activeSources.forEach((source) => {
        try {
          source.onended = null;
          source.stop();
        } catch (e) {}
      });
      this.activeSources.clear();
    }
    if (this.isPlaying) {
      this.isPlaying = false;
      this._emit('agent_stop_talking', {});
    }
  }

  setMuted(muted: boolean) {
    this.muted = !!muted;
    if (this.mediaStream) {
      this.mediaStream.getAudioTracks().forEach((track) => {
        track.enabled = !this.muted;
      });
    }
  }

  sendDTMF(digit: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: 'dtmf',
          digit: String(digit)
        })
      );
    }
  }

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
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      this.ws.send(JSON.stringify({ type: 'end' }));
      this.ws.close();
      this.ws = null;
    }

    if (wasConnected) {
      this._emit('end', {});
    }
  }

  _resamplePCM(audioData: Float32Array, origSampleRate: number, targetSampleRate: number): Float32Array {
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

  _bytesToBase64(bytes: Uint8Array): string {
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  _base64ToBytes(base64: string): Uint8Array {
    const binary = atob(base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }
}
