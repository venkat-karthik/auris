"use client";

import { useAuth } from "@/components/Providers";
import { useTheme } from "next-themes";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  UserSquare2,
  PhoneCall,
  CreditCard,
  Settings,
  LogOut,
  Sun,
  Moon,
  Menu,
  X,
  User
} from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Agents", href: "/agents", icon: UserSquare2 },
    { name: "Call Logs", href: "/calls", icon: PhoneCall },
    { name: "Billing", href: "/billing", icon: CreditCard },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-[#07070a] text-slate-800 dark:text-slate-200">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 glass shadow-lg flex flex-col justify-between transform lg:translate-x-0 lg:static lg:h-screen transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col flex-1 py-6">
          {/* Logo / Title */}
          <div className="px-6 flex items-center justify-between">
            <Link href="/dashboard" className="flex items-center space-x-2">
              <span className="text-2xl font-black bg-gradient-to-r from-teal-500 to-indigo-600 bg-clip-text text-transparent dark:from-teal-400 dark:to-indigo-400">
                Auris
              </span>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1.5 rounded-lg hover:bg-slate-200/50 dark:hover:bg-zinc-800/50 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Nav items */}
          <nav className="mt-8 px-4 space-y-1">
            {navigation.map((item) => {
              const active = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                    active
                      ? "bg-gradient-to-r from-teal-500/10 to-indigo-500/10 text-teal-600 dark:text-teal-400 border-l-4 border-teal-500"
                      : "hover:bg-slate-200/30 dark:hover:bg-zinc-800/20 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                  }`}
                >
                  <item.icon className={`w-5 h-5 ${active ? "text-teal-500" : "text-slate-400 dark:text-slate-500"}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer profile panel & logout */}
        <div className="p-4 border-t border-slate-100 dark:border-zinc-800/60 flex flex-col space-y-3">
          <div className="flex items-center space-x-3 px-2">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-teal-400 to-indigo-500 flex items-center justify-center text-white font-bold text-sm">
              {user?.full_name ? user.full_name[0].toUpperCase() : "U"}
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-bold truncate leading-none mb-1">
                {user?.full_name || "User Profile"}
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 truncate">
                {user?.email || ""}
              </p>
            </div>
          </div>

          <button
            onClick={logout}
            className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm font-semibold text-rose-500 dark:text-rose-400 hover:bg-rose-500/5 dark:hover:bg-rose-500/10 transition-colors cursor-pointer"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden lg:h-screen">
        {/* Header bar */}
        <header className="h-16 border-b border-slate-200/60 dark:border-zinc-800/60 flex items-center justify-between px-6 bg-white/50 dark:bg-zinc-950/50 backdrop-blur-sm z-30 flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg hover:bg-slate-200/50 dark:hover:bg-zinc-800/50 transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="text-sm font-bold text-slate-500 dark:text-slate-400 flex items-center space-x-1.5">
            <span>Auris Cloud</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-black border border-emerald-500/20">
              Live
            </span>
          </div>

          {/* Theme toggler */}
          <div className="flex items-center space-x-4">
            {mounted && (
              <button
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="p-2 rounded-xl hover:bg-slate-200/50 dark:hover:bg-zinc-800/50 transition-colors cursor-pointer"
                title="Toggle Theme"
              >
                {theme === "dark" ? <Sun className="w-5 h-5 text-amber-500" /> : <Moon className="w-5 h-5 text-indigo-500" />}
              </button>
            )}
          </div>
        </header>

        {/* Content body wrapper with scroll */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
