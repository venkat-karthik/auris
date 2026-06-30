"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Phone,
  Plus,
  Trash2,
  Loader2,
  Search,
  Settings,
  Link as LinkIcon
} from "lucide-react";

interface LeasedNumber {
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

export default function TelephonyPage() {
  const { token } = useAuth();
  const [phoneNumbers, setPhoneNumbers] = useState<LeasedNumber[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [areaCode, setAreaCode] = useState("");
  const [availableNumbers, setAvailableNumbers] = useState<{ phone_number: string, region: string, monthly_cost_usd: number }[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [buyLoading, setBuyLoading] = useState<string | null>(null);
  const [numberLabel, setNumberLabel] = useState("Main Desk Line");
  const [bindingLoading, setBindingLoading] = useState<number | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchPhoneNumbersAndAgents = async () => {
    if (!token) return;
    try {
      const phoneRes = await fetch(`${API_URL}/phone-numbers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (phoneRes.ok) {
        const data = await phoneRes.json();
        setPhoneNumbers(data);
      }

      const agentsRes = await fetch(`${API_URL}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (agentsRes.ok) {
        const data = await agentsRes.json();
        setAgents(data);
      }
    } catch (err) {
      console.error("Error fetching telephony details:", err);
    }
  };

  useEffect(() => {
    fetchPhoneNumbersAndAgents();
  }, [token]);

  const handleSearchNumbers = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!areaCode.trim()) {
      toast.error("Please enter an area code");
      return;
    }
    setSearchLoading(true);
    setAvailableNumbers([]);
    try {
      const res = await fetch(`${API_URL}/phone-numbers/search?area_code=${areaCode}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAvailableNumbers(data);
        if (data.length === 0) {
          toast.info("No phone numbers found for this area code.");
        }
      } else {
        toast.error("Failed to query phone numbers");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error searching phone numbers");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleBuyNumber = async (numberStr: string, region: string) => {
    setBuyLoading(numberStr);
    try {
      const res = await fetch(`${API_URL}/phone-numbers/buy`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          phone_number: numberStr,
          label: numberLabel,
          region: region
        })
      });

      if (res.ok) {
        toast.success("Phone number leased successfully!");
        setAvailableNumbers((prev) => prev.filter((n) => n.phone_number !== numberStr));
        fetchPhoneNumbersAndAgents();
      } else {
        const errData = await res.json();
        toast.error(errData.detail || "Failed to lease phone number");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error purchasing number");
    } finally {
      setBuyLoading(null);
    }
  };

  const handleBindAgent = async (numberId: number, agentIdVal: string) => {
    setBindingLoading(numberId);
    const parsedAgentId = agentIdVal ? parseInt(agentIdVal) : null;
    try {
      const res = await fetch(`${API_URL}/phone-numbers/${numberId}/bind`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ agent_id: parsedAgentId })
      });

      if (res.ok) {
        toast.success("Agent binding updated");
        fetchPhoneNumbersAndAgents();
      } else {
        toast.error("Failed to update binding");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error setting binding");
    } finally {
      setBindingLoading(null);
    }
  };

  const handleReleaseNumber = async (numberId: number) => {
    if (!confirm("Are you sure you want to release this phone number back to the carrier? This action is permanent.")) return;

    try {
      const res = await fetch(`${API_URL}/phone-numbers/${numberId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        toast.success("Phone number released");
        fetchPhoneNumbersAndAgents();
      } else {
        toast.error("Failed to release number");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error releasing phone number");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Title header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Phone className="text-teal-500 w-8 h-8" /> Telephony Carriers
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Lease digital phone lines, connect inbound webhooks, and map active carrier routing directly to your voice agents.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left panel: Active leased numbers list */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold flex items-center gap-2">
                Active Leased Lines ({phoneNumbers.length})
              </h2>
              {phoneNumbers.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center">
                  You don't have any leased phone lines yet. Search below to add one.
                </p>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-zinc-800/80">
                  {phoneNumbers.map((num) => (
                    <div key={num.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div>
                        <p className="font-mono text-base font-bold text-slate-800 dark:text-white">
                          {num.phone_number}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">{num.label}</p>
                      </div>
                      <div className="flex items-center space-x-3">
                        {/* Bind select list */}
                        <div className="flex items-center space-x-2">
                          <LinkIcon className="w-3.5 h-3.5 text-slate-400" />
                          <select
                            value={num.agent_id?.toString() ?? ""}
                            disabled={bindingLoading === num.id}
                            onChange={(e) => handleBindAgent(num.id, e.target.value)}
                            className="bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 text-xs rounded-xl px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-teal-500"
                          >
                            <option value="">[Not Assigned]</option>
                            {agents.map((a) => (
                              <option key={a.id} value={a.id}>{a.name}</option>
                            ))}
                          </select>
                        </div>
                        <button
                          onClick={() => handleReleaseNumber(num.id)}
                          className="p-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-colors"
                          title="Release Number"
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

          {/* Right panel: Search and buy new numbers */}
          <div className="space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold flex items-center gap-2">
                Lease a New Line
              </h2>
              <form onSubmit={handleSearchNumbers} className="space-y-3">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Area Code</label>
                  <div className="relative flex items-center">
                    <Search className="absolute left-3 w-4 h-4 text-slate-400" />
                    <input
                      type="text"
                      maxLength={4}
                      value={areaCode}
                      onChange={(e) => setAreaCode(e.target.value.replace(/\D/g, ""))}
                      placeholder="e.g. 91 (India) or 206 (US)"
                      className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Line Label</label>
                  <input
                    type="text"
                    value={numberLabel}
                    onChange={(e) => setNumberLabel(e.target.value)}
                    placeholder="e.g. Inbound Reception"
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                  />
                </div>
                <button
                  type="submit"
                  disabled={searchLoading}
                  className="w-full py-2.5 rounded-xl bg-teal-500 hover:bg-teal-600 text-white font-semibold text-xs shadow-md shadow-teal-500/25 transition-all flex items-center justify-center space-x-2 cursor-pointer"
                >
                  {searchLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <span>Search Numbers</span>
                  )}
                </button>
              </form>

              {/* Display available numbers to buy */}
              {availableNumbers.length > 0 && (
                <div className="border-t border-slate-100 dark:border-zinc-800 pt-4 space-y-3">
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Available Inventory</label>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {availableNumbers.map((n) => (
                      <div key={n.phone_number} className="p-3 rounded-xl border border-slate-100 dark:border-zinc-800/80 flex items-center justify-between gap-3 text-xs bg-slate-50/50 dark:bg-zinc-900/40">
                        <div>
                          <p className="font-mono font-bold">{n.phone_number}</p>
                          <p className="text-[10px] text-slate-400">{n.region}</p>
                        </div>
                        <button
                          onClick={() => handleBuyNumber(n.phone_number, n.region)}
                          disabled={buyLoading !== null}
                          className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-[10px] font-bold transition-all disabled:opacity-50 cursor-pointer"
                        >
                          {buyLoading === n.phone_number ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <span>Rent Line</span>
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
