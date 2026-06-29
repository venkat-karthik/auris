"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Bot,
  Plus,
  Trash2,
  Edit,
  Loader2,
  Sparkles,
  Settings2,
  X
} from "lucide-react";

interface Agent {
  id: number;
  name: string;
  description: string | null;
  graph: any;
  model_config: any;
}

export default function AgentsPage() {
  const { token, orgId } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);

  // Form states
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchAgents = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
      } else {
        toast.error("Failed to load agents list");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error loading agents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, [token]);

  const handleCreateAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Please enter a name for the agent");
      return;
    }

    setSubmitLoading(true);
    try {
      const res = await fetch(`${API_URL}/agents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name,
          description,
          graph: { system_prompt: systemPrompt },
          model_config_data: {
            language: "en",
            cost_tier: "standard",
            stt: { provider: "deepgram" },
            llm: { provider: "openai", model: "gpt-4o-mini" },
            tts: { provider: "elevenlabs" }
          },
          context_variables: {}
        })
      });

      if (res.ok) {
        toast.success("Agent created successfully!");
        setModalOpen(false);
        // Reset form
        setName("");
        setDescription("");
        setSystemPrompt("");
        fetchAgents();
      } else {
        toast.error("Failed to create agent");
      }
    } catch (err) {
      console.error(err);
      toast.error("Could not create agent");
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDeleteAgent = async (id: number) => {
    if (!confirm("Are you sure you want to delete this agent? This action cannot be undone.")) return;

    try {
      const res = await fetch(`${API_URL}/agents/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        toast.success("Agent deleted");
        fetchAgents();
      } else {
        toast.error("Failed to delete agent");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error deleting agent");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header section */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
              <Bot className="text-teal-500 w-8 h-8" /> Voice Agents
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Manage your AI phone receptionists, adjust prompt definitions, and configure routing keys.
            </p>
          </div>
          
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold shadow-lg shadow-teal-500/20 dark:shadow-none hover:shadow-xl hover:shadow-teal-500/35 transition-all cursor-pointer"
          >
            <Plus className="w-5 h-5" />
            <span>Create Agent</span>
          </button>
        </div>

        {/* Loading / Listing states */}
        {loading ? (
          <div className="h-64 w-full flex items-center justify-center">
            <Loader2 className="w-10 h-10 text-teal-500 animate-spin" />
          </div>
        ) : agents.length === 0 ? (
          <div className="glass rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-4 max-w-lg mx-auto">
            <div className="p-4 bg-teal-500/10 dark:bg-teal-500/20 text-teal-500 rounded-2xl">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="font-bold text-xl">Create your first Agent</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              You haven't initialized any voice receptionists yet. Give it a name and set up its system prompt to begin.
            </p>
            <button
              onClick={() => setModalOpen(true)}
              className="px-6 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-600 text-white font-semibold transition-colors cursor-pointer"
            >
              Get Started
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="glass rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 flex flex-col justify-between group relative overflow-hidden"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 bg-teal-500/10 dark:bg-teal-500/20 text-teal-500 rounded-xl group-hover:scale-110 transition-transform">
                      <Bot className="w-5 h-5" />
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold border border-emerald-500/20">
                      Active
                    </span>
                  </div>

                  <div className="space-y-1">
                    <h3 className="font-bold text-lg leading-snug group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
                      {agent.name}
                    </h3>
                    <p className="text-xs text-slate-400 dark:text-slate-500 truncate">
                      ID: {agent.id}
                    </p>
                  </div>

                  <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-3 min-h-[60px]">
                    {agent.description || "No description provided."}
                  </p>
                </div>

                <div className="flex items-center space-x-3 pt-6 border-t border-slate-100 dark:border-zinc-800/60 mt-6">
                  <Link
                    href={`/agents/${agent.id}`}
                    className="flex-1 flex items-center justify-center space-x-1.5 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-900/50 text-sm font-semibold transition-colors"
                  >
                    <Settings2 className="w-4 h-4 text-slate-400" />
                    <span>Configure</span>
                  </Link>
                  <button
                    onClick={() => handleDeleteAgent(agent.id)}
                    className="p-2.5 rounded-xl text-rose-500 hover:bg-rose-500/5 dark:hover:bg-rose-500/10 border border-transparent hover:border-rose-500/10 transition-all cursor-pointer"
                    title="Delete Agent"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Agent Modal Overlay */}
        {modalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
              onClick={() => setModalOpen(false)}
            />

            {/* Modal Card */}
            <div className="relative w-full max-w-lg glass rounded-2xl shadow-2xl overflow-hidden p-8 flex flex-col space-y-6 animate-scale-up">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">New Voice Agent</h2>
                <button
                  onClick={() => setModalOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-slate-200/50 dark:hover:bg-zinc-800/50 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateAgent} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Agent Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Frontdesk receptionist"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-sm"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Description</label>
                  <input
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Handles initial business inbound inquiries"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-sm"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">System Prompt</label>
                  <textarea
                    rows={4}
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    placeholder="You are a warm, professional virtual assistant for Acme Corp. Be concise and friendly..."
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-sm resize-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitLoading}
                  className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold shadow-lg shadow-teal-500/25 dark:shadow-none focus:outline-none focus:ring-2 focus:ring-teal-500/50 transition-all cursor-pointer disabled:opacity-75 disabled:cursor-not-allowed"
                >
                  {submitLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <span>Create Agent</span>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
