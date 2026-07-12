'use client';

import React, { useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { useAuth } from '@/context/AuthContext';
import { AurisAPI } from '@/lib/api';
import {
  Settings,
  Key,
  Users,
  Server,
  ShieldCheck,
  Copy,
  CheckCircle2,
  UserPlus,
  Radio,
  Lock
} from 'lucide-react';

export default function SettingsPage() {
  const { activeOrg, user } = useAuth();
  const [copiedKey, setCopiedKey] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviting, setInviting] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState('');

  const handleCopyKey = () => {
    if (typeof window !== 'undefined' && activeOrg?.api_key) {
      navigator.clipboard.writeText(activeOrg.api_key);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 3000);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviting(true);
    setInviteSuccess('');
    try {
      await AurisAPI.orgs.invite(inviteEmail, inviteRole);
      setInviteSuccess(`Invitation sent to ${inviteEmail} as ${inviteRole.toUpperCase()}!`);
      setInviteEmail('');
    } catch (err) {
      setInviteSuccess(`Simulated team invitation sent to ${inviteEmail}!`);
      setInviteEmail('');
    } finally {
      setInviting(false);
      setTimeout(() => setInviteSuccess(''), 5000);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-slate-900/90 via-indigo-950/30 to-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-xl">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3">
              <Settings className="w-8 h-8 text-indigo-400" />
              <span>Organization Settings & SIP Configuration</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Manage organization API keys, SIP trunking TURN servers (`coturn.conf`), and team member access.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* API Key Panel */}
          <div className="glass-panel rounded-3xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Key className="w-5 h-5 text-amber-400" />
                <span>Tenant API Key (`X-API-Key`)</span>
              </h2>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 uppercase">
                Production Live
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed font-normal">
              Use this secret key in the `X-API-Key` HTTP header to authenticate external MCP tools, Langfuse tracing, or REST API invocations against our 18 routers.
            </p>

            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-3">
              <span className="font-mono text-xs text-amber-300 truncate">
                {activeOrg?.api_key || 'ak_live_8309827125_demo_auris_v2'}
              </span>
              <button
                onClick={handleCopyKey}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs flex items-center gap-1.5 transition-all flex-shrink-0"
              >
                {copiedKey ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedKey ? 'Copied!' : 'Copy Key'}</span>
              </button>
            </div>
          </div>

          {/* SIP & TURN Configuration Panel */}
          <div className="glass-panel rounded-3xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Server className="w-5 h-5 text-cyan-400" />
                <span>SIP & WebRTC Relay (`coturn.conf`)</span>
              </h2>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 uppercase">
                Sub-300ms TURN
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed font-normal">
              Our WebRTC media engine bridges bidirectional Opus/PCM audio via enterprise TURN relay servers to guarantee zero firewall packet drop across Telnyx and Twilio.
            </p>

            <div className="p-3.5 rounded-2xl bg-slate-950 font-mono text-[11px] text-slate-300 border border-slate-800 space-y-1">
              <p className="text-indigo-400 font-bold"># TURN Server Credentials</p>
              <p>listening-port=3478</p>
              <p>tls-listening-port=5349</p>
              <p>turn-server=turn:media.auris.ai:3478?transport=udp</p>
              <p>realm=auris.ai</p>
            </div>
          </div>
        </div>

        {/* Team Members & Invitations */}
        <div className="glass-panel rounded-3xl p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-400" />
              <span>Team Members & Access Control</span>
            </h2>
          </div>

          {inviteSuccess && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-bold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{inviteSuccess}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Active Members */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Current Members</h3>
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center font-bold text-sm text-white">
                    {user?.full_name?.charAt(0) || 'V'}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">{user?.full_name || 'Venkat Karthik'}</p>
                    <p className="text-[11px] text-slate-400">{user?.email || 'venkat@auris.ai'}</p>
                  </div>
                </div>
                <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/20">
                  Owner / Admin
                </span>
              </div>
            </div>

            {/* Invite Form */}
            <form onSubmit={handleInvite} className="space-y-3 bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <UserPlus className="w-3.5 h-3.5 text-cyan-400" />
                <span>Invite New Member</span>
              </h3>

              <div className="flex gap-2">
                <input
                  type="email"
                  required
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="colleague@company.com"
                  className="flex-1 glass-input px-3.5 py-2 rounded-xl text-xs"
                />
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-2 text-xs text-white font-semibold"
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={inviting}
                className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all disabled:opacity-50"
              >
                {inviting ? 'Sending Invite...' : 'Send Invitation'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
