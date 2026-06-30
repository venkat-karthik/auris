"use client";

import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Megaphone,
  Plus,
  Trash2,
  Play,
  FileText,
  Clock,
  CheckCircle,
  HelpCircle,
  MessageSquare
} from "lucide-react";

interface BroadcastCampaign {
  id: string;
  name: string;
  status: "idle" | "running" | "completed";
  template: string;
  progress: string;
  created_at: string;
}

export default function WhatsAppBroadcastPage() {
  const [campaigns, setCampaigns] = useState<BroadcastCampaign[]>([
    {
      id: "broadcast-1",
      name: "Welcome Onboarding WhatsApp",
      status: "completed",
      template: "welcome_onboarding_v2",
      progress: "120/120 sent",
      created_at: "3 days ago"
    }
  ]);

  const [name, setName] = useState("");
  const [template, setTemplate] = useState("welcome_onboarding_v2");
  const [modalOpen, setModalOpen] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);

  const handleCreateBroadcast = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Please enter a campaign name");
      return;
    }
    setSubmitLoading(true);
    setTimeout(() => {
      const item: BroadcastCampaign = {
        id: `broadcast-${Date.now()}`,
        name,
        status: "idle",
        template,
        progress: "0/0 sent",
        created_at: "Just now"
      };
      setCampaigns((prev) => [item, ...prev]);
      setName("");
      setModalOpen(false);
      setSubmitLoading(false);
      toast.success("WhatsApp Broadcast campaign initialized!");
    }, 800);
  };

  const handleTriggerBroadcast = (id: string) => {
    setCampaigns((prev) =>
      prev.map((c) => {
        if (c.id === id) {
          toast.success("Broadcast broadcast executing... Sending template nodes.");
          return { ...c, status: "running", progress: "1/50 sent" };
        }
        return c;
      })
    );
  };

  const handleDeleteBroadcast = (id: string) => {
    setCampaigns((prev) => prev.filter((c) => c.id !== id));
    toast.success("Campaign deleted");
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 font-sans">
        {/* Title */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
              <Megaphone className="text-teal-500 w-8 h-8" /> WhatsApp Campaigns
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Manage and monitor your bulk WhatsApp template broadcasts to leads.
            </p>
          </div>
          
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs shadow-lg shadow-teal-500/25 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Campaign</span>
          </button>
        </div>

        {/* Workspace content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Broadcast Log History</h2>
              
              {campaigns.length === 0 ? (
                <p className="text-xs text-slate-400 py-12 text-center">
                  No WhatsApp campaigns found. Create one using the form on the right.
                </p>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-zinc-800/80">
                  {campaigns.map((c) => (
                    <div key={c.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 dark:text-white">{c.name}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                            c.status === "completed" ? "bg-indigo-500/10 text-indigo-400" :
                            c.status === "running" ? "bg-emerald-500/10 text-emerald-500" : "bg-slate-200 text-slate-500"
                          }`}>
                            {c.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-slate-400">
                          <span className="flex items-center gap-1 font-mono text-[10px]">{c.template}</span>
                          <span>{c.progress}</span>
                          <span>Created {c.created_at}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {c.status === "idle" && (
                          <button
                            onClick={() => handleTriggerBroadcast(c.id)}
                            className="p-2 rounded-xl bg-teal-500/10 text-teal-400 hover:bg-teal-500 hover:text-white transition-colors"
                            title="Start Campaign"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteBroadcast(c.id)}
                          className="p-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
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
              <h2 className="text-lg font-bold">New WhatsApp Broadcast</h2>
              <form onSubmit={handleCreateBroadcast} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Campaign Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Lead Promotion Template"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Select Template</label>
                  <select
                    value={template}
                    onChange={(e) => setTemplate(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-zinc-950/80 border border-slate-200 dark:border-zinc-800 text-xs rounded-xl px-3 py-2.5 outline-none focus:ring-1 focus:ring-teal-500"
                  >
                    <option value="welcome_onboarding_v2">Welcome Onboarding (Meta Approved)</option>
                    <option value="lead_followup_hsm">Lead Follow-Up Promo (Meta Approved)</option>
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={submitLoading}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs transition-all flex items-center justify-center"
                >
                  <span>Create Campaign</span>
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
