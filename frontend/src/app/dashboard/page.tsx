"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import LiveMonitor from "@/components/LiveMonitor";
import { toast } from "sonner";
import {
  TrendingUp,
  Clock,
  Coins,
  Bot,
  PhoneCall,
  Loader2,
  Calendar,
  BarChart2,
  PieChart as PieIcon,
  PhoneOff
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";

interface CallRun {
  id: number;
  duration_seconds: number | null;
  status: string;
  created_at: string;
  voicemail: boolean | null;
}

interface AgentAnalytic {
  agent_id: number;
  name: string;
  call_count: number;
  avg_duration: number;
  conversion_rate: number;
  voicemail_count: number;
  total_cost: number;
}

interface CallOutcome {
  outcome: string;
  count: number;
}

const COLORS = ["#14b8a6", "#6366f1", "#06b6d4", "#a855f7", "#ec4899", "#10b981"];

export default function DashboardPage() {
  const { token } = useAuth();
  const [balance, setBalance] = useState<number>(0);
  const [agentsCount, setAgentsCount] = useState<number>(0);
  const [calls, setCalls] = useState<CallRun[]>([]);
  const [agentAnalytics, setAgentAnalytics] = useState<AgentAnalytic[]>([]);
  const [callOutcomes, setCallOutcomes] = useState<CallOutcome[]>([]);
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
        const balanceData = await balanceRes.json();
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

      // 4. Fetch agent analytics
      const agentRes = await fetch(`${API_URL}/analytics/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (agentRes.ok) {
        const agentData = await agentRes.json();
        setAgentAnalytics(agentData || []);
      }

      // 5. Fetch call outcomes
      const outcomeRes = await fetch(`${API_URL}/analytics/call_outcomes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (outcomeRes.ok) {
        const outcomeData = await outcomeRes.json();
        setCallOutcomes(outcomeData || []);
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
  const voicemailsCount = calls.filter(c => c.voicemail).length;

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
            Realtime activity, agent performance metrics, and call outcome distribution.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Credits Balance Card */}
          <div className="glass transition-all duration-300 hover:-translate-y-0.5 glow-indigo p-6 rounded-2xl flex items-center justify-between shadow-sm">
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
          <div className="glass transition-all duration-300 hover:-translate-y-0.5 glow-teal p-6 rounded-2xl flex items-center justify-between shadow-sm">
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
          <div className="glass transition-all duration-300 hover:-translate-y-0.5 glow-indigo p-6 rounded-2xl flex items-center justify-between shadow-sm">
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
          <div className="glass transition-all duration-300 hover:-translate-y-0.5 glow-teal p-6 rounded-2xl flex items-center justify-between shadow-sm">
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

        {/* First Row of Charts: Call Volume & Outcome */}
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

          {/* Call Outcome Distribution */}
          <div className="glass p-6 rounded-2xl shadow-sm flex flex-col space-y-6">
            <div className="flex items-center space-x-2">
              <PieIcon className="w-5 h-5 text-indigo-500" />
              <h3 className="font-bold text-lg">Call Outcomes</h3>
            </div>

            <div className="h-48 w-full flex items-center justify-center relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={callOutcomes}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="count"
                    nameKey="outcome"
                  >
                    {callOutcomes.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(9, 9, 11, 0.9)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      borderRadius: "12px",
                      color: "#fff",
                      fontSize: "12px"
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Total</span>
                <span className="text-2xl font-black">{callOutcomes.reduce((acc, curr) => acc + curr.count, 0)}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              {callOutcomes.map((entry, index) => (
                <div key={entry.outcome} className="flex items-center space-x-1.5">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-slate-400 font-medium truncate">{entry.outcome} ({entry.count})</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Second Row of Charts: Agent Analytics & Recent Logs */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Agent Performance Chart */}
          <div className="lg:col-span-2 glass p-6 rounded-2xl shadow-sm flex flex-col space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BarChart2 className="w-5 h-5 text-indigo-500" />
                <h3 className="font-bold text-lg">Agent Performance & Conversions</h3>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agentAnalytics} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
                  <Legend verticalAlign="top" height={36} iconType="circle" />
                  <Bar name="Calls Handled" dataKey="call_count" fill="#0ea5e9" radius={[4, 4, 0, 0]} barSize={30} />
                  <Bar name="Conversion Rate (%)" dataKey="conversion_rate" fill="#10b981" radius={[4, 4, 0, 0]} barSize={30} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass p-6 rounded-2xl shadow-sm flex flex-col space-y-4">
            <LiveMonitor />
          </div>
        </div>

        {/* Row 4: Voicemails and Recent Calls Log */}
        <div className="glass p-6 rounded-2xl shadow-sm flex flex-col space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-lg">Recent Call Activity Logs</h3>
            {voicemailsCount > 0 && (
              <span className="flex items-center gap-1 text-xs text-red-500 font-bold bg-red-500/10 px-2.5 py-0.5 rounded-full">
                <PhoneOff className="w-3 h-3" /> {voicemailsCount} Voicemails Detected
              </span>
            )}
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-100/55 dark:bg-zinc-900/50 text-slate-400 dark:text-slate-500 border-b border-slate-200/60 dark:border-zinc-800/60 font-bold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-4">Call ID</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Voicemail</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-zinc-800/40">
                {calls.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-sm text-slate-400">
                      No call logs recorded yet.
                    </td>
                  </tr>
                ) : (
                  calls.slice(0, 8).map(call => (
                    <tr key={call.id} className="hover:bg-slate-100/30 dark:hover:bg-zinc-900/20 transition-colors">
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">
                        #{call.id}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${call.status === "completed" ? "text-emerald-500" : "text-amber-500"}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${call.status === "completed" ? "bg-emerald-500" : "bg-amber-500"}`} />
                          {call.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {call.voicemail ? (
                          <span className="text-[10px] px-2 py-0.5 bg-rose-500/10 text-rose-500 rounded border border-rose-500/20 font-bold">Voicemail</span>
                        ) : (
                          <span className="text-[10px] px-2 py-0.5 bg-slate-100 dark:bg-zinc-800 text-slate-400 rounded font-medium">None</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-500 dark:text-slate-400">
                        {call.duration_seconds ? `${Math.round(call.duration_seconds)}s` : "--"}
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-400 dark:text-slate-500">
                        {new Date(call.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
