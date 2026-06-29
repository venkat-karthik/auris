"use client";

import { useAuth } from "@/components/Providers";
import { useTheme } from "next-themes";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Bot,
  Mic,
  FileText,
  Boxes,
  Phone,
  MessageSquareCode,
  PhoneCall,
  BarChart3,
  Send,
  Megaphone,
  CreditCard,
  Key,
  Users2,
  LogOut,
  Sun,
  Moon,
  Menu,
  X,
  Sparkles,
  ExternalLink
} from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, token } = useAuth();
  const { theme, setTheme } = useTheme();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [credits, setCredits] = useState<number>(0);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!token) return;
    const fetchBalance = async () => {
      try {
        const res = await fetch(`${API_URL}/billing/balance`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setCredits(data.balance_credits || 0);
        }
      } catch (err) {
        console.error("Error fetching balance:", err);
      }
    };
    fetchBalance();
  }, [token, pathname]);

  const navSetup = [
    { name: "Voice AI Assistants", href: "/agents", icon: Bot },
    { name: "Workflow Canvas", href: "/builder", icon: Sparkles },
    { name: "Clone Voice", href: "/clone-voice", icon: Mic },
    { name: "Files", href: "/files", icon: FileText },
    { name: "Integrations", href: "/integrations", icon: Boxes },
  ];

  const navMonitoring = [
    { name: "Phone Numbers", href: "/telephony", icon: Phone },
    { name: "WhatsApp Numbers", href: "/whatsapp", icon: MessageSquareCode },
    { name: "Call Logs", href: "/calls", icon: PhoneCall },
    { name: "Analytics", href: "/analytics", icon: BarChart3 },
  ];

  const navCampaigns = [
    { name: "Bulk Call", href: "/campaigns", icon: Send },
    { name: "Broadcast", href: "/broadcast", icon: Megaphone },
  ];

  const navBilling = [
    { name: "Billing", href: "/billing", icon: CreditCard },
    { name: "API", href: "/settings", icon: Key },
    { name: "Reseller", href: "/reseller", icon: Users2 },
  ];

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-[#09090b] text-slate-800 dark:text-slate-200 font-sans">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 text-slate-400 flex flex-col justify-between transform lg:translate-x-0 lg:static lg:h-screen transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col flex-1 py-5 overflow-y-auto">
          {/* Logo / Version label */}
          <div className="px-6 flex items-center justify-between border-b border-slate-800/80 pb-4">
            <Link href="/dashboard" className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center text-white font-black text-lg">
                O
              </div>
              <span className="text-xl font-bold tracking-tight text-white">
                OmniDimension
              </span>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          {/* Navigation Menu */}
          <div className="mt-6 px-3 space-y-6">
            
            {/* Voice AI Setup Section */}
            <div>
              <label className="px-3 text-[10px] font-black tracking-widest text-slate-500 uppercase block mb-2">
                Voice AI Setup
              </label>
              <div className="space-y-0.5">
                {navSetup.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(item.href + "/");
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center space-x-3 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                        active
                          ? "bg-teal-500/10 text-teal-400 font-bold border-l-2 border-teal-500"
                          : "hover:bg-slate-850 hover:text-white"
                      }`}
                    >
                      <item.icon className={`w-3.5 h-3.5 ${active ? "text-teal-400" : "text-slate-500"}`} />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Operations & Monitoring Section */}
            <div>
              <label className="px-3 text-[10px] font-black tracking-widest text-slate-500 uppercase block mb-2">
                Operations & Monitoring
              </label>
              <div className="space-y-0.5">
                {navMonitoring.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(item.href + "/");
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center space-x-3 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                        active
                          ? "bg-teal-500/10 text-teal-400 font-bold border-l-2 border-teal-500"
                          : "hover:bg-slate-850 hover:text-white"
                      }`}
                    >
                      <item.icon className={`w-3.5 h-3.5 ${active ? "text-teal-400" : "text-slate-500"}`} />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Campaigns Section */}
            <div>
              <label className="px-3 text-[10px] font-black tracking-widest text-slate-500 uppercase block mb-2">
                Campaigns
              </label>
              <div className="space-y-0.5">
                {navCampaigns.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(item.href + "/");
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center space-x-3 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                        active
                          ? "bg-teal-500/10 text-teal-400 font-bold border-l-2 border-teal-500"
                          : "hover:bg-slate-850 hover:text-white"
                      }`}
                    >
                      <item.icon className={`w-3.5 h-3.5 ${active ? "text-teal-400" : "text-slate-500"}`} />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Account & Billing Section */}
            <div>
              <label className="px-3 text-[10px] font-black tracking-widest text-slate-500 uppercase block mb-2">
                Account & Billing
              </label>
              <div className="space-y-0.5">
                {navBilling.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(item.href + "/");
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center space-x-3 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                        active
                          ? "bg-teal-500/10 text-teal-400 font-bold border-l-2 border-teal-500"
                          : "hover:bg-slate-850 hover:text-white"
                      }`}
                    >
                      <item.icon className={`w-3.5 h-3.5 ${active ? "text-teal-400" : "text-slate-500"}`} />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>

          </div>
        </div>

        {/* Footer profile panel & settings actions */}
        <div className="p-4 border-t border-slate-800 flex flex-col space-y-3 bg-slate-950/40">
          <div className="flex items-center justify-between px-2">
            <span className="text-[10px] text-slate-500 font-bold uppercase">Balance</span>
            <span className="text-xs px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 font-bold font-mono">
              ₹{credits.toFixed(2)}
            </span>
          </div>

          <a
            href="https://wa.me/918309827125"
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-center space-x-2 py-2 rounded-lg border border-slate-700 hover:border-teal-500/50 hover:bg-slate-800 text-xs font-bold text-white transition-all cursor-pointer text-center"
          >
            <span>Book a Meeting</span>
            <ExternalLink className="w-3 h-3 text-slate-500" />
          </a>

          <div className="flex items-center justify-between border-t border-slate-800 pt-3">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center font-bold text-xs">
                {user?.full_name ? user.full_name[0].toUpperCase() : "U"}
              </div>
              <div className="overflow-hidden w-28">
                <p className="text-xs font-bold text-white truncate leading-none mb-0.5">
                  {user?.full_name || "Guest User"}
                </p>
                <p className="text-[10px] text-slate-500 truncate">
                  {user?.email || ""}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              {mounted && (
                <button
                  onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                  className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                  title="Toggle Theme"
                >
                  {theme === "dark" ? <Sun className="w-4 h-4 text-amber-500" /> : <Moon className="w-4 h-4 text-indigo-400" />}
                </button>
              )}
              <button
                onClick={logout}
                className="p-1.5 rounded hover:bg-slate-800 text-rose-400 hover:text-rose-300 transition-colors cursor-pointer"
                title="Log Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden lg:h-screen">
        {/* Header bar */}
        <header className="h-16 border-b border-slate-200 dark:border-zinc-800/80 flex items-center justify-between px-6 bg-white dark:bg-zinc-950/40 backdrop-blur-sm z-30 flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-zinc-900 transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="text-sm font-bold text-slate-500 dark:text-slate-400 flex items-center space-x-1.5">
            <span>Workspace</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold border border-emerald-500/20">
              Live
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              href="/billing"
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20 text-xs font-bold hover:bg-teal-500/20 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5 text-teal-500" />
              <span>Top up wallet</span>
            </Link>
          </div>
        </header>

        {/* Content body wrapper with scroll */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50/50 dark:bg-[#070709]">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
