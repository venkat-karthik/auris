"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Send,
  Upload,
  Play,
  Pause,
  Trash2,
  FileSpreadsheet,
  Users,
  CheckCircle,
  Clock,
  Loader2
} from "lucide-react";

interface Campaign {
  id: number;
  name: string;
  status: "idle" | "running" | "paused" | "completed";
  agent_id: number;
  agent_name: string;
  total_contacts: number;
  processed_contacts: number;
  successful_calls: number;
  created_at: string;
}

interface Agent {
  id: number;
  name: string;
}

export default function CampaignsPage() {
  const { token } = useAuth();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Form states
  const [name, setName] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [createLoading, setCreateLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchCampaignsAndAgents = async () => {
    if (!token) return;
    try {
      const campRes = await fetch(`${API_URL}/campaigns`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (campRes.ok) {
        const data = await campRes.json();
        setCampaigns(data);
      }

      const agentsRes = await fetch(`${API_URL}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (agentsRes.ok) {
        const data = await agentsRes.json();
        setAgents(data);
        if (data.length > 0) setSelectedAgentId(data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaignsAndAgents();
  }, [token]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setCsvFile(e.target.files[0]);
      toast.success(`Selected file: ${e.target.files[0].name}`);
    }
  };

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !selectedAgentId || !csvFile) {
      toast.error("Please provide campaign name, select an agent, and upload a contacts CSV");
      return;
    }

    setCreateLoading(true);
    const formData = new FormData();
    formData.append("name", name);
    formData.append("agent_id", selectedAgentId.toString());
    formData.append("file", csvFile);

    try {
      const res = await fetch(`${API_URL}/campaigns/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (res.ok) {
        toast.success("Campaign created and dialing contacts imported successfully!");
        setName("");
        setCsvFile(null);
        fetchCampaignsAndAgents();
      } else {
        toast.error("Failed to upload campaign CSV");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error creating campaign");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleToggleCampaign = async (id: number, currentStatus: string) => {
    const action = currentStatus === "running" ? "pause" : "start";
    try {
      const res = await fetch(`${API_URL}/campaigns/${id}/${action}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success(`Campaign ${action}ed`);
        fetchCampaignsAndAgents();
      } else {
        toast.error(`Failed to ${action} campaign`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header Title */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Send className="text-teal-500 w-8 h-8" /> Outbound Dialer Campaigns
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Import recipient lists, program smart concurrency thresholds, and broadcast high-throughput conversational audio campaigns.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* List of active/previous campaigns */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Broadcast Campaigns</h2>
              
              {loading ? (
                <div className="py-8 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-teal-500" /></div>
              ) : campaigns.length === 0 ? (
                <p className="text-xs text-slate-400 py-12 text-center">
                  No active outbound campaigns found. Create one using the form on the right.
                </p>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-zinc-800/80">
                  {campaigns.map((c) => (
                    <div key={c.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 dark:text-white">{c.name}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                            c.status === "running" ? "bg-emerald-500/10 text-emerald-500" :
                            c.status === "paused" ? "bg-amber-500/10 text-amber-500" :
                            c.status === "completed" ? "bg-indigo-500/10 text-indigo-500" : "bg-slate-200 text-slate-500"
                          }`}>
                            {c.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-slate-400">
                          <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> {c.processed_contacts}/{c.total_contacts} Contacts</span>
                          <span className="flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5 text-emerald-500" /> {c.successful_calls} Successful</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleCampaign(c.id, c.status)}
                          className="p-2 rounded-xl bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-slate-300 hover:bg-teal-500 hover:text-white transition-colors"
                        >
                          {c.status === "running" ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Create Campaign Panel */}
          <div className="space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">New Campaign</h2>
              <form onSubmit={handleCreateCampaign} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Campaign Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Feedback Campaign Q2"
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Assigned Agent</label>
                  <select
                    value={selectedAgentId ?? ""}
                    onChange={(e) => setSelectedAgentId(parseInt(e.target.value))}
                    className="w-full bg-slate-50 dark:bg-zinc-950/80 border border-slate-200 dark:border-zinc-800 text-xs rounded-xl px-3 py-2.5 outline-none focus:ring-1 focus:ring-teal-500"
                  >
                    {agents.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 block">Contacts File (CSV)</label>
                  <div className="border-2 border-dashed border-slate-200 dark:border-zinc-800 rounded-2xl p-6 text-center cursor-pointer hover:border-teal-500/50 transition-colors relative">
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileUpload}
                      className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                    />
                    <div className="flex flex-col items-center space-y-2">
                      <FileSpreadsheet className="w-8 h-8 text-teal-500" />
                      <span className="text-xs font-bold">
                        {csvFile ? csvFile.name : "Drag or select CSV"}
                      </span>
                      <span className="text-[10px] text-slate-400">CSV must contain a `phone_number` column</span>
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={createLoading}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs shadow-lg shadow-teal-500/25 transition-all flex items-center justify-center space-x-2 cursor-pointer"
                >
                  {createLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <span>Initialize Broadcast</span>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
