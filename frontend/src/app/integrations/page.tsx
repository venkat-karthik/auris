"use client";

import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Boxes,
  Calendar,
  Layers,
  Database,
  ExternalLink,
  Search,
  CheckCircle,
  HelpCircle
} from "lucide-react";

interface IntegrationItem {
  name: string;
  category: "Calendar & CRM" | "Messaging" | "Data & Sheets" | "Custom & Tools";
  timing: "During Call" | "Post Call";
  description: string;
  connected: boolean;
}

export default function IntegrationsPage() {
  const [activeCategory, setActiveCategory] = useState<string>("All");
  const [integrations, setIntegrations] = useState<IntegrationItem[]>([
    {
      name: "Cal.com",
      category: "Calendar & CRM",
      timing: "During Call",
      description: "Sync your Cal.com calendar to allow voice assistants to schedule meetings on your behalf.",
      connected: false
    },
    {
      name: "Calendly",
      category: "Calendar & CRM",
      timing: "During Call",
      description: "Connect your Calendly account to check availability and schedule appointments through your voice assistants.",
      connected: false
    },
    {
      name: "Custom API",
      category: "Custom & Tools",
      timing: "During Call",
      description: "Connect to any custom API endpoint to extend your assistant's capabilities with external data and services.",
      connected: true
    },
    {
      name: "Salesforce",
      category: "Calendar & CRM",
      timing: "Post Call",
      description: "Connect your Salesforce CRM to access customer data, manage leads, and update records through your voice assistants.",
      connected: false
    },
    {
      name: "Google Calendar",
      category: "Calendar & CRM",
      timing: "During Call",
      description: "Connect your Google Calendar to check availability and schedule appointments through your voice assistants.",
      connected: false
    },
    {
      name: "Google Sheets",
      category: "Data & Sheets",
      timing: "Post Call",
      description: "Connect your Google Sheets to read, write, and manage spreadsheet data through your voice assistants.",
      connected: false
    }
  ]);

  const categories = ["All", "Calendar & CRM", "Messaging", "Data & Sheets", "Custom & Tools"];

  const handleToggleConnection = (name: string) => {
    setIntegrations((prev) =>
      prev.map((item) => {
        if (item.name === name) {
          const nextState = !item.connected;
          toast.success(`${item.name} is now ${nextState ? "Connected" : "Disconnected"}`);
          return { ...item, connected: nextState };
        }
        return item;
      })
    );
  };

  const filteredIntegrations = integrations.filter(
    (item) => activeCategory === "All" || item.category === activeCategory
  );

  return (
    <DashboardLayout>
      <div className="space-y-8 font-sans">
        {/* Header Block */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Boxes className="text-teal-500 w-8 h-8" /> Integrations
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Connect your OmniDimension account with other services to enhance your workflow.
          </p>
        </div>

        {/* Tab filters and search */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex flex-wrap gap-1.5 bg-slate-100 dark:bg-zinc-900 p-1 rounded-xl">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  (activeCategory === cat || (activeCategory === "All" && cat === "All"))
                    ? "bg-white dark:bg-zinc-800 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-60">
            <input
              type="text"
              placeholder="Search integrations"
              className="w-full px-4 py-2 pl-9 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
            />
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
          </div>
        </div>

        {/* Grid cards list */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredIntegrations.map((item) => (
            <div
              key={item.name}
              className="glass rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 flex flex-col justify-between"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-teal-500/10 dark:bg-teal-500/20 text-teal-500 flex items-center justify-center font-bold">
                    {item.name[0]}
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                    item.timing === "During Call" 
                      ? "bg-teal-500/10 text-teal-400 border border-teal-500/20" 
                      : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                  }`}>
                    {item.timing}
                  </span>
                </div>

                <div className="space-y-1">
                  <h3 className="font-bold text-base leading-snug">{item.name}</h3>
                  <p className="text-[10px] text-slate-500">{item.category}</p>
                </div>

                <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-3 min-h-[48px]">
                  {item.description}
                </p>
              </div>

              <div className="flex items-center justify-between pt-6 border-t border-slate-100 dark:border-zinc-800/80 mt-6">
                <button
                  onClick={() => handleToggleConnection(item.name)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    item.connected
                      ? "bg-rose-500/15 text-rose-500 hover:bg-rose-500/25"
                      : "bg-teal-500 hover:bg-teal-600 text-white shadow-md shadow-teal-500/20"
                  }`}
                >
                  {item.connected ? "Disconnect" : "Connect"}
                </button>
                {item.connected && (
                  <span className="flex items-center gap-1 text-[10px] text-emerald-500 font-bold">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Connected</span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
