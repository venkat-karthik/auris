"use client";

import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Users2,
  Send,
  Building,
  CheckCircle,
  HelpCircle,
  Loader2
} from "lucide-react";

export default function ResellerRequestPage() {
  const [name, setName] = useState("Karthik Kodeboyina");
  const [email, setEmail] = useState("karthikkodeboyina@gmail.com");
  const [phone, setPhone] = useState("+91");
  const [volume, setVolume] = useState("10,000 - 50,000 mins");
  const [interest, setInterest] = useState("agency_sub_accounts");
  const [useCase, setUseCase] = useState("I have a product question regarding setting up subaccounts.");
  const [submitLoading, setSubmitLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !phone || !useCase) {
      toast.error("Please fill in all required form fields");
      return;
    }

    setSubmitLoading(true);
    try {
      const res = await fetch(`${API_URL}/reseller`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name,
          email,
          phone,
          volume,
          interest,
          use_case: useCase
        })
      });

      if (res.ok) {
        toast.success("Reseller application query registered successfully! Our team will contact you soon.");
        setName("");
        setEmail("");
        setPhone("+91");
        setUseCase("");
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to submit reseller form");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error submitting partner inquiry");
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 font-sans max-w-3xl mx-auto">
        {/* Title Block */}
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center justify-center gap-2">
            <Users2 className="text-teal-500 w-8 h-8" /> Become a reseller
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Get programmatic access to manage child orgs, transfer credits, and set per-client controls.
          </p>
        </div>

        {/* Query form card */}
        <form onSubmit={handleSubmit} className="glass rounded-2xl p-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Name *</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your Name"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs font-semibold"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Email *</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your.name@company.com"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs font-semibold"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Phone Number *</label>
              <input
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. +91 9988776655"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs font-semibold"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Monthly Call Volume *</label>
              <select
                value={volume}
                onChange={(e) => setVolume(e.target.value)}
                className="w-full bg-slate-50 dark:bg-zinc-950/80 border border-slate-200 dark:border-zinc-800 text-xs rounded-xl px-3 py-2.5 outline-none focus:ring-1 focus:ring-teal-500"
              >
                <option value="Under 10,000 mins">Under 10,000 mins</option>
                <option value="10,000 - 50,000 mins">10,000 - 50,000 mins</option>
                <option value="50,000 - 200,000 mins">50,000 - 200,000 mins</option>
                <option value="200,000+ mins">200,000+ mins</option>
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">What can we help you with? *</label>
            <select
              value={interest}
              onChange={(e) => setInterest(e.target.value)}
              className="w-full bg-slate-50 dark:bg-zinc-950/80 border border-slate-200 dark:border-zinc-800 text-xs rounded-xl px-3 py-2.5 outline-none focus:ring-1 focus:ring-teal-500"
            >
              <option value="agency_sub_accounts">Reselling accounts / Sub-organizations</option>
              <option value="volume_inbound_dialer">Bulk pricing discounts</option>
              <option value="custom_integration">Custom enterprise deployments</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Describe your use case *</label>
            <textarea
              rows={4}
              required
              value={useCase}
              onChange={(e) => setUseCase(e.target.value)}
              placeholder="e.g. We are a marketing agency looking to deploy voice agents to 20 client pipelines..."
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs resize-none"
            />
          </div>

          <button
            type="submit"
            disabled={submitLoading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs transition-all flex items-center justify-center space-x-2 cursor-pointer"
          >
            {submitLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            <span>Submit Partner Query</span>
          </button>
        </form>
      </div>
    </DashboardLayout>
  );
}
