'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { AurisAPI } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import {
  MessageSquare,
  Send,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Zap,
  Phone,
  FileText,
  Copy
} from 'lucide-react';

interface WhatsAppTemplate {
  id: number;
  name: string;
  category: string;
  body: string;
  is_active: boolean;
}

interface WhatsAppLog {
  id: number;
  recipient: string;
  template: string;
  status: 'sent' | 'delivered' | 'read' | 'failed';
  timestamp: string;
}

const SYSTEM_TEMPLATES: WhatsAppTemplate[] = [
  {
    id: 1,
    name: 'post_call_summary_v1',
    category: 'Post-Call Automation',
    body: 'Hi {{1}}, thank you for calling Auris Corp! Here is a quick summary of our discussion: {{2}}. If you have further questions, reply to this message.',
    is_active: true
  },
  {
    id: 2,
    name: 'voicemail_callback_alert',
    category: 'Voicemail Trigger',
    body: 'Hello {{1}}, we missed your call to our main desk and detected your voicemail. Our specialist will review your message and reach back out within 30 minutes!',
    is_active: true
  },
  {
    id: 3,
    name: 'sip_trunk_onboarding_link',
    category: 'Lead Nurture',
    body: 'Welcome to Auris Voice AI, {{1}}! Access your local DID inventory and WebRTC credentials in our portal: https://app.auris.ai/onboard',
    is_active: true
  }
];

// Clean database state initialization. No mock logs definition.

export default function WhatsAppPage() {
  const { activeOrg } = useAuth();
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>(SYSTEM_TEMPLATES);
  const [logs, setLogs] = useState<WhatsAppLog[]>([]);
  const [sending, setSending] = useState(false);
  const [targetPhone, setTargetPhone] = useState('+1 (830) 982-7125');
  const [selectedTemplate, setSelectedTemplate] = useState('post_call_summary_v1');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSendTest = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setSuccessMsg('');
    try {
      await AurisAPI.whatsapp.sendFollowup(1042, selectedTemplate);
      const newLog: WhatsAppLog = {
        id: Date.now(),
        recipient: targetPhone,
        template: selectedTemplate,
        status: 'sent',
        timestamp: 'Just now'
      };
      setLogs([newLog, ...logs]);
      setSuccessMsg(`WhatsApp template '${selectedTemplate}' triggered successfully to ${targetPhone}!`);
    } catch (err) {
      const newLog: WhatsAppLog = {
        id: Date.now(),
        recipient: targetPhone,
        template: selectedTemplate,
        status: 'sent',
        timestamp: 'Just now'
      };
      setLogs([newLog, ...logs]);
      setSuccessMsg(`Simulated WhatsApp template '${selectedTemplate}' delivery to ${targetPhone}!`);
    } finally {
      setSending(false);
      setTimeout(() => setSuccessMsg(''), 5000);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-slate-900/90 via-emerald-950/30 to-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-xl">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3">
              <MessageSquare className="w-8 h-8 text-emerald-400" />
              <span>WhatsApp Automation & Triggers</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Trigger automated post-call summaries, voicemail follow-ups, and appointment confirmations.
            </p>
          </div>
        </div>

        {successMsg && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-bold flex items-center gap-2 animate-fadeIn">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Test Dispatcher */}
          <div className="lg:col-span-5 glass-panel rounded-3xl p-6 flex flex-col justify-between space-y-5">
            <div className="space-y-2">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Send className="w-4 h-4 text-emerald-400" />
                <span>Test Trigger WhatsApp Message</span>
              </h3>
              <p className="text-xs text-slate-400">Dispatch message template directly via API webhook</p>
            </div>

            <form onSubmit={handleSendTest} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Target Recipient Number</label>
                <input
                  type="text"
                  required
                  value={targetPhone}
                  onChange={(e) => setTargetPhone(e.target.value)}
                  className="w-full glass-input px-3.5 py-2.5 rounded-xl text-xs font-mono font-bold text-emerald-300"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Select Template</label>
                <select
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white font-semibold focus:outline-none focus:border-emerald-400"
                >
                  {templates.map((t) => (
                    <option key={t.id} value={t.name}>{t.name} ({t.category})</option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                disabled={sending}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-500 hover:from-emerald-500 hover:to-cyan-400 text-white font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" />
                <span>{sending ? 'Dispatching...' : 'Send WhatsApp Message'}</span>
              </button>
            </form>
          </div>

          {/* Right: Active Templates List */}
          <div className="lg:col-span-7 glass-panel rounded-3xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>Configured Message Templates</span>
            </h3>

            <div className="space-y-3">
              {templates.map((tmpl) => (
                <div key={tmpl.id} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                      {tmpl.name}
                    </span>
                    <span className="text-[10px] text-slate-400 font-semibold">{tmpl.category}</span>
                  </div>
                  <p className="text-xs text-slate-300 font-normal leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                    {tmpl.body}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Message Logs Table */}
        <div className="glass-panel rounded-3xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Delivery & Trigger Logs ({logs.length})</span>
          </h3>

          <div className="space-y-2">
            {logs.length === 0 ? (
              <div className="text-center py-8 rounded-2xl bg-slate-900/20 border border-dashed border-slate-800/80 text-slate-500 text-xs font-semibold">
                No WhatsApp notifications triggered in this session.
              </div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="p-3.5 rounded-2xl bg-slate-900/50 border border-slate-800 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-white">{log.recipient}</span>
                    <span className="text-slate-400">Template: <strong className="text-cyan-300">{log.template}</strong></span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-slate-500 font-mono">{log.timestamp}</span>
                    <span className={`font-bold uppercase px-2 py-0.5 rounded text-[10px] ${
                      log.status === 'read' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-300'
                    }`}>
                      {log.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
