"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth } from "@/components/Providers";
import { toast } from "sonner";
import {
  Cpu,
  Layers,
  Save,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  Activity
} from "lucide-react";

export default function ModelsDashboardPage() {
  const { token } = useAuth();
  const [modelType, setModelType] = useState("gpt-4o-mini");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(150);
  const [saveLoading, setSaveLoading] = useState(false);

  const handleSaveModels = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveLoading(true);
    // Simulate setting platform cost/model profiles
    setTimeout(() => {
      setSaveLoading(false);
      toast.success("LLM inference rules saved successfully!");
    }, 800);
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Title */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Cpu className="text-teal-500 w-8 h-8" /> Inference Models & LLM Rules
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Configure default LLM orchestrators, voice generation engines (TTS), and streaming Speech-to-Text cost parameters.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <form onSubmit={handleSaveModels} className="glass rounded-2xl p-6 space-y-6">
              <h2 className="text-lg font-bold">LLM Defaults Settings</h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Base LLM Engine</label>
                  <select
                    value={modelType}
                    onChange={(e) => setModelType(e.target.value)}
                    className="w-full bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 text-xs rounded-xl px-3 py-2.5 outline-none focus:ring-1 focus:ring-teal-500"
                  >
                    <option value="gpt-4o">OpenAI GPT-4o (Premium)</option>
                    <option value="gpt-4o-mini">OpenAI GPT-4o-Mini (Economy)</option>
                    <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Advanced Reasoning)</option>
                    <option value="llama3-70b-groq">Llama 3 70B via Groq (Ultra-Low Latency)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Temperature (Creativity)</label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-200 dark:bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
                    />
                    <span className="text-xs font-mono font-bold w-8">{temperature}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Max Response Tokens</label>
                  <input
                    type="number"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={saveLoading}
                className="py-2.5 px-6 rounded-xl bg-teal-500 hover:bg-teal-600 text-white text-xs font-semibold shadow-md shadow-teal-500/25 transition-all flex items-center gap-2 cursor-pointer"
              >
                {saveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                <span>Save Inference Rules</span>
              </button>
            </form>
          </div>

          <div className="space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold flex items-center gap-1.5">
                <Activity className="w-5 h-5 text-teal-500" /> Latency Overview
              </h2>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between border-b border-slate-100 dark:border-zinc-800 pb-2">
                  <span className="text-slate-400">Deepgram STT</span>
                  <span className="font-mono text-emerald-500 font-bold">~120ms</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 dark:border-zinc-800 pb-2">
                  <span className="text-slate-400">Groq LLM Llama3</span>
                  <span className="font-mono text-emerald-500 font-bold">~180ms</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 dark:border-zinc-800 pb-2">
                  <span className="text-slate-400">Cartesia TTS</span>
                  <span className="font-mono text-emerald-500 font-bold">~90ms</span>
                </div>
                <div className="flex justify-between font-bold pt-1">
                  <span>Total Loop Latency</span>
                  <span className="font-mono text-teal-500">~390ms</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
