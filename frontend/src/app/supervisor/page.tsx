'use client';

import React, { useState, useEffect, useRef } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { useAuth } from '@/context/AuthContext';
import { AurisAPI } from '@/lib/api';
import { Headphones, Activity, MessageSquare, ShieldAlert, PhoneOff, Send, Clock, User, Mic } from 'lucide-react';

interface ActiveCall {
  run_id: number;
  agent_id: number;
  agent_name: string;
  transport: string;
  call_type: string;
  caller_number: string;
  called_number: string;
  started_at: number;
  last_transcript: string;
  status: string;
}

export default function SupervisorDashboard() {
  const { activeOrg } = useAuth();
  const [calls, setCalls] = useState<ActiveCall[]>([]);
  const [connected, setConnected] = useState(false);
  
  // Whisper modal state
  const [whisperingTo, setWhisperingTo] = useState<number | null>(null);
  const [whisperText, setWhisperText] = useState('');
  const [sendingWhisper, setSendingWhisper] = useState(false);

  // Takeover state
  const [takeoverActive, setTakeoverActive] = useState<number | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const wsUrl = baseUrl.replace('http', 'ws') + '/monitor/ws';
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // Auto reconnect after 5s
      setTimeout(connectWebSocket, 5000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'init') {
          setCalls(data.calls || []);
        } else if (data.type === 'call_started') {
          setCalls(prev => [...prev, data.call]);
        } else if (data.type === 'call_updated') {
          setCalls(prev => prev.map(c => 
            c.run_id === data.run_id 
              ? { ...c, last_transcript: data.last_transcript }
              : c
          ));
        } else if (data.type === 'call_ended') {
          setCalls(prev => prev.filter(c => c.run_id !== data.run_id));
          if (takeoverActive === data.run_id) setTakeoverActive(null);
          if (whisperingTo === data.run_id) setWhisperingTo(null);
        }
      } catch (err) {
        console.error('Error parsing monitor message', err);
      }
    };
  };

  const handleWhisper = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!whisperingTo || !whisperText.trim()) return;
    
    try {
      setSendingWhisper(true);
      await AurisAPI.supervisor.whisper(whisperingTo, whisperText);
      setWhisperText('');
      setWhisperingTo(null);
    } catch (err) {
      console.error('Failed to send whisper', err);
    } finally {
      setSendingWhisper(false);
    }
  };

  const handleTakeover = async (runId: number) => {
    if (takeoverActive === runId) {
      // Stop takeover
      try {
        await AurisAPI.supervisor.takeoverStop(runId);
        setTakeoverActive(null);
      } catch (err) {
        console.error('Failed to stop takeover', err);
      }
    } else {
      // Start takeover
      try {
        await AurisAPI.supervisor.takeoverStart(runId);
        setTakeoverActive(runId);
      } catch (err) {
        console.error('Failed to start takeover', err);
      }
    }
  };

  const formatDuration = (startTimestamp: number) => {
    const seconds = Math.floor(Date.now() / 1000 - startTimestamp);
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8 pb-12 relative">
        
        {/* Whisper Modal */}
        {whisperingTo !== null && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-indigo-500/30 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-indigo-400" />
                <span>Whisper to AI Agent</span>
              </h3>
              <p className="text-xs text-slate-300">
                Send a hidden prompt to the AI agent to alter its behavior mid-call. The customer will not hear this.
              </p>
              <form onSubmit={handleWhisper} className="space-y-4">
                <textarea
                  value={whisperText}
                  onChange={(e) => setWhisperText(e.target.value)}
                  placeholder="e.g. Offer them a 20% discount if they mention price..."
                  className="w-full h-24 glass-input p-3 rounded-xl text-sm resize-none"
                  required
                />
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setWhisperingTo(null)}
                    className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={sendingWhisper || !whisperText.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 transition-all disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Send Whisper</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-slate-900/90 via-indigo-950/30 to-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-xl">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3">
              <Headphones className="w-8 h-8 text-indigo-400" />
              <span>Live Supervisor Dashboard</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Monitor active calls, read real-time transcripts, and intervene when necessary.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className={`px-4 py-2 rounded-xl flex items-center gap-2 border text-sm font-bold shadow-lg ${
              connected 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-emerald-500/10' 
                : 'bg-red-500/10 text-red-400 border-red-500/20 shadow-red-500/10 animate-pulse'
            }`}>
              <Activity className="w-4 h-4" />
              <span>{connected ? 'Live Sync Active' : 'Reconnecting...'}</span>
            </div>
          </div>
        </div>

        {/* Active Calls Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
          {calls.length === 0 ? (
            <div className="col-span-full py-16 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-3xl bg-slate-900/30">
              <PhoneOff className="w-12 h-12 text-slate-600 mb-4" />
              <p className="text-slate-400 font-bold">No active calls right now</p>
              <p className="text-slate-500 text-sm mt-1">Incoming or outbound calls will appear here automatically.</p>
            </div>
          ) : (
            calls.map((call) => {
              const isTakenOver = takeoverActive === call.run_id;
              
              return (
                <div 
                  key={call.run_id} 
                  className={`glass-panel rounded-3xl p-5 space-y-4 relative overflow-hidden transition-all duration-300 ${
                    isTakenOver ? 'border-red-500/40 shadow-[0_0_20px_rgba(239,68,68,0.15)]' : 'border-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.05)]'
                  }`}
                >
                  {/* Live Pulse Indicator Background */}
                  <div className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-20 pointer-events-none animate-pulse ${
                    isTakenOver ? 'bg-red-500' : 'bg-emerald-500'
                  }`} />
                  
                  {/* Header info */}
                  <div className="flex items-start justify-between relative z-10">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`w-2 h-2 rounded-full animate-ping ${isTakenOver ? 'bg-red-400' : 'bg-emerald-400'}`} />
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${isTakenOver ? 'text-red-400' : 'text-emerald-400'}`}>
                          {isTakenOver ? 'Human Override Active' : 'AI Active'}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-white flex items-center gap-1.5">
                        <User className="w-4 h-4 text-slate-400" />
                        {call.caller_number} → {call.called_number}
                      </h3>
                      <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <Mic className="w-3.5 h-3.5" />
                        Agent: {call.agent_name}
                      </p>
                    </div>
                    <div className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-700 flex items-center gap-1.5 shadow-sm text-xs text-slate-300 font-mono font-bold">
                      <Clock className="w-3.5 h-3.5 text-indigo-400" />
                      <LiveTimer startTimestamp={call.started_at} />
                    </div>
                  </div>

                  {/* Transcript Scrollbox */}
                  <div className="h-32 p-3 rounded-xl bg-slate-950/80 border border-slate-800 overflow-y-auto font-mono text-[11px] leading-relaxed relative z-10">
                    {!call.last_transcript ? (
                      <span className="text-slate-500 italic">Waiting for speech...</span>
                    ) : (
                      <span className="text-emerald-300">{call.last_transcript}</span>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-2 relative z-10">
                    <button
                      onClick={() => setWhisperingTo(call.run_id)}
                      disabled={isTakenOver}
                      className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Whisper</span>
                    </button>
                    <button
                      onClick={() => handleTakeover(call.run_id)}
                      className={`flex-1 py-2.5 rounded-xl text-white text-xs font-bold transition-all flex items-center justify-center gap-2 border shadow-lg ${
                        isTakenOver 
                          ? 'bg-slate-800 border-slate-700 hover:bg-slate-700 shadow-slate-900/50' 
                          : 'bg-red-600/80 border-red-500/50 hover:bg-red-500 shadow-red-500/20'
                      }`}
                    >
                      <ShieldAlert className="w-3.5 h-3.5" />
                      <span>{isTakenOver ? 'Release Call' : 'Barge-in'}</span>
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </AppLayout>
  );
}

// Helper component for updating timer without causing full re-renders of the list
function LiveTimer({ startTimestamp }: { startTimestamp: number }) {
  const [display, setDisplay] = useState('0:00');

  useEffect(() => {
    const update = () => {
      const seconds = Math.floor(Date.now() / 1000 - startTimestamp);
      const m = Math.floor(seconds / 60);
      const s = seconds % 60;
      setDisplay(`${m}:${s.toString().padStart(2, '0')}`);
    };
    
    update();
    const int = setInterval(update, 1000);
    return () => clearInterval(int);
  }, [startTimestamp]);

  return <span>{display}</span>;
}
