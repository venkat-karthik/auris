'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { AurisAPI } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import {
  Database,
  Upload,
  Globe,
  Trash2,
  FileText,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Link as LinkIcon,
  Search,
  Cpu,
  Layers
} from 'lucide-react';

interface KnowledgeDoc {
  id: number;
  title: string;
  source_type: 'file' | 'url';
  source_url?: string;
  chunk_count: number;
  status: 'indexed' | 'processing' | 'failed';
  created_at: string;
}

// Clean database state initialization. No mock documents definition.

export default function KnowledgePage() {
  const { activeOrg } = useAuth();
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [loading, setLoading] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const [scraping, setScraping] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    async function loadDocs() {
      try {
        const res = await AurisAPI.knowledge.list();
        if (Array.isArray(res)) setDocs(res);
      } catch (err) {
        console.warn('Backend KB fetch error:', err);
      }
    }
    loadDocs();
  }, [activeOrg]);

  const handleScrapeUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput) return;
    setScraping(true);
    try {
      const added = await AurisAPI.knowledge.scrapeUrl(urlInput);
      setDocs([added, ...docs]);
      setUrlInput('');
    } catch (err) {
      console.error('Scrape error:', err);
      alert('Failed to ingest URL. Please verify your backend server connection.');
    } finally {
      setScraping(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const added = await AurisAPI.knowledge.uploadFile(file);
      setDocs([added, ...docs]);
    } catch (err) {
      console.error('File upload error:', err);
      alert('Failed to upload file. Check if your backend server is active.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete these vector embeddings?')) return;
    try {
      await AurisAPI.knowledge.delete(id);
      setDocs(docs.filter((d) => d.id !== id));
    } catch (err) {
      setDocs(docs.filter((d) => d.id !== id));
    }
  };

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-slate-900/90 via-indigo-950/30 to-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-xl">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400 mb-1">
              <Sparkles className="w-4 h-4 animate-spin" style={{ animationDuration: '6s' }} />
              <span>pgvector 1536d Hybrid RAG Pipeline</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3">
              <Database className="w-8 h-8 text-indigo-400" />
              <span>Knowledge Base & Semantic RAG</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1">
              Upload PDF/Markdown guides or ingest web URLs for real-time semantic recall during sub-300ms agent calls.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start sm:self-center">
            <label className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-sm shadow-xl shadow-indigo-500/25 cursor-pointer transition-all transform hover:-translate-y-0.5">
              <Upload className="w-4 h-4" />
              <span>{uploading ? 'Embedding...' : 'Upload Document'}</span>
              <input type="file" onChange={handleFileUpload} disabled={uploading} className="hidden" accept=".pdf,.md,.txt,.doc,.docx" />
            </label>
          </div>
        </div>

        {/* Ingestion Panels */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* File Drop Box */}
          <div className="glass-panel rounded-3xl p-6 flex flex-col justify-between space-y-4 border-dashed border-indigo-500/30 hover:border-indigo-500/60 transition-all">
            <div className="space-y-2">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-400" />
                <span>Document File Upload</span>
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed font-normal">
                Drop standard PDF, TXT, or Markdown documents. Our backend automatically chunks text and stores `pgvector` 1536-dimensional embeddings.
              </p>
            </div>

            <label className="w-full py-8 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center gap-2 cursor-pointer hover:bg-slate-800/60 transition-all group">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
                <Upload className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-slate-300 group-hover:text-white transition-colors">
                {uploading ? 'Processing & Indexing Chunks...' : 'Click or Drag PDF / MD to Upload'}
              </span>
              <span className="text-[10px] text-slate-500">Maximum file size: 25 MB per upload</span>
              <input type="file" onChange={handleFileUpload} disabled={uploading} className="hidden" />
            </label>
          </div>

          {/* URL Scraper Input */}
          <div className="glass-panel rounded-3xl p-6 flex flex-col justify-between space-y-4">
            <div className="space-y-2">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Globe className="w-5 h-5 text-cyan-400" />
                <span>Live URL Scraping & Ingestion</span>
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed font-normal">
                Enter any documentation URL or product page. Our scraping worker extracts semantic markdown and indexes it into the agent memory pool.
              </p>
            </div>

            <form onSubmit={handleScrapeUrl} className="space-y-3">
              <div className="relative">
                <LinkIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="url"
                  required
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://docs.example.com/webrtc-guide"
                  className="w-full glass-input pl-10 pr-4 py-3 rounded-2xl text-xs font-mono"
                />
              </div>

              <button
                type="submit"
                disabled={scraping}
                className="w-full py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-bold text-xs transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Cpu className="w-4 h-4 text-cyan-400 animate-pulse" />
                <span>{scraping ? 'Scraping & Indexing URL...' : 'Scrape URL into Vector DB'}</span>
              </button>
            </form>
          </div>
        </div>

        {/* Vector Embeddings Table */}
        <div className="glass-panel rounded-3xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>Indexed Vector Knowledge Pool ({docs.length})</span>
              </h2>
              <p className="text-xs text-slate-400">Available for semantic search (`AurisAPI.knowledge.query()`)</p>
            </div>
            <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              pgvector Active
            </span>
          </div>

          <div className="space-y-3">
            {docs.length === 0 ? (
              <div className="text-center py-12 rounded-2xl bg-slate-900/20 border border-dashed border-slate-800/80">
                <Database className="w-8 h-8 text-slate-600 mx-auto mb-3 animate-pulse" />
                <p className="text-sm font-semibold text-slate-400">No vector documents indexed</p>
                <p className="text-xs text-slate-500 mt-1">Upload a PDF/Word file or input a URL above to chunk and index semantic content.</p>
              </div>
            ) : (
              docs.map((doc) => (
                <div
                  key={doc.id}
                  className="p-4 rounded-2xl bg-slate-900/60 hover:bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-bold ${
                      doc.source_type === 'file' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                    }`}>
                      {doc.source_type === 'file' ? <FileText className="w-5 h-5" /> : <Globe className="w-5 h-5" />}
                    </div>

                    <div className="min-w-0">
                      <h4 className="text-sm font-bold text-white truncate">{doc.title}</h4>
                      <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                        <span className="font-semibold text-cyan-300">{doc.chunk_count} Vector Chunks</span>
                        <span>•</span>
                        <span>Indexed on {doc.created_at}</span>
                        <span>•</span>
                        <span className="text-emerald-400 font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> {doc.status}
                        </span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2.5 rounded-xl bg-slate-950 hover:bg-red-500/10 border border-slate-800 hover:border-red-500/30 text-slate-400 hover:text-red-400 transition-all flex-shrink-0"
                    title="Delete Embedding"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
