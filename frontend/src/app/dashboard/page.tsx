"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  TrendingUp,
  Clock,
  Coins,
  Bot,
  PhoneCall,
  Loader2,
  Calendar
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";

interface CallRun {
  id: number;
  duration_seconds: number | null;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const { token, orgId } = useAuth();
  const [balance, setBalance] = useState<number>(0);
  const [agentsCount, setAgentsCount] = useState<number>(0);
  const [calls, setCalls] = useState<CallRun[]>([]);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchDashboardData = async () => {
    if (!token) return;
    try {
      // 1. Fetch balance
      const balanceRes = await fetch(`${API_URL}/billing/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (balanceRes.ok) {
        const balanceData = await balanceRes.ok ? await balanceRes.json() : { balance_credits: 0 };
        setBalance(balanceData.balance_credits || 0);
      }

      // 2. Fetch agents count
      const agentsRes = await fetch(`${API_URL}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (agentsRes.ok) {
        const agentsData = await agentsRes.json();
        setAgentsCount(agentsData.length || 0);
      }

      // 3. Fetch call runs
      const callsRes = await fetch(`${API_URL}/calls`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (callsRes.ok) {
        const callsData = await callsRes.json();
        setCalls(callsData || []);
      }
    } catch (err) {
      console.error(err);
      toast.error("Could not fetch latest metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [token]);

  // Compute stats
  const totalCallSeconds = calls.reduce((acc, call) => acc + (call.duration_seconds || 0), 0);
  const totalMinutes = Math.round(totalCallSeconds / 60);
  const completedCalls = calls.filter(c => c.status === "completed").length;

  // Process data for Recharts (calls per day)
  const getChartData = () => {
    const dates: Record<string, number> = {};
    // Seed last 7 days
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      dates[dateStr] = 0;
    }

    calls.forEach(call => {
      try {
        const d = new Date(call.created_at);
        const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        if (dateStr in dates) {
          dates[dateStr] += 1;
        }
      } catch (e) {}
    });

    return Object.entries(dates).map(([name, count]) => ({ name, Calls: count }));
  };

  const chartData = getChartData();

  if (loading) {
    return (
      <DashboardLayout>
        <div className="h-[70vh] w-full flex items-center justify-center">
          <Loader2 className="w-10 h-10 text-teal-500 animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-fade-in">
        {/* Title */}
        <div className="flex flex-col space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight">Overview</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Realtime activity, credit balances, and operational insights.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Credits Balance Card */}
          <div className="glass p-6 rounded-2xl flex items-center justify-between shadow-sm">
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Credit Balance</span>
              <p className="text-3xl font-black text-indigo-600 dark:text-indigo-400">
                ₹{balance.toLocaleString()}
              </p>
            </div>
            <div className="p-3 bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-500 rounded-xl">
              <Coins className="w-6 h-6" />
            </div>
          </div>

          {/* Call Minutes Card */}
          <div className="glass p-6 rounded-2xl flex items-center justify-between shadow-sm">
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Call Minutes</span>
              <p className="text-3xl font-black text-teal-600 dark:text-teal-400">
                {totalMinutes} min
              </p>
            </div>
            <div className="p-3 bg-teal-500/10 dark:bg-teal-500/20 text-teal-500 rounded-xl">
              <Clock className="w-6 h-6" />
            </div>
          </div>

          {/* Active Agents Card */}
          <div className="glass p-6 rounded-2xl flex items-center justify-between shadow-sm">
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Agents</span>
              <p className="text-3xl font-black text-emerald-600 dark:text-emerald-400">
                {agentsCount}
              </p>
            </div>
            <div className="p-3 bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-500 rounded-xl">
              <Bot className="w-6 h-6" />
            </div>
          </div>

          {/* Total Calls Card */}
          <div className="glass p-6 rounded-2xl flex items-center justify-between shadow-sm">
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Calls Handled</span>
              <p className="text-3xl font-black text-sky-600 dark:text-sky-400">
                {calls.length}
              </p>
            </div>
            <div className="p-3 bg-sky-500/10 dark:bg-sky-500/20 text-sky-500 rounded-xl">
              <PhoneCall className="w-6 h-6" />
            </div>
          </div>
        </div>

        {/* Analytics Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Call Volume Chart */}
          <div className="lg:col-span-2 glass p-6 rounded-2xl shadow-sm flex flex-col space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-teal-500" />
                <h3 className="font-bold text-lg">Call Volume Trend</h3>
              </div>
              <span className="text-xs text-slate-400 dark:text-slate-500 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" /> Last 7 Days
              </span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCalls" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} opacity={0.15} />
                  <XAxis dataKey="name" stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(9, 9, 11, 0.9)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      borderRadius: "12px",
                      color: "#fff",
                      fontSize: "12px"
                    }}
                  />
                  <Area type="monotone" dataKey="Calls" stroke="#14b8a6" strokeWidth={2.5} fillOpacity={1} fill="url(#colorCalls)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Quick Logs Panel */}
          <div className="glass p-6 rounded-2xl shadow-sm flex flex-col space-y-4">
            <h3 className="font-bold text-lg">Recent Calls</h3>
            <div className="flex-1 overflow-y-auto space-y-3 max-h-[260px] pr-2">
              {calls.length === 0 ? (
                <div className="h-full flex items-center justify-center text-sm text-slate-400">
                  No call logs recorded yet.
                </div>
              ) : (
                calls.slice(0, 5).map(call => (
                  <div
                    key={call.id}
                    className="p-3 rounded-xl bg-white/40 dark:bg-zinc-900/40 border border-slate-100 dark:border-zinc-800/50 flex items-center justify-between text-sm"
                  >
                    <div className="space-y-1">
                      <p className="font-bold flex items-center gap-1.5">
                        <span className={`w-2 h-2 rounded-full ${call.status === "completed" ? "bg-emerald-500" : "bg-amber-500"}`} />
                        Call #{call.id}
                      </p>
                      <p className="text-xs text-slate-400 dark:text-slate-500">
                        {new Date(call.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    <span className="text-xs px-2 py-1 rounded-lg bg-slate-100 dark:bg-zinc-800/80 font-mono text-slate-500 dark:text-slate-400">
                      {call.duration_seconds ? `${Math.round(call.duration_seconds)}s` : "--"}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
