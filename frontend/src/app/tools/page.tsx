"use client";

import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Wrench,
  Plus,
  Trash2,
  Play,
  Save,
  CheckCircle,
  Clock,
  HelpCircle,
  FileCode
} from "lucide-react";

interface WebhookTool {
  id: string;
  name: string;
  url: string;
  method: "GET" | "POST";
  description: string;
}

export default function DeveloperToolsPage() {
  const [tools, setTools] = useState<WebhookTool[]>([
    {
      id: "tool-1",
      name: "Check Room Availability",
      url: "https://api.acme-hotels.com/v1/rooms/check",
      method: "POST",
      description: "Triggered by agent to verify open reservation rooms for caller."
    }
  ]);

  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [method, setMethod] = useState<"GET" | "POST">("POST");
  const [description, setDescription] = useState("");

  const handleAddTool = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !url.trim()) {
      toast.error("Please provide both name and endpoint URL");
      return;
    }
    const newTool: WebhookTool = {
      id: `tool-${Date.now()}`,
      name,
      url,
      method,
      description
    };
    setTools((prev) => [...prev, newTool]);
    setName("");
    setUrl("");
    setDescription("");
    toast.success("Custom webhook tool registered locally!");
  };

  const handleDeleteTool = (id: string) => {
    setTools((prev) => prev.filter((t) => t.id !== id));
    toast.success("Tool removed");
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header Block */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Wrench className="text-teal-500 w-8 h-8" /> Developer Webhook Tools
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Define custom functions, hook APIs, and set up live parameters that voice agents can trigger autonomously during active calls.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* List of tools */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Registered Webhook Tools</h2>
              {tools.length === 0 ? (
                <p className="text-xs text-slate-400 py-12 text-center">
                  No webhook functions defined yet. Create one on the right.
                </p>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-zinc-800/80">
                  {tools.map((t) => (
                    <div key={t.id} className="py-4 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 dark:text-white">{t.name}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-slate-100 dark:bg-zinc-800 text-slate-500">
                            {t.method}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 font-mono">{t.url}</p>
                        <p className="text-xs text-slate-500 leading-relaxed mt-1">{t.description}</p>
                      </div>
                      <button
                        onClick={() => handleDeleteTool(t.id)}
                        className="p-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-colors"
                        title="Remove Tool"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Add Webhook Form */}
          <div className="space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Register Custom Tool</h2>
              <form onSubmit={handleAddTool} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Tool Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Fetch Order Status"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Endpoint URL</label>
                  <input
                    type="url"
                    required
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://api.yoursite.com/webhook"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Request Method</label>
                  <select
                    value={method}
                    onChange={(e) => setMethod(e.target.value as "GET" | "POST")}
                    className="w-full bg-slate-50 dark:bg-zinc-950/80 border border-slate-200 dark:border-zinc-800 text-xs rounded-xl px-3 py-2.5 outline-none focus:ring-1 focus:ring-teal-500"
                  >
                    <option value="POST">POST (Recommended)</option>
                    <option value="GET">GET</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Description</label>
                  <textarea
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe what this webhook does (so the AI LLM knows when to call it)..."
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs resize-none"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs shadow-lg shadow-teal-500/25 transition-all flex items-center justify-center space-x-2 cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  <span>Register Function</span>
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
