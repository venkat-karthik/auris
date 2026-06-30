"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import {
  BarChart3,
  PhoneCall,
  Activity,
  Clock,
  Users2,
  Calendar,
  Sparkles
} from "lucide-react";

interface AnalyticsStats {
  total_calls: number;
  completed_calls: number;
  failed_calls: number;
  total_duration_sec: number;
  avg_duration_sec: number;
  agents_count: number;
}

export default function AnalyticsDashboardPage() {
  const { token } = useAuth();
  const [activeRange, setActiveRange] = useState("7d");
  const [stats, setStats] = useState<AnalyticsStats>({
    total_calls: 0,
    completed_calls: 0,
    failed_calls: 0,
    total_duration_sec: 0,
    avg_duration_sec: 0,
    agents_count: 1
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  useEffect(() => {
    if (!token) return;
    const fetchAnalytics = async () => {
      try {
        const res = await fetch(`${API_URL}/analytics/summary`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        console.error("Error loading analytics:", err);
      }
    };
    fetchAnalytics();
  }, [token]);

  return (
    <DashboardLayout>
      <div className="space-y-8 font-sans">
        {/* Title Block */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <BarChart3 className="text-teal-500 w-8 h-8" /> Analytics Dashboard
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            View and analyze your call performance metrics, success rates, and customer talk duration distributions.
          </p>
        </div>

        {/* Date Filter Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-zinc-800 pb-4">
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-zinc-900 p-1 rounded-xl text-xs font-bold">
            <button
              onClick={() => setActiveRange("7d")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                activeRange === "7d" ? "bg-white dark:bg-zinc-800 text-slate-900 dark:text-white shadow-sm" : "text-slate-500"
              }`}
            >
              Last 7 days
            </button>
            <button
              onClick={() => setActiveRange("30d")}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                activeRange === "30d" ? "bg-white dark:bg-zinc-800 text-slate-900 dark:text-white shadow-sm" : "text-slate-500"
              }`}
            >
              Last 30 days
            </button>
          </div>

          <div className="flex items-center gap-2 text-xs font-bold text-slate-500">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span>Jun 22, 2026 - Jun 29, 2026</span>
          </div>
        </div>

        {/* Key Metrics Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Card 1 */}
          <div className="glass p-5 rounded-2xl space-y-3 relative overflow-hidden">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-xs font-bold uppercase tracking-wider">Total Calls</span>
              <PhoneCall className="w-4 h-4 text-teal-500" />
            </div>
            <p className="text-3xl font-black">{stats.total_calls}</p>
            <p className="text-[10px] text-rose-500 font-bold">-100% vs previous 7d</p>
          </div>

          {/* Card 2 */}
          <div className="glass p-5 rounded-2xl space-y-3 relative overflow-hidden">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-xs font-bold uppercase tracking-wider">Connect Rate</span>
              <Activity className="w-4 h-4 text-teal-500" />
            </div>
            <p className="text-3xl font-black">
              {stats.total_calls > 0 ? `${Math.round((stats.completed_calls / stats.total_calls) * 100)}%` : "0%"}
            </p>
            <p className="text-[10px] text-slate-500 font-bold">0 of {stats.total_calls} connected</p>
          </div>

          {/* Card 3 */}
          <div className="glass p-5 rounded-2xl space-y-3 relative overflow-hidden">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-xs font-bold uppercase tracking-wider">Total Duration</span>
              <Clock className="w-4 h-4 text-teal-500" />
            </div>
            <p className="text-3xl font-black">{stats.total_duration_sec}s</p>
            <p className="text-[10px] text-rose-500 font-bold">-100% vs previous 7d</p>
          </div>

          {/* Card 4 */}
          <div className="glass p-5 rounded-2xl space-y-3 relative overflow-hidden">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-xs font-bold uppercase tracking-wider">Avg. Duration</span>
              <Clock className="w-4 h-4 text-teal-500" />
            </div>
            <p className="text-3xl font-black">{stats.avg_duration_sec}s</p>
            <p className="text-[10px] text-slate-500 font-bold">Average length of call loop</p>
          </div>

          {/* Card 5 */}
          <div className="glass p-5 rounded-2xl space-y-3 relative overflow-hidden">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-xs font-bold uppercase tracking-wider">Total Assistants</span>
              <Users2 className="w-4 h-4 text-teal-500" />
            </div>
            <p className="text-3xl font-black">{stats.agents_count}</p>
            <p className="text-[10px] text-slate-500 font-bold">Active voice agents configured</p>
          </div>
        </div>

        {/* Latency / Hourly Charts mock layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 glass p-6 rounded-2xl space-y-4">
            <h2 className="text-lg font-bold">Best Time to Call</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Connect rate across a typical week. Greener blocks represent higher customer connect success rates.
            </p>
            {/* Heatmap grid placeholder */}
            <div className="grid grid-cols-7 gap-2 pt-4">
              {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => (
                <div key={day} className="text-center space-y-1">
                  <span className="text-[10px] text-slate-500 font-bold uppercase block">{day}</span>
                  <div className="grid grid-rows-5 gap-1.5">
                    {[1, 2, 3, 4, 5].map((idx) => (
                      <div
                        key={idx}
                        className={`h-6 rounded bg-emerald-500/10 border border-emerald-500/5 hover:bg-emerald-500/40 transition-all`}
                        title="High connection success probability"
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass p-6 rounded-2xl space-y-4">
            <h2 className="text-lg font-bold">Call Duration</h2>
            <div className="space-y-4 pt-2">
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-slate-400">Under 1 min</span>
                  <span>75%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-teal-500 h-full w-[75%]" />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-slate-400">1 - 3 mins</span>
                  <span>20%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-indigo-500 h-full w-[20%]" />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-slate-400">3+ mins</span>
                  <span>5%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full w-[5%]" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
