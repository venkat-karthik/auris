'use client';

import React, { useState, useEffect, useRef } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { AurisAPI, CallRun, Agent } from '@/lib/api';
import { AurisVoiceClient, TranscriptEntry } from '@/lib/voice-client';
import { useAuth } from '@/context/AuthContext';
import {
  PhoneCall,
  Play,
  Pause,
  Volume2,
  Clock,
  Sparkles,
  Bot,
  Filter,
  ArrowUpRight,
  PhoneForwarded,
  CheckCircle2,
  AlertCircle,
  FileText,
  Activity,
  Send,
  Radio,
  Mic,
  MicOff,
  PhoneOff
} from 'lucide-react';

// Clean database state initialization. No mock calls or mock transcripts definition.

export default function CallsPage() {
  const { activeOrg } = useAuth();
  const [calls, setCalls] = useState<CallRun[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedCall, setSelectedCall] = useState<CallRun | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<number | null>(null);

  // Dispatch & WebRTC Modal
  const [showDispatchModal, setShowDispatchModal] = useState(false);
  const [callMode, setCallMode] = useState<'webrtc' | 'sip'>('webrtc');
  const [targetPhone, setTargetPhone] = useState('+1 (830) 982-7125');
  const [dispatchAgentId, setDispatchAgentId] = useState<number>(1);
  const [dispatching, setDispatching] = useState(false);

  // Active WebRTC Live Call State
  const [activeVoiceClient, setActiveVoiceClient] = useState<AurisVoiceClient | null>(null);
  const [isLiveCallActive, setIsLiveCallActive] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [micVolume, setMicVolume] = useState<number>(0);
  const [liveTranscripts, setLiveTranscripts] = useState<TranscriptEntry[]>([]);
  const [activeCallRunId, setActiveCallRunId] = useState<number | null>(null);

  useEffect(() => {
    async function fetchCalls() {
      try {
        const [callsData, agentsData] = await Promise.all([
          AurisAPI.calls.list(selectedAgentFilter || undefined, 50).catch(() => null),
          AurisAPI.agents.list().catch(() => null)
        ]);

        if (callsData && Array.isArray(callsData)) {
          setCalls(callsData);
          if (callsData.length > 0 && !selectedCall) {
            setSelectedCall(callsData[0]);
          }
        }
        if (agentsData && Array.isArray(agentsData)) {
          setAgents(agentsData);
          if (agentsData.length > 0) {
            setDispatchAgentId(agentsData[0].id);
          }
        }
      } catch (err) {
        console.warn('Call runs load error:', err);
      }
    }
    fetchCalls();
  }, [selectedAgentFilter]);

  const handleStartCallSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setDispatching(true);
    try {
      if (callMode === 'sip') {
        await AurisAPI.calls.dispatch(dispatchAgentId, targetPhone, { source: 'Frontend Simulator' });
        setShowDispatchModal(false);
        const callsRes = await AurisAPI.calls.list(selectedAgentFilter || undefined, 50).catch(() => null);
        if (callsRes && Array.isArray(callsRes)) {
          setCalls(callsRes);
          if (callsRes.length > 0) setSelectedCall(callsRes[0]);
        }
      } else {
        // Start Live WebRTC Browser Call
        const token = localStorage.getItem('auris_token') || 'dev_token';
        const webCallRes = await AurisAPI.calls.webCall(dispatchAgentId, 'Browser WebRTC Client').catch(() => null);
        const activeToken = webCallRes?.access_token || token;
        const callId = webCallRes?.call_id || Date.now();
        setActiveCallRunId(callId);

        const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';
        const client = new AurisVoiceClient({
          baseUrl,
          agentId: dispatchAgentId,
          token: activeToken,
          callerNumber: 'Browser WebRTC Client'
        });

        client.on('volume', ({ level }: { level: number }) => setMicVolume(level));
        client.on('transcript', (entry: TranscriptEntry & { history: TranscriptEntry[] }) => {
          setLiveTranscripts(entry.history || [entry]);
        });
        client.on('end', async () => {
          setIsLiveCallActive(false);
          setActiveVoiceClient(null);
          setMicVolume(0);
          if (callId) await AurisAPI.calls.end(callId).catch(() => null);
          const callsRes = await AurisAPI.calls.list(selectedAgentFilter || undefined, 50).catch(() => null);
          if (callsRes && Array.isArray(callsRes)) setCalls(callsRes);
        });
        client.on('error', (err: any) => {
          console.warn('Live WebRTC error:', err);
          alert(`Call interrupted or backend offline: ${err.message || 'Check microphone & server'}`);
          client.stop();
        });

        await client.start();
        setActiveVoiceClient(client);
        setIsLiveCallActive(true);
        setShowDispatchModal(false);
      }
    } catch (err: any) {
      console.warn('Session start failed:', err);
      alert(err.message || 'Failed to start call. Verify microphone permission and local server status.');
    } finally {
      setDispatching(false);
    }
  };

  const handleEndLiveCall = async () => {
    if (activeVoiceClient) {
      activeVoiceClient.stop();
      setActiveVoiceClient(null);
    }
    setIsLiveCallActive(false);
    setMicVolume(0);
    if (activeCallRunId) {
      await AurisAPI.calls.end(activeCallRunId).catch(() => null);
    }
    const callsRes = await AurisAPI.calls.list(selectedAgentFilter || undefined, 50).catch(() => null);
    if (callsRes && Array.isArray(callsRes)) setCalls(callsRes);
  };

  const toggleLiveMute = () => {
    if (activeVoiceClient) {
      const nextMute = !isMuted;
      activeVoiceClient.setMuted(nextMute);
      setIsMuted(nextMute);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-slate-900/90 via-indigo-950/30 to-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-xl">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3">
              <PhoneCall className="w-8 h-8 text-cyan-400 animate-pulse" />
              <span>Live Call Runs & Transcripts</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Real-time conversational logs, audio waveform playback, VAD metrics, and mid-call transcripts.
            </p>
          </div>

          <button
            onClick={() => setShowDispatchModal(true)}
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-sm shadow-xl shadow-indigo-500/25 transition-all transform hover:-translate-y-0.5 self-start sm:self-center"
          >
            <Send className="w-4 h-4" />
            <span>Launch Test Call</span>
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-cyan-400" />
              <span>Filter by Agent:</span>
            </span>
            <select
              value={selectedAgentFilter || ''}
              onChange={(e) => setSelectedAgentFilter(e.target.value ? Number(e.target.value) : null)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white font-semibold focus:outline-none focus:border-cyan-400"
            >
              <option value="">All Voice Agents</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>{a.name} ({a.tier})</option>
              ))}
              {!agents.length && <option value="1">Agent #1 — Inbound Reception</option>}
            </select>
          </div>

          <div className="text-xs text-slate-400">
            Showing <strong className="text-white">{calls.length}</strong> active & completed call runs
          </div>
        </div>

        {/* Main Viewport: Calls List + Transcript Inspector */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Feed */}
          <div className="lg:col-span-5 space-y-4 max-h-[calc(100vh-12rem)] overflow-y-auto pr-2">
            {calls.length === 0 ? (
              <div className="text-center py-12 rounded-3xl bg-slate-900/20 border border-dashed border-slate-800/80">
                <PhoneCall className="w-8 h-8 text-slate-600 mx-auto mb-3 animate-pulse" />
                <p className="text-sm font-semibold text-slate-400">No recent call runs found</p>
                <p className="text-xs text-slate-500 mt-1">Initiate a live run to view telephonic logs here.</p>
              </div>
            ) : (
              calls.map((call) => {
                const isSelected = selectedCall?.id === call.id;
                return (
                  <div
                    key={call.id}
                    onClick={() => setSelectedCall(call)}
                    className={`p-4 rounded-3xl border transition-all cursor-pointer flex flex-col gap-3 ${
                      isSelected
                        ? 'bg-gradient-to-r from-indigo-600/20 to-cyan-500/10 border-indigo-500/50 shadow-md shadow-indigo-500/10'
                        : 'bg-slate-900/50 hover:bg-slate-900/80 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${
                          call.direction === 'inbound'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-indigo-500/10 text-indigo-400'
                        }`}>
                          {call.direction === 'inbound' ? 'IN' : 'OUT'}
                        </div>
                        <div>
                          <p className="text-sm font-extrabold text-white leading-tight">{call.customer_number}</p>
                          <p className="text-[11px] text-slate-400 mt-0.5">Agent Trunk: {call.agent_number}</p>
                        </div>
                      </div>

                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        call.status === 'completed'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : call.status === 'voicemail'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 animate-pulse'
                      }`}>
                        {call.status}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 line-clamp-2 font-normal">{call.summary || 'Active session...'}</p>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        {call.duration_seconds ? `${call.duration_seconds}s` : 'Active'}
                      </span>
                      {call.sentiment && (
                        <span className="font-bold text-cyan-300">Sentiment: {call.sentiment}</span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Right Inspector & Waveform */}
          <div className="lg:col-span-7 glass-panel rounded-3xl p-6 flex flex-col justify-between space-y-6">
            {selectedCall ? (
              <div className="space-y-6">
                {/* Call Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-extrabold text-white">{selectedCall.customer_number}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">ID: {selectedCall.id}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                      <Bot className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Agent #{selectedCall.agent_id} — Sub-300ms Conversational Flow</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setIsPlaying(!isPlaying)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                        isPlaying
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20'
                      }`}
                    >
                      {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                      <span>{isPlaying ? 'Pause Audio' : 'Play Waveform'}</span>
                    </button>
                  </div>
                </div>

                {/* Simulated Waveform Player */}
                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 space-y-3">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                    <span className="flex items-center gap-2">
                      <Volume2 className="w-4 h-4 text-cyan-400 animate-pulse" />
                      <span>Audio Recording (16kHz PCM Mono)</span>
                    </span>
                    <span className="font-mono text-slate-400">
                      {isPlaying ? '01:14 / 02:22' : '00:00 / 02:22'}
                    </span>
                  </div>

                  {/* Waveform Bars */}
                  <div className="flex items-center justify-between h-10 gap-1 px-2 py-1 rounded-xl bg-slate-900 overflow-hidden">
                    {Array.from({ length: 48 }).map((_, idx) => {
                      const heights = [30, 45, 65, 85, 95, 75, 40, 20, 50, 80, 90, 60, 35, 70, 95, 80, 45, 25];
                      const h = heights[idx % heights.length];
                      return (
                        <div
                          key={idx}
                          style={{ height: `${isPlaying && idx % 3 === 0 ? Math.min(100, h + 15) : h}%` }}
                          className={`flex-1 rounded-full transition-all duration-300 ${
                            idx < 22 ? 'bg-gradient-to-t from-indigo-500 to-cyan-400' : 'bg-slate-800'
                          }`}
                        />
                      );
                    })}
                  </div>
                </div>

                {/* Summary & Key Topics */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">AI Post-Call Summary</h4>
                  <p className="text-xs text-slate-200 leading-relaxed bg-slate-900/60 p-4 rounded-2xl border border-slate-800 font-normal">
                    {selectedCall.summary || 'Summary generation processing...'}
                  </p>

                  {selectedCall.key_topics && (
                    <div className="flex items-center gap-2 flex-wrap pt-1">
                      <span className="text-xs font-bold text-slate-400">Key Topics:</span>
                      {selectedCall.key_topics.map((t, i) => (
                        <span key={i} className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                          #{t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Transcripts Feed */}
                <div className="space-y-3 pt-3 border-t border-slate-800">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Live Bidirectional Transcript Log</span>
                  </h4>

                  <div className="flex flex-col items-center justify-center py-12 text-slate-500 border border-slate-850/50 rounded-2xl bg-slate-900/10">
                    <FileText className="w-8 h-8 mb-2 text-slate-600 animate-pulse" />
                    <p className="text-xs font-semibold">Transcript: {selectedCall.transcript_path ? selectedCall.transcript_path.split('/').pop() : 'No raw path stored'}</p>
                    <p className="text-[10px] text-slate-600 mt-1 max-w-xs text-center">
                      {selectedCall.transcript_path 
                        ? 'The live audio transcript for this run has been archived in MinIO object storage.' 
                        : 'No transcription text has been populated for this run yet.'}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-20 text-slate-500 text-sm">Select any call run on the left to inspect waveforms and transcripts.</div>
            )}
          </div>
        </div>

        {/* Dispatch / WebRTC Mode Selection Modal */}
        {showDispatchModal && !isLiveCallActive && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
            <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Send className="w-4 h-4 text-cyan-400" />
                  <span>Launch Live Voice Session</span>
                </h3>
                <button onClick={() => setShowDispatchModal(false)} className="text-slate-400 hover:text-white font-bold text-sm">✕</button>
              </div>

              <form onSubmit={handleStartCallSession} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">Select Transport Mode</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setCallMode('webrtc')}
                      className={`p-3 rounded-2xl border text-left flex flex-col gap-1 transition-all ${
                        callMode === 'webrtc'
                          ? 'bg-gradient-to-br from-indigo-600/30 to-cyan-500/20 border-cyan-400 text-white shadow-md'
                          : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <span className="font-extrabold text-xs flex items-center gap-1.5 text-cyan-300">
                        <Mic className="w-3.5 h-3.5" />
                        <span>Browser Mic (WebRTC)</span>
                      </span>
                      <span className="text-[10px] leading-tight text-slate-400">Speak directly to agent via browser microphone.</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setCallMode('sip')}
                      className={`p-3 rounded-2xl border text-left flex flex-col gap-1 transition-all ${
                        callMode === 'sip'
                          ? 'bg-gradient-to-br from-indigo-600/30 to-cyan-500/20 border-indigo-400 text-white shadow-md'
                          : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <span className="font-extrabold text-xs flex items-center gap-1.5 text-indigo-300">
                        <PhoneForwarded className="w-3.5 h-3.5" />
                        <span>Outbound SIP Trunk</span>
                      </span>
                      <span className="text-[10px] leading-tight text-slate-400">Dispatch Telnyx/Twilio call to real phone number.</span>
                    </button>
                  </div>
                </div>

                {callMode === 'sip' && (
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">Target Customer Phone Number</label>
                    <input
                      type="text"
                      required
                      value={targetPhone}
                      onChange={(e) => setTargetPhone(e.target.value)}
                      placeholder="+1 (830) 982-7125"
                      className="w-full glass-input px-3.5 py-2.5 rounded-xl text-xs font-mono font-bold text-cyan-300"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">Select Voice Agent</label>
                  {agents.length === 0 ? (
                    <div className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-rose-400 font-semibold">
                      No voice agents available. Please create a voice agent first.
                    </div>
                  ) : (
                    <select
                      value={dispatchAgentId}
                      onChange={(e) => setDispatchAgentId(Number(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white font-semibold focus:outline-none focus:border-cyan-400"
                    >
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>{a.name} ({a.tier})</option>
                      ))}
                    </select>
                  )}
                </div>

                <div className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                  <p className="font-semibold text-slate-300 flex items-center gap-1">
                    <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                    <span>{callMode === 'webrtc' ? 'Live WebRTC 16kHz Audio Pipeline' : 'PSTN SIP Trunk Audio Engine'}</span>
                  </p>
                  <p>{callMode === 'webrtc' ? 'Establishes bidirectional sub-300ms audio stream with live voice activity detection (VAD).' : 'Dispatches SIP webhook to your Telnyx trunk configuration.'}</p>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button type="button" onClick={() => setShowDispatchModal(false)} className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold">Cancel</button>
                  <button type="submit" disabled={dispatching || agents.length === 0} className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-xs shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50">
                    {dispatching ? 'Connecting...' : callMode === 'webrtc' ? 'Connect Live Browser Call' : 'Dispatch SIP Call'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Active WebRTC Live Call Interactive Modal */}
        {isLiveCallActive && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
            <div className="w-full max-w-lg rounded-3xl bg-slate-900 border border-cyan-500/40 p-6 shadow-2xl shadow-cyan-500/10 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-emerald-400 animate-ping" />
                  <div>
                    <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                      <span>Live WebRTC Voice Session</span>
                    </h3>
                    <p className="text-[11px] text-cyan-300">Agent #{dispatchAgentId} • Sub-300ms Conversational Loop</p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-bold font-mono">
                  CONNECTED
                </span>
              </div>

              {/* Pulsing Audio Orb & Waveform Meter */}
              <div className="flex flex-col items-center justify-center py-8 bg-slate-950/80 rounded-3xl border border-slate-800/80 relative overflow-hidden">
                <div
                  style={{
                    transform: `scale(${1 + micVolume * 1.8})`,
                    opacity: 0.3 + micVolume * 0.7
                  }}
                  className="w-24 h-24 rounded-full bg-gradient-to-tr from-cyan-500 to-indigo-600 blur-md transition-all duration-75 flex items-center justify-center"
                />
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-20 h-20 rounded-full bg-slate-900 border-2 border-cyan-400 flex items-center justify-center shadow-lg">
                    {isMuted ? <MicOff className="w-8 h-8 text-rose-400" /> : <Mic className="w-8 h-8 text-cyan-300 animate-pulse" />}
                  </div>
                </div>
                <p className="text-xs font-semibold text-slate-400 mt-4 z-10">
                  {isMuted ? 'Microphone Muted' : 'Listening & Streaming Audio... Speak now'}
                </p>
              </div>

              {/* Real-time Bidirectional Transcript Stream */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Live Conversation Stream</span>
                </span>
                <div className="h-44 overflow-y-auto p-3.5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2.5 text-xs font-normal">
                  {liveTranscripts.length === 0 ? (
                    <p className="text-slate-500 italic text-center py-12">Conversation started. Say "Hello" to initiate dialogue with the agent...</p>
                  ) : (
                    liveTranscripts.map((t, idx) => (
                      <div
                        key={t.id || idx}
                        className={`p-2.5 rounded-xl ${
                          t.role === 'user'
                            ? 'bg-indigo-600/10 text-indigo-200 border border-indigo-500/20 ml-6'
                            : 'bg-slate-850 text-slate-200 border border-slate-800 mr-6'
                        }`}
                      >
                        <span className="font-extrabold text-[10px] uppercase tracking-wider block mb-0.5 text-cyan-400">
                          {t.role === 'user' ? 'You (Microphone)' : `Voice Agent #${dispatchAgentId}`}
                        </span>
                        <span>{t.text}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Call Control Buttons */}
              <div className="flex items-center justify-between gap-4 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={toggleLiveMute}
                  className={`flex-1 py-3 px-4 rounded-2xl font-bold text-xs flex items-center justify-center gap-2 transition-all ${
                    isMuted
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'bg-slate-800 hover:bg-slate-700 text-white'
                  }`}
                >
                  {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  <span>{isMuted ? 'Unmute Mic' : 'Mute Mic'}</span>
                </button>

                <button
                  type="button"
                  onClick={handleEndLiveCall}
                  className="flex-1 py-3 px-4 rounded-2xl font-bold text-xs flex items-center justify-center gap-2 bg-gradient-to-r from-rose-600 to-red-500 hover:from-rose-500 hover:to-red-400 text-white shadow-lg shadow-rose-500/25 transition-all"
                >
                  <PhoneOff className="w-4 h-4" />
                  <span>Disconnect Call</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
