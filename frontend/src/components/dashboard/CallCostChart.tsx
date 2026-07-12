'use client';

import React, { useState, useEffect } from 'react';
import { DollarSign, Cpu, Layers, ShieldCheck, Zap } from 'lucide-react';

interface CostBreakdown {
  modelName: string;
  provider: string;
  creditsUsed: number;
  avgCostPerMin: number;
  percentage: number;
  color: string;
}

const MOCK_COST_DATA: CostBreakdown[] = [
  { modelName: 'Claude 3.5 Sonnet (Conversational Tier 3)', provider: 'Anthropic', creditsUsed: 420, avgCostPerMin: 18.5, percentage: 48, color: 'from-indigo-600 to-purple-500' },
  { modelName: 'GPT-4o Voice & Realtime Engine', provider: 'OpenAI', creditsUsed: 280, avgCostPerMin: 14.0, percentage: 32, color: 'from-cyan-600 to-cyan-400' },
  { modelName: 'Llama 3 70B (Fast Local Tier)', provider: 'Groq / Local', creditsUsed: 120, avgCostPerMin: 4.2, percentage: 14, color: 'from-emerald-600 to-emerald-400' },
  { modelName: 'Deepgram Nova-2 Audio VAD', provider: 'Deepgram', creditsUsed: 52, avgCostPerMin: 2.1, percentage: 6, color: 'from-amber-600 to-amber-400' },
];

export default function CallCostChart() {
  const [costs, setCosts] = useState<CostBreakdown[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setCosts(MOCK_COST_DATA);
    }, 350);
    return () => clearTimeout(timer);
  }, []);

  const totalCredits = (costs.length > 0 ? costs : MOCK_COST_DATA).reduce((acc, c) => acc + c.creditsUsed, 0);

  return (
    <div className="glass-card rounded-3xl p-6 border border-slate-800/80 space-y-6 relative overflow-hidden">
      <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-purple-400">
            <DollarSign className="w-4 h-4" />
            <span>Atomic Credit Ledger & Model Breakdown</span>
          </div>
          <h3 className="text-lg font-extrabold text-white mt-1">AI Model Cost Consumption</h3>
          <p className="text-xs text-slate-400">Per-minute atomic credit allocation across LLM, TTS, and VAD audio engines</p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-emerald-400">
          <Zap className="w-3.5 h-3.5 animate-bounce" />
          <span>Total Consumed: {totalCredits} Credits</span>
        </div>
      </div>

      {/* Stacked Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
          <span>Engine Distribution</span>
          <span className="text-slate-400 font-mono">100% Accounted</span>
        </div>
        <div className="w-full h-4 rounded-xl bg-slate-900 overflow-hidden flex gap-0.5 p-0.5 border border-slate-800">
          {(costs.length > 0 ? costs : MOCK_COST_DATA).map((item, idx) => (
            <div
              key={idx}
              style={{ width: `${item.percentage}%` }}
              title={`${item.modelName}: ${item.percentage}%`}
              className={`h-full rounded-sm bg-gradient-to-r ${item.color} transition-all duration-700 hover:opacity-80`}
            />
          ))}
        </div>
      </div>

      {/* Detailed Table Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
        {(costs.length > 0 ? costs : MOCK_COST_DATA).map((item, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-2xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 transition-all flex flex-col justify-between space-y-2"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-0.5">
                <p className="text-xs font-bold text-white leading-tight">{item.modelName}</p>
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">{item.provider}</p>
              </div>
              <span className="text-xs font-black font-mono text-cyan-400 bg-slate-950 px-2 py-0.5 rounded-lg border border-slate-800">
                {item.percentage}%
              </span>
            </div>

            <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/60 font-medium text-slate-300">
              <span>Used: <strong className="text-white">{item.creditsUsed} cr</strong></span>
              <span>Rate: <strong className="text-purple-300">{item.avgCostPerMin} cr/min</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
