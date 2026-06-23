"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Settings,
  Key,
  Building,
  Plus,
  Trash2,
  Copy,
  CheckCircle,
  Loader2,
  Lock
} from "lucide-react";

export default function SettingsPage() {
  const { token, user } = useAuth();
  
  // Settings forms
  const [orgName, setOrgName] = useState("Test Organization");
  const [saveLoading, setSaveLoading] = useState(false);
  const [apiKeyCreated, setApiKeyCreated] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const handleOrgSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveLoading(true);
    setTimeout(() => {
      setSaveLoading(false);
      toast.success("Organization profile updated successfully!");
    }, 1000);
  };

  const handleGenerateKey = () => {
    // Mock key generation
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let key = "auris_live_";
    for (let i = 0; i < 32; i++) {
      key += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setApiKeyCreated(key);
    toast.success("API Key generated! Make sure to copy it now.");
  };

  const handleCopyKey = () => {
    if (!apiKeyCreated) return;
    navigator.clipboard.writeText(apiKeyCreated);
    setCopySuccess(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopySuccess(false), 2000);
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Settings className="text-teal-500 w-8 h-8" /> Settings
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Configure organization settings, look up profile credentials, and manage developer API keys.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Org details profile */}
          <div className="glass p-6 md:p-8 rounded-3xl shadow-sm space-y-6">
            <h3 className="font-bold text-lg flex items-center gap-2 border-b border-slate-100 dark:border-zinc-800/80 pb-3">
              <Building className="text-teal-500 w-5 h-5" /> Organization Details
            </h3>

            <form onSubmit={handleOrgSave} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Organization Name</label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-sm"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Default Currency</label>
                <input
                  type="text"
                  disabled
                  value="INR (Indian Rupee)"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-100/50 dark:bg-zinc-900/50 text-slate-500 text-sm cursor-not-allowed"
                />
              </div>

              <button
                type="submit"
                disabled={saveLoading}
                className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-600 text-white font-semibold transition-colors cursor-pointer disabled:opacity-75"
              >
                {saveLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>Save Profile</span>
              </button>
            </form>
          </div>

          {/* API keys credentials */}
          <div className="glass p-6 md:p-8 rounded-3xl shadow-sm space-y-6">
            <h3 className="font-bold text-lg flex items-center gap-2 border-b border-slate-100 dark:border-zinc-800/80 pb-3">
              <Key className="text-indigo-500 w-5 h-5" /> API Credentials
            </h3>

            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Use API keys to authenticate outbound telephony requests, stream audio via SDKs, or trigger webhook triggers. Keep your keys secret.
            </p>

            <div className="space-y-4">
              {/* Generate new key action */}
              <button
                onClick={handleGenerateKey}
                className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-900/50 text-sm font-semibold transition-colors cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Generate New API Key</span>
              </button>

              {/* Display generated key card */}
              {apiKeyCreated && (
                <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/20 space-y-3">
                  <span className="text-[10px] font-bold text-indigo-500 uppercase tracking-wider block">Generated Token</span>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      readOnly
                      value={apiKeyCreated}
                      className="flex-1 px-3 py-2 rounded-lg border border-indigo-500/20 bg-zinc-950 text-indigo-400 font-mono text-xs focus:outline-none"
                    />
                    <button
                      onClick={handleCopyKey}
                      className="p-2 rounded-lg bg-indigo-500 text-white hover:bg-indigo-600 transition-colors"
                      title="Copy Key"
                    >
                      {copySuccess ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-[10px] text-slate-400">
                    Warning: You won't be able to see this key again once you leave this screen.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
