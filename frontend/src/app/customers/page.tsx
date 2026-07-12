'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { AurisAPI } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import {
  Users,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  PhoneCall,
  UserCheck,
  Tag,
  Database,
  Sliders
} from 'lucide-react';

interface CustomerProfile {
  id: number;
  phone_number: string;
  name?: string;
  total_calls: number;
  last_call_at: string;
  memory_kv?: { [key: string]: string };
}

// Clean database state initialization. No mock customers definition.

export default function CustomersPage() {
  const { activeOrg } = useAuth();
  const [customers, setCustomers] = useState<CustomerProfile[]>([]);
  const [selectedCust, setSelectedCust] = useState<CustomerProfile | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    async function fetchCustomers() {
      try {
        const res = await AurisAPI.customers.list();
        if (Array.isArray(res)) {
          setCustomers(res);
          if (res.length > 0) {
            setSelectedCust(res[0]);
          }
        }
      } catch (err) {
        console.warn('Customers memory API offline:', err);
      }
    }
    fetchCustomers();
  }, [activeOrg]);

  const filtered = customers.filter((c) =>
    (!searchQuery || c.phone_number.includes(searchQuery) || (c.name && c.name.toLowerCase().includes(searchQuery.toLowerCase())))
  );

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-slate-900/90 via-indigo-950/30 to-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-xl">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3">
              <Users className="w-8 h-8 text-cyan-400" />
              <span>Customer Memory & Profile Engine</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Persistent key-value memory (`memory_kv`) extracted across call runs to give agents context on returning callers.
            </p>
          </div>

          <div className="relative w-full sm:w-72 self-start sm:self-center">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search phone or name..."
              className="w-full glass-input pl-10 pr-4 py-2 rounded-xl text-xs"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {customers.length === 0 ? (
            <div className="lg:col-span-12 text-center py-20 rounded-3xl bg-slate-950/45 border border-dashed border-slate-800 backdrop-blur-md">
              <Users className="w-12 h-12 text-slate-600 mx-auto mb-4 animate-pulse" />
              <h3 className="text-lg font-bold text-slate-300">No Customers Found</h3>
              <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
                No customer profiles have been created yet. Once agents execute calls, customer names, numbers, and extracted semantic memories will appear here automatically.
              </p>
            </div>
          ) : (
            <>
              {/* Left: Directory Feed */}
              <div className="lg:col-span-5 space-y-3 max-h-[640px] overflow-y-auto pr-1">
                {filtered.map((cust) => {
                  const isSelected = selectedCust?.id === cust.id;
                  return (
                    <div
                      key={cust.id}
                      onClick={() => setSelectedCust(cust)}
                      className={`p-4 rounded-2xl cursor-pointer transition-all border flex items-center justify-between gap-4 ${
                        isSelected
                          ? 'bg-slate-900/95 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)] font-semibold'
                          : 'bg-slate-900/50 hover:bg-slate-900/80 border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500/20 to-cyan-500/20 border border-indigo-500/30 flex items-center justify-center text-cyan-300 font-extrabold text-sm">
                          {cust.name ? cust.name.charAt(0) : 'C'}
                        </div>
                        <div>
                          <p className="text-sm font-extrabold text-white leading-tight">{cust.name || cust.phone_number}</p>
                          <p className="text-[11px] text-slate-400 font-mono mt-0.5">{cust.phone_number}</p>
                        </div>
                      </div>

                      <div className="text-right flex-shrink-0">
                        <span className="text-xs font-bold text-cyan-300 bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700">
                          {cust.total_calls} Calls
                        </span>
                        <p className="text-[10px] text-slate-500 font-mono mt-1">{cust.last_call_at.split(' ')[0]}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {/* Right: Memory Inspector */}
          <div className="lg:col-span-7 glass-panel rounded-3xl p-6 flex flex-col justify-between space-y-6">
            {selectedCust ? (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-extrabold text-white">{selectedCust.name || selectedCust.phone_number}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                        Verified Contact
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-2">
                      <PhoneCall className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{selectedCust.phone_number} • Last Active: {selectedCust.last_call_at}</span>
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Extracted Semantic Memory Key-Value Store (`memory_kv`)</span>
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed font-normal">
                    When this customer calls any agent, this memory dictionary is automatically injected into the system prompt so the AI can recall past context immediately without asking repetitive questions.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    {selectedCust.memory_kv && Object.entries(selectedCust.memory_kv).map(([key, val], idx) => (
                      <div key={idx} className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
                        <p className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
                          {key.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs text-white font-medium">{val}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-purple-400" />
                    <span>Auto-Summarization Worker</span>
                  </span>
                  <span className="text-emerald-400 font-semibold">Enabled (Refreshed after every call)</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-20 text-slate-500 text-sm">Select any customer on the left to inspect semantic memory logs.</div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
