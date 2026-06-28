/* eslint-disable @typescript-eslint/no-explicit-any, react-hooks/exhaustive-deps, react-hooks/purity, @typescript-eslint/no-unused-vars */
"use client";

import { useEffect, useState, useRef } from "react";
import { Activity, Phone, User, Bot, Volume2, ShieldAlert } from "lucide-react";

interface ActiveCall {
  run_id: number;
  agent_id: number;
  agent_name: string;
  transport: string;
  call_type: string;
  caller_number: string;
  called_number: string;
  started_at: number; // epoch seconds
  last_transcript: string;
}

export default function LiveMonitor() {
  const [calls, setCalls] = useState<ActiveCall[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";
    const ws = new WebSocket(`${WS_URL}/monitor/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "init") {
          setCalls(data.calls || []);
        } else if (data.type === "call_started") {
          setCalls((prev) => [...prev.filter((c) => c.run_id !== data.call.run_id), data.call]);
        } else if (data.type === "call_updated") {
          setCalls((prev) =>
            prev.map((c) =>
              c.run_id === data.run_id
                ? { ...c, last_transcript: data.last_transcript }
                : c
            )
          );
        } else if (data.type === "call_ended") {
          setCalls((prev) => prev.filter((c) => c.run_id !== data.run_id));
        }
      } catch (e) {
        console.error("Error parsing monitor websocket payload:", e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Attempt reconnect after 5s
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          // Reconnect logic
        }
      }, 5000);
    };

    return () => {
      ws.close();
    };
  }, []);

  // Update call durations every second
  const [, setTick] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setTick((t) => t + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const getElapsedSeconds = (startedAt: number) => {
    const elapsed = Math.floor(Date.now() / 1000 - startedAt);
    return elapsed > 0 ? elapsed : 0;
  };

  const formatDuration = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="glass p-6 rounded-2xl shadow-sm flex flex-col space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className={`w-5 h-5 ${calls.length > 0 ? "text-rose-500 animate-pulse" : "text-purple-500"}`} />
          <h3 className="font-bold text-lg">Live Call Monitor</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`w-2 h-2 rounded-full ${
              connected ? "bg-fuchsia-500 animate-ping" : "bg-rose-500"
            }`}
          />
          <span className="text-xs text-slate-400 dark:text-slate-500 font-medium">
            {connected ? "Subscribed" : "Disconnected"}
          </span>
        </div>
      </div>

      {/* Active Calls List */}
      <div className="flex-1 overflow-y-auto space-y-4 max-h-[300px] pr-2">
        {calls.length === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center text-center space-y-3">
            <div className="relative flex items-center justify-center">
              <span className="absolute inline-flex h-12 w-12 rounded-full bg-purple-500/10 dark:bg-purple-500/20 animate-ping" />
              <div className="p-3 bg-purple-500/20 text-purple-500 rounded-full">
                <Volume2 className="w-6 h-6 animate-bounce" />
              </div>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-600 dark:text-slate-300">Awaiting Calls</p>
              <p className="text-xs text-slate-400 dark:text-slate-500">
                Listening for incoming WebRTC or outbound telephony calls...
              </p>
            </div>
          </div>
        ) : (
          calls.map((call) => {
            const elapsed = getElapsedSeconds(call.started_at);
            return (
              <div
                key={call.run_id}
                className="p-4 rounded-2xl bg-white/40 dark:bg-zinc-950/40 border border-slate-200/50 dark:border-zinc-800/60 space-y-3 flex flex-col transition-all hover:scale-[1.01]"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse shrink-0" />
                    <span className="text-xs font-bold text-rose-500 uppercase tracking-widest">Live</span>
                    <span className="text-xs font-mono text-slate-500 dark:text-slate-400 font-semibold">
                      #{call.run_id}
                    </span>
                  </div>
                  <span className="text-xs font-bold font-mono text-fuchsia-500 dark:text-fuchsia-400 bg-fuchsia-500/10 px-2 py-0.5 rounded-md">
                    {formatDuration(elapsed)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center space-x-1.5 text-slate-500 dark:text-slate-400">
                    <Bot className="w-3.5 h-3.5 text-purple-500" />
                    <span className="font-bold truncate">{call.agent_name}</span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-slate-500 dark:text-slate-400">
                    <Phone className="w-3.5 h-3.5 text-cyan-500" />
                    <span className="font-mono truncate">{call.caller_number}</span>
                  </div>
                </div>

                {call.last_transcript ? (
                  <div className="text-xs p-2 rounded-xl bg-slate-100/50 dark:bg-zinc-900/60 border border-slate-100 dark:border-zinc-800/40 font-mono text-slate-700 dark:text-slate-300 italic truncate">
                    {call.last_transcript}
                  </div>
                ) : (
                  <div className="text-xs p-2 rounded-xl bg-slate-100/50 dark:bg-zinc-900/60 border border-slate-100 dark:border-zinc-800/40 font-mono text-slate-400 dark:text-slate-600 italic">
                    Connected. Greeting client...
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
