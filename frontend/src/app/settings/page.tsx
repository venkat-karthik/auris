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
  Loader2
} from "lucide-react";

export default function SettingsPage() {
  const { token, user } = useAuth();
  
  // Settings states
  const [orgName, setOrgName] = useState("My Team");
  const [saveLoading, setSaveLoading] = useState(false);
  const [apiKeyCreated, setApiKeyCreated] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [apiKeys, setApiKeys] = useState<{ id: number, name: string, key_prefix: string, created_at: string }[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [createKeyLoading, setCreateKeyLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchOrgAndKeys = async () => {
    if (!token) return;
    try {
      // 1. Load active API keys
      const keysRes = await fetch(`${API_URL}/api-keys`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (keysRes.ok) {
        const data = await keysRes.json();
        setApiKeys(data);
      }

      // 2. Load user and organization information
      const userRes = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (userRes.ok) {
        const me = await userRes.json();
        // Since auth/me returns selected_org_id, we default the team name or set it based on current defaults.
        // Let's use the local state name updated by updates.
      }
    } catch (err) {
      console.error("Error fetching settings:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrgAndKeys();
  }, [token]);

  const handleOrgSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/organization`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ name: orgName })
      });
      if (res.ok) {
        toast.success("Organization profile updated successfully!");
      } else {
        toast.error("Failed to update organization");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error updating organization");
    } finally {
      setSaveLoading(false);
    }
  };

  const handleGenerateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) {
      toast.error("Please enter a key name");
      return;
    }
    setCreateKeyLoading(true);
    try {
      const res = await fetch(`${API_URL}/api-keys`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ name: newKeyName })
      });
      if (res.ok) {
        const data = await res.json();
        setApiKeyCreated(data.raw_key);
        setNewKeyName("");
        toast.success("API Key generated! Make sure to copy it now.");
        fetchOrgAndKeys(); // Reload key list
      } else {
        toast.error("Failed to generate API Key");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error generating API Key");
    } finally {
      setCreateKeyLoading(false);
    }
  };

  const handleCopyKey = () => {
    if (!apiKeyCreated) return;
    navigator.clipboard.writeText(apiKeyCreated);
    setCopySuccess(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const handleRevokeKey = async (keyId: number) => {
    if (!confirm("Are you sure you want to revoke this API Key? It will stop working immediately.")) {
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api-keys/${keyId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("API Key successfully revoked");
        fetchOrgAndKeys();
      } else {
        toast.error("Failed to revoke API key");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error revoking API key");
    }
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
              {/* Form to generate new key */}
              <form onSubmit={handleGenerateKey} className="flex gap-2 items-end">
                <div className="flex-1 space-y-1">
                  <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Key Identifier Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Production Webhook Dialer"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-sm"
                  />
                </div>
                <button
                  type="submit"
                  disabled={createKeyLoading}
                  className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white font-semibold transition-colors cursor-pointer disabled:opacity-75 h-[42px]"
                >
                  {createKeyLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  <span>Generate</span>
                </button>
              </form>

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
                      className="p-2 rounded-lg bg-indigo-500 text-white hover:bg-indigo-600 transition-colors cursor-pointer"
                      title="Copy Key"
                    >
                      {copySuccess ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-[10px] text-rose-500 font-medium">
                    ⚠️ Copy this key now! You will not be able to retrieve or view it again.
                  </p>
                </div>
              )}

              {/* API keys list */}
              <div className="space-y-2 border-t border-slate-100 dark:border-zinc-800/80 pt-4">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active API Keys</h4>
                {loading ? (
                  <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Loading keys...</span>
                  </div>
                ) : apiKeys.length === 0 ? (
                  <p className="text-xs text-slate-400 py-2">No API keys registered for this organization.</p>
                ) : (
                  <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                    {apiKeys.map((key) => (
                      <div key={key.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-100/40 dark:bg-zinc-900/30 border border-slate-100 dark:border-zinc-800/40 text-xs">
                        <div className="space-y-1">
                          <span className="font-semibold block text-slate-800 dark:text-slate-200">{key.name}</span>
                          <span className="font-mono text-slate-400 block text-[10px]">{key.key_prefix}••••••••••••</span>
                        </div>
                        <button
                          onClick={() => handleRevokeKey(key.id)}
                          className="p-2 text-rose-500 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer"
                          title="Revoke Key"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
