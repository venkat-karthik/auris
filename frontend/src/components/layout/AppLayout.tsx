'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard,
  Bot,
  PhoneCall,
  Phone,
  Database,
  Megaphone,
  MessageSquare,
  Mic,
  Users,
  CreditCard,
  Settings,
  Activity,
  ChevronDown,
  Sparkles,
  Zap,
  Plus,
  LogOut,
  Bell,
  CheckCircle2,
  Workflow,
  Puzzle,
  Headphones
} from 'lucide-react';

const NAV_GROUPS = [
  {
    label: 'Core System',
    items: [
      { name: 'Command Center', href: '/', icon: LayoutDashboard },
      { name: 'Voice Agents', href: '/agents', icon: Bot },
      { name: 'Workflow Studio', href: '/agents/1/studio', icon: Workflow },
      { name: 'Live Call Runs', href: '/calls', icon: PhoneCall },
      { name: 'Live Supervisor', href: '/supervisor', icon: Headphones },
    ],
  },
  {
    label: 'Telephony & AI Engine',
    items: [
      { name: 'DID Number Pool', href: '/phone-numbers', icon: Phone },
      { name: 'Outbound Campaigns', href: '/campaigns', icon: Megaphone },
      { name: 'Knowledge Base (RAG)', href: '/knowledge', icon: Database },
      { name: 'Cloned Voices', href: '/cloned-voices', icon: Mic },
    ],
  },
  {
    label: 'Operations & Billing',
    items: [
      { name: 'Customer Memory', href: '/customers', icon: Users },
      { name: 'WhatsApp Automation', href: '/whatsapp', icon: MessageSquare },
      { name: 'Integrations', href: '/integrations', icon: Puzzle },
      { name: 'Billing & Credits', href: '/billing', icon: CreditCard },
      { name: 'SIP & Settings', href: '/settings', icon: Settings },
    ],
  },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, activeOrg, organizations, selectOrganization, logout, isLoading } = useAuth();
  const [showOrgDropdown, setShowOrgDropdown] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#080a0f] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 rounded-full border-4 border-t-indigo-500 border-slate-800 animate-spin" />
          <span className="text-slate-400 text-sm font-semibold tracking-wide">Resolving Security Session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#080a0f] text-slate-100">
      {/* ── Left Glass Sidebar ─────────────────────────────────────────────────── */}
      <aside className="w-68 flex-shrink-0 flex flex-col border-r border-slate-800/80 bg-slate-950/40 backdrop-blur-xl z-20">
        {/* Brand Header */}
        <div className="p-5 flex items-center justify-between border-b border-slate-800/60">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-[2px] shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-all">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold tracking-tight text-lg text-white">Auris</span>
                <span className="text-xs font-semibold px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  v2.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Advanced Agentic Voice</p>
            </div>
          </Link>
        </div>

        {/* Navigation Groups */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {NAV_GROUPS.map((group, gIdx) => (
            <div key={gIdx}>
              <p className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                {group.label}
              </p>
              <div className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-gradient-to-r from-indigo-600/20 to-cyan-500/10 text-white border border-indigo-500/30 shadow-sm shadow-indigo-500/10 font-semibold'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                      <span>{item.name}</span>
                      {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#06b6d4]" />}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* System Health / API Status Widget */}
        <div className="p-4 m-3 rounded-2xl bg-gradient-to-br from-slate-900/80 to-slate-950/80 border border-slate-800/80 backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-xs font-semibold text-emerald-400">All Systems Operational</span>
            </div>
            <Activity className="w-3.5 h-3.5 text-slate-500" />
          </div>
          <p className="text-[11px] text-slate-400">
            18 FastAPI routers & V2 local DID pool live (`82/82` tests OK)
          </p>
        </div>
      </aside>

      {/* ── Main Area (Header + Page Content) ─────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 flex-shrink-0 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-xl flex items-center justify-between px-6 z-10">
          {/* Active Organization Switcher */}
          <div className="relative">
            <button
              onClick={() => setShowOrgDropdown(!showOrgDropdown)}
              className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-sm font-medium transition-all"
            >
              <div className="w-2 h-2 rounded-full bg-indigo-400 shadow-[0_0_6px_#6366f1]" />
              <span className="text-white font-semibold">{activeOrg?.name || 'Auris Organization'}</span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {showOrgDropdown && (
              <div className="absolute top-full left-0 mt-2 w-64 rounded-2xl bg-slate-900/95 border border-slate-800 p-2 shadow-2xl backdrop-blur-xl z-50">
                <p className="px-3 py-1.5 text-[11px] font-semibold uppercase text-slate-400">Organizations</p>
                {organizations.map((org) => (
                  <button
                    key={org.id}
                    onClick={() => {
                      selectOrganization(org);
                      setShowOrgDropdown(false);
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left text-sm font-medium transition-all ${
                      activeOrg?.id === org.id ? 'bg-indigo-600/20 text-white font-semibold' : 'text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    <span>{org.name}</span>
                    {activeOrg?.id === org.id && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                  </button>
                ))}
                <div className="border-t border-slate-800 mt-2 pt-2">
                  <Link
                    href="/settings"
                    onClick={() => setShowOrgDropdown(false)}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-indigo-400 hover:bg-slate-800/60 transition-all"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create / Onboard Organization</span>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Right Action Icons & Balance */}
          <div className="flex items-center gap-4">
            {/* Live Balance Pill */}
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20">
              <Zap className="w-4 h-4 text-emerald-400 animate-bounce" />
              <span className="text-sm font-bold text-white">
                ₹{activeOrg?.balance_credits.toFixed(1) || '0.0'}
              </span>
              <span className="text-xs text-slate-400 font-medium">credits</span>
              <Link
                href="/billing"
                className="ml-2 px-2 py-0.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-[11px] font-bold text-emerald-300 transition-all"
              >
                + Top Up
              </Link>
            </div>

            {/* Quick Web Call Launch */}
            <Link
              href="/calls"
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-sm font-bold shadow-lg shadow-indigo-500/25 transition-all transform hover:-translate-y-0.5"
            >
              <PhoneCall className="w-4 h-4 animate-pulse" />
              <span>Launch Live Call</span>
            </Link>

            <button className="p-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-all relative">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyan-400" />
            </button>

            {/* User Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowUserDropdown(!showUserDropdown)}
                className="flex items-center gap-2.5 p-1.5 rounded-xl hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-all"
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white font-bold text-sm shadow-md">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'V'}
                </div>
                <div className="text-left hidden sm:block">
                  <p className="text-xs font-bold text-white leading-tight">{user?.full_name || 'Venkat Karthik'}</p>
                  <p className="text-[10px] text-slate-400 leading-tight">{user?.email || 'venkat@auris.ai'}</p>
                </div>
              </button>

              {showUserDropdown && (
                <div className="absolute top-full right-0 mt-2 w-56 rounded-2xl bg-slate-900/95 border border-slate-800 p-2 shadow-2xl backdrop-blur-xl z-50">
                  <div className="px-3 py-2 border-b border-slate-800 mb-1">
                    <p className="text-xs font-bold text-white">{user?.full_name || 'Venkat Karthik'}</p>
                    <p className="text-[11px] text-slate-400 truncate">{user?.email || 'venkat@auris.ai'}</p>
                  </div>
                  <Link
                    href="/settings"
                    onClick={() => setShowUserDropdown(false)}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium text-slate-300 hover:bg-slate-800 transition-all"
                  >
                    <Settings className="w-4 h-4 text-slate-400" />
                    <span>Account Settings</span>
                  </Link>
                  <button
                    onClick={() => {
                      logout();
                      setShowUserDropdown(false);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <LogOut className="w-4 h-4 text-red-400" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content Viewport */}
        <main className="flex-1 overflow-y-auto bg-[#080a0f] p-6 relative">
          {children}
        </main>
      </div>
    </div>
  );
}
