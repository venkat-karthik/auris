'use client';

import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Calendar, ArrowUpRight } from 'lucide-react';

interface VolumeDataPoint {
  time: string;
  inbound: number;
  outbound: number;
  web: number;
}

const MOCK_VOLUME_DATA: VolumeDataPoint[] = [
  { time: '08:00', inbound: 45, outbound: 20, web: 15 },
  { time: '10:00', inbound: 82, outbound: 55, web: 38 },
  { time: '12:00', inbound: 120, outbound: 90, web: 65 },
  { time: '14:00', inbound: 95, outbound: 110, web: 50 },
  { time: '16:00', inbound: 140, outbound: 85, web: 75 },
  { time: '18:00', inbound: 165, outbound: 130, web: 95 },
  { time: '20:00', inbound: 110, outbound: 70, web: 60 },
];

export default function CallVolumeChart() {
  const [data, setData] = useState<VolumeDataPoint[]>([]);
  const [selectedRange, setSelectedRange] = useState<'today' | '7d' | '30d'>('today');

  useEffect(() => {
    // Simulate async data fetching / streaming for React Suspense & real-time updates
    const timer = setTimeout(() => {
      setData(MOCK_VOLUME_DATA);
    }, 400);
    return () => clearTimeout(timer);
  }, [selectedRange]);

  const maxTotal = Math.max(
    ...MOCK_VOLUME_DATA.map((d) => d.inbound + d.outbound + d.web),
    1
  );

  return (
    <div className="glass-card rounded-3xl p-6 border border-slate-800/80 space-y-5 relative overflow-hidden group">
      <div className="absolute -top-24 -right-24 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400">
            <Activity className="w-4 h-4" />
            <span>Telephony Throughput Pipeline</span>
          </div>
          <h3 className="text-lg font-extrabold text-white mt-1">Real-Time Call Volume & Direction</h3>
          <p className="text-xs text-slate-400">Bidirectional WebRTC browser voice & SIP PSTN concurrent active sessions</p>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800 self-start sm:self-center">
          {(['today', '7d', '30d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setSelectedRange(range)}
              className={`px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wide transition-all ${
                selectedRange === range
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Bar Chart Visualization */}
      <div className="pt-4 pb-2">
        <div className="flex items-end justify-between gap-3 h-52 px-2">
          {(data.length > 0 ? data : MOCK_VOLUME_DATA).map((pt, idx) => {
            const total = pt.inbound + pt.outbound + pt.web;
            const heightPct = Math.round((total / maxTotal) * 100);
            const inPct = Math.round((pt.inbound / total) * heightPct);
            const outPct = Math.round((pt.outbound / total) * heightPct);
            const webPct = Math.max(heightPct - inPct - outPct, 0);

            return (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2 group/bar">
                <div className="w-full flex flex-col items-center justify-end h-44 relative">
                  {/* Tooltip on hover */}
                  <div className="absolute -top-12 left-1/2 -translate-x-1/2 opacity-0 group-hover/bar:opacity-100 transition-opacity bg-slate-900 border border-slate-700 px-2.5 py-1.5 rounded-xl shadow-xl z-20 pointer-events-none whitespace-nowrap text-[10px] space-y-0.5">
                    <p className="font-bold text-white border-b border-slate-800 pb-0.5">{pt.time} UTC — {total} Calls</p>
                    <p className="text-cyan-400">Inbound: {pt.inbound}</p>
                    <p className="text-indigo-400">Outbound: {pt.outbound}</p>
                    <p className="text-purple-400">WebRTC: {pt.web}</p>
                  </div>

                  <div className="w-full max-w-[36px] flex flex-col justify-end gap-0.5 rounded-xl overflow-hidden bg-slate-900/60 p-0.5 border border-slate-800/60 group-hover/bar:border-cyan-500/50 transition-all">
                    <div
                      style={{ height: `${webPct}%` }}
                      className="w-full rounded-sm bg-gradient-to-t from-purple-600 to-purple-400 transition-all duration-500"
                    />
                    <div
                      style={{ height: `${outPct}%` }}
                      className="w-full rounded-sm bg-gradient-to-t from-indigo-600 to-indigo-400 transition-all duration-500"
                    />
                    <div
                      style={{ height: `${inPct}%` }}
                      className="w-full rounded-sm bg-gradient-to-t from-cyan-600 to-cyan-400 transition-all duration-500"
                    />
                  </div>
                </div>
                <span className="text-[11px] font-mono font-semibold text-slate-400 group-hover/bar:text-cyan-300 transition-colors">
                  {pt.time}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend Footer */}
      <div className="flex flex-wrap items-center justify-between pt-3 border-t border-slate-800/60 text-xs gap-4">
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-md bg-gradient-to-tr from-cyan-600 to-cyan-400 shadow-sm shadow-cyan-500/30" />
            <span className="font-semibold text-slate-300">Inbound Trunk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-md bg-gradient-to-tr from-indigo-600 to-indigo-400 shadow-sm shadow-indigo-500/30" />
            <span className="font-semibold text-slate-300">Outbound SIP</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-md bg-gradient-to-tr from-purple-600 to-purple-400 shadow-sm shadow-purple-500/30" />
            <span className="font-semibold text-slate-300">Web browser RTC</span>
          </div>
        </div>

        <div className="flex items-center gap-1 text-emerald-400 font-bold">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>+24.8% vs yesterday</span>
        </div>
      </div>
    </div>
  );
}
