"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  MessageSquareCode,
  Plus,
  Trash2,
  Loader2,
  CheckCircle,
  Link2,
  Sparkles
} from "lucide-react";

interface WhatsappNumber {
  id: number;
  phone_number: string;
  label: string;
  is_active: boolean;
  agent_id: number | null;
  agent_name: string | null;
}

interface Agent {
  id: number;
  name: string;
}

export default function WhatsappNumbersPage() {
  const { token } = useAuth();
  const [whatsappNumbers, setWhatsappNumbers] = useState<WhatsappNumber[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [newNumber, setNewNumber] = useState("");
  const [newLabel, setNewLabel] = useState("WhatsApp Business Desk");
  const [createLoading, setCreateLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchWhatsappNumbersAndAgents = async () => {
    if (!token) return;
    try {
      // 1. Fetch agents to bind to
      const agentsRes = await fetch(`${API_URL}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (agentsRes.ok) {
        const data = await agentsRes.json();
        setAgents(data);
      }

      // 2. Fetch linked WhatsApp numbers
      const waRes = await fetch(`${API_URL}/whatsapp`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (waRes.ok) {
        const data = await waRes.json();
        setWhatsappNumbers(data);
      }
    } catch (err) {
      console.error("Error loading WhatsApp channels:", err);
      toast.error("Failed to load WhatsApp settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWhatsappNumbersAndAgents();
  }, [token]);

  const handleAddNumber = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNumber.trim()) {
      toast.error("Please enter a WhatsApp number");
      return;
    }
    setCreateLoading(true);
    try {
      const res = await fetch(`${API_URL}/whatsapp`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          phone_number: newNumber,
          label: newLabel
        })
      });

      if (res.ok) {
        toast.success("WhatsApp channel connected successfully!");
        setNewNumber("");
        setModalOpen(false);
        fetchWhatsappNumbersAndAgents();
      } else {
        const errData = await res.json();
        toast.error(errData.detail || "Failed to register WhatsApp channel");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error registering number");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteNumber = async (id: number) => {
    if (!confirm("Are you sure you want to disconnect this WhatsApp number?")) return;
    try {
      const res = await fetch(`${API_URL}/whatsapp/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("WhatsApp channel disconnected");
        fetchWhatsappNumbersAndAgents();
      } else {
        toast.error("Failed to disconnect number");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error deleting channel connection");
    }
  };

  const handleBindAgent = async (id: number, agentId: number) => {
    try {
      const res = await fetch(`${API_URL}/whatsapp/${id}/bind`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          agent_id: agentId || null
        })
      });
      if (res.ok) {
        toast.success("WhatsApp agent binding updated successfully!");
        fetchWhatsappNumbersAndAgents();
      } else {
        toast.error("Failed to bind agent to WhatsApp channel");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error setting channel routing");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 font-sans">
        {/* Title */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
              <MessageSquareCode className="text-teal-500 w-8 h-8" /> WhatsApp Channels
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Connect and manage your WhatsApp Business numbers to link outbound campaigns and routing.
            </p>
          </div>
          
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs shadow-lg shadow-teal-500/25 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Number</span>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Connected WhatsApp Numbers</h2>
              {loading ? (
                <div className="py-8 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-teal-500" /></div>
              ) : whatsappNumbers.length === 0 ? (
                <p className="text-xs text-slate-400 py-12 text-center">
                  No WhatsApp numbers linked to your workspace yet.
                </p>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-zinc-800/80">
                  {whatsappNumbers.map((num) => (
                    <div key={num.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div>
                        <p className="font-mono text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
                          <span>{num.phone_number}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold font-sans border border-emerald-500/20">
                            Phone WhatsApp
                          </span>
                        </p>
                        <p className="text-xs text-slate-400 mt-1">{num.label}</p>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400">Answered by</span>
                          <select
                            value={num.agent_id ?? ""}
                            onChange={(e) => handleBindAgent(num.id, parseInt(e.target.value))}
                            className="bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 text-xs rounded-xl px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500"
                          >
                            <option value="">Select Agent...</option>
                            {agents.map((a) => (
                              <option key={a.id} value={a.id}>{a.name}</option>
                            ))}
                          </select>
                        </div>

                        <button
                          onClick={() => handleDeleteNumber(num.id)}
                          className="p-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-colors"
                        >
                          <Trash2 className="w-4.5 h-4.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modal */}
        {modalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setModalOpen(false)} />
            <div className="relative w-full max-w-md glass rounded-2xl p-6 space-y-6">
              <h2 className="text-lg font-bold">Connect WhatsApp Number</h2>
              <form onSubmit={handleAddNumber} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">WhatsApp Phone Number *</label>
                  <input
                    type="text"
                    required
                    value={newNumber}
                    onChange={(e) => setNewNumber(e.target.value)}
                    placeholder="e.g. +918309827125"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Display Label</label>
                  <input
                    type="text"
                    value={newLabel}
                    onChange={(e) => setNewLabel(e.target.value)}
                    placeholder="Support desk line"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                  />
                </div>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs transition-all flex items-center justify-center"
                >
                  {createLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Connect number</span>}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
