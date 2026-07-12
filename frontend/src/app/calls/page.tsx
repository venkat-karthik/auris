'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { AurisAPI, CallRun, Agent } from '@/lib/api';
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
  Radio
} from 'lucide-react';

// Clean database state initialization. No mock calls or mock transcripts definition.

export default function CallsPage() {
  const { activeOrg } = useAuth();
  const [calls, setCalls] = useState<CallRun[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedCall, setSelectedCall] = useState<CallRun | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<number | null>(null);

  // Dispatch Call Modal
  const [showDispatchModal, setShowDispatchModal] = useState(false);
  const [targetPhone, setTargetPhone] = useState('+1 (830) 982-7125');
  const [dispatchAgentId, setDispatchAgentId] = useState<number>(1);
  const [dispatching, setDispatching] = useState(false);

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
        if (agentsData && Array.isArray(agentsData)) setAgents(agentsData);
      } catch (err) {
        console.warn('Call runs load error:', err);
      }
    }
    fetchCalls();
  }, [selectedAgentFilter]);

  const handleDispatchCall = async (e: React.FormEvent) => {
    e.preventDefault();
    setDispatching(true);
    try {
      await AurisAPI.calls.dispatch(dispatchAgentId, targetPhone, { source: 'Frontend Simulator' });
      setShowDispatchModal(false);
      // Reload calls
      const callsRes = await AurisAPI.calls.list(selectedAgentFilter || undefined, 50).catch(() => null);
      if (callsRes && Array.isArray(callsRes)) {
        setCalls(callsRes);
        if (callsRes.length > 0) {
          setSelectedCall(callsRes[0]);
        }
      }
    } catch (err) {
      console.warn('Dispatch failed:', err);
      alert('Failed to dispatch call. Please verify your telephony configs and live database connection.');
    } finally {
      setDispatching(false);
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

        {/* Dispatch Modal */}
        {showDispatchModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
            <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Send className="w-4 h-4 text-cyan-400" />
                  <span>Launch Simulated WebRTC / SIP Call</span>
                </h3>
                <button onClick={() => setShowDispatchModal(false)} className="text-slate-400 hover:text-white font-bold text-sm">✕</button>
              </div>

              <form onSubmit={handleDispatchCall} className="space-y-4">
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

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">Select Voice Agent</label>
                  <select
                    value={dispatchAgentId}
                    onChange={(e) => setDispatchAgentId(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white font-semibold focus:outline-none focus:border-cyan-400"
                  >
                    <option value={1}>Agent #1 — Inbound Reception & Lead Gen Specialist</option>
                    <option value={2}>Agent #2 — Outbound Campaign Follow-Up Assistant</option>
                    <option value={3}>Agent #3 — Enterprise Level 2 Technical Support Agent</option>
                  </select>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                  <p className="font-semibold text-slate-300 flex items-center gap-1">
                    <Radio className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Real-Time WebRTC Pipeline</span>
                  </p>
                  <p>Calls are downsampled to 16kHz PCM with sub-300ms round-trip latency and active RMS silence detection.</p>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button type="button" onClick={() => setShowDispatchModal(false)} className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold">Cancel</button>
                  <button type="submit" disabled={dispatching} className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-xs shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50">
                    {dispatching ? 'Dispatching...' : 'Start Live Call Session'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
