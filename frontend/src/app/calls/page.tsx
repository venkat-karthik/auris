"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  PhoneCall,
  Loader2,
  Calendar,
  Clock,
  Phone,
  FileText,
  X,
  BadgeAlert
} from "lucide-react";

interface CallRun {
  id: number;
  agent_id: number;
  transport: string;
  call_type: string;
  status: string;
  caller_number: string | null;
  called_number: string | null;
  duration_seconds: number | null;
  disposition: string | null;
  created_at: string;
}

export default function CallLogsPage() {
  const { token } = useAuth();
  const [calls, setCalls] = useState<CallRun[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Selected call states for modal detail
  const [selectedCall, setSelectedCall] = useState<CallRun | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [mockTranscript, setMockTranscript] = useState<{ sender: string, text: string }[]>([]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchCalls = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/calls`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCalls(data);
      } else {
        toast.error("Failed to load call logs");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error loading calls");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, [token]);

  const viewCallDetails = (call: CallRun) => {
    setSelectedCall(call);
    setDetailModalOpen(true);
    
    // Populate fake transcript for testing call detailed view
    setMockTranscript([
      { sender: "agent", text: "Hello, welcome to Auris Support! How may I assist you?" },
      { sender: "user", text: "Hi, I was checking if you have multi-language support?" },
      { sender: "agent", text: "Yes! We support English, Hindi, Telugu, Tamil, and several other regional Indian languages." },
      { sender: "user", text: "Great. Thanks for the quick response." },
      { sender: "agent", text: "You are welcome. Have a wonderful day!" }
    ]);
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <PhoneCall className="text-teal-500 w-8 h-8" /> Call Logs
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Review detailed reports of inbound and WebRTC browser calls, including duration and user response transcripts.
          </p>
        </div>

        {/* Loading and Tables */}
        {loading ? (
          <div className="h-64 w-full flex items-center justify-center">
            <Loader2 className="w-10 h-10 text-teal-500 animate-spin" />
          </div>
        ) : calls.length === 0 ? (
          <div className="glass rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-4 max-w-lg mx-auto">
            <div className="p-4 bg-teal-500/10 dark:bg-teal-500/20 text-teal-500 rounded-2xl">
              <Phone className="w-8 h-8" />
            </div>
            <h3 className="font-bold text-xl">No Calls Recorded</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              When calls are received via Telnyx or initiated in the browser sandbox, they will display here.
            </p>
          </div>
        ) : (
          <div className="glass rounded-2xl overflow-hidden shadow-sm border border-slate-200/50 dark:border-zinc-800/60">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-100/55 dark:bg-zinc-900/50 text-slate-400 dark:text-slate-500 border-b border-slate-200/60 dark:border-zinc-800/60 font-bold uppercase tracking-wider text-[11px]">
                    <th className="py-4 px-6">ID</th>
                    <th className="py-4 px-6">Type</th>
                    <th className="py-4 px-6">Caller ID</th>
                    <th className="py-4 px-6">Status</th>
                    <th className="py-4 px-6">Duration</th>
                    <th className="py-4 px-6">Timestamp</th>
                    <th className="py-4 px-6 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-zinc-800/40">
                  {calls.map((call) => (
                    <tr
                      key={call.id}
                      className="hover:bg-slate-100/30 dark:hover:bg-zinc-900/20 transition-colors"
                    >
                      <td className="py-4 px-6 font-bold text-slate-900 dark:text-white">
                        #{call.id}
                      </td>
                      <td className="py-4 px-6">
                        <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 dark:bg-zinc-800 font-semibold">
                          {call.transport === "webrtc" ? "Browser" : "Telephony"}
                        </span>
                      </td>
                      <td className="py-4 px-6 font-mono text-slate-500 dark:text-slate-400">
                        {call.caller_number || "Anonymous"}
                      </td>
                      <td className="py-4 px-6">
                        <span
                          className={`inline-flex items-center gap-1 text-xs font-bold ${
                            call.status === "completed"
                              ? "text-emerald-500"
                              : "text-amber-500"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              call.status === "completed" ? "bg-emerald-500" : "bg-amber-500"
                            }`}
                          />
                          {call.status}
                        </span>
                      </td>
                      <td className="py-4 px-6 font-mono text-slate-500 dark:text-slate-400">
                        {call.duration_seconds ? `${Math.round(call.duration_seconds)}s` : "--"}
                      </td>
                      <td className="py-4 px-6 text-slate-400 dark:text-slate-500 text-xs">
                        {new Date(call.created_at).toLocaleDateString([], {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit"
                        })}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => viewCallDetails(call)}
                          className="inline-flex items-center gap-1.5 text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer"
                        >
                          <FileText className="w-3.5 h-3.5" /> Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Call Detail Transcript Modal */}
        {detailModalOpen && selectedCall && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
              onClick={() => setDetailModalOpen(false)}
            />

            {/* Modal Content */}
            <div className="relative w-full max-w-2xl glass rounded-2xl shadow-2xl overflow-hidden p-8 flex flex-col space-y-6 animate-scale-up">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-zinc-800/80 pb-3">
                <div>
                  <h2 className="text-xl font-bold">Call Run Details</h2>
                  <p className="text-xs text-slate-400 dark:text-slate-500">ID: #{selectedCall.id}</p>
                </div>
                <button
                  onClick={() => setDetailModalOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-slate-200/50 dark:hover:bg-zinc-800/50 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Call Overview Grid */}
              <div className="grid grid-cols-3 gap-4 p-4 rounded-xl bg-white/40 dark:bg-zinc-900/40 border border-slate-100 dark:border-zinc-800/50 text-xs">
                <div className="space-y-1">
                  <span className="text-slate-400 font-semibold block">Duration</span>
                  <div className="flex items-center gap-1 text-sm font-bold">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{selectedCall.duration_seconds ? `${Math.round(selectedCall.duration_seconds)}s` : "--"}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-slate-400 font-semibold block">Transport Type</span>
                  <span className="text-sm font-bold capitalize">{selectedCall.transport}</span>
                </div>
                <div className="space-y-1">
                  <span className="text-slate-400 font-semibold block">Disposition</span>
                  <span className="text-sm font-bold capitalize">{selectedCall.disposition || "normal"}</span>
                </div>
              </div>

              {/* Transcript Bubbles */}
              <div className="space-y-3">
                <h3 className="font-bold text-sm">Transcript Logs</h3>
                <div className="space-y-4 max-h-[250px] overflow-y-auto pr-2">
                  {mockTranscript.map((t, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col space-y-1 max-w-[85%] ${
                        t.sender === "user" ? "ml-auto items-end" : "mr-auto items-start"
                      }`}
                    >
                      <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">
                        {t.sender === "user" ? "You" : "Agent"}
                      </span>
                      <div
                        className={`p-3 rounded-2xl text-xs ${
                          t.sender === "user"
                            ? "bg-teal-500 text-white rounded-tr-none"
                            : "bg-slate-100 dark:bg-zinc-800/80 text-slate-800 dark:text-slate-100 rounded-tl-none"
                        }`}
                      >
                        {t.text}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
