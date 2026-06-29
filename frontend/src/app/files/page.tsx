"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  FileText,
  Upload,
  Database,
  Trash2,
  CheckCircle,
  Clock,
  Loader2,
  FileUp
} from "lucide-react";

interface KbDocument {
  id: number;
  filename: string;
  file_size: number;
  status: "pending" | "processing" | "completed" | "failed";
  chunk_count: number;
  created_at: string;
}

export default function KnowledgeBaseFilesPage() {
  const { token } = useAuth();
  const [documents, setDocuments] = useState<KbDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchDocuments = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/knowledge-base`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error("Error loading RAG documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [token]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
    }
  };

  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      toast.error("Please select a document file to upload");
      return;
    }

    setUploadLoading(true);
    const formData = new FormData();
    formData.append("file", uploadFile);

    try {
      const res = await fetch(`${API_URL}/knowledge-base/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        toast.success("Document uploaded successfully! Parsing and indexing vectors in background.");
        setUploadFile(null);
        fetchDocuments();
      } else {
        const data = await res.json();
        toast.error(data.detail || "Failed to upload document");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error during document ingestion");
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDeleteDocument = async (id: number) => {
    if (!confirm("Are you sure you want to delete this document? All indexing vector embeddings will be wiped.")) return;

    try {
      const res = await fetch(`${API_URL}/knowledge-base/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        toast.success("Document and RAG embeddings removed successfully");
        fetchDocuments();
      } else {
        toast.error("Failed to remove document");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error deleting document");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Title Block */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <FileText className="text-teal-500 w-8 h-8" /> Knowledge Base RAG Ingestion
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Upload enterprise PDF documents, FAQs, and business manuals. Files are parsed, chunked, and embedded into pgvector automatically.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* List of files */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Ingested Documents</h2>
              
              {loading ? (
                <div className="py-8 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-teal-500" /></div>
              ) : documents.length === 0 ? (
                <p className="text-xs text-slate-400 py-12 text-center">
                  No business documents found. Use the uploader to index your knowledge base.
                </p>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-zinc-800/80">
                  {documents.map((doc) => (
                    <div key={doc.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 dark:text-white">{doc.filename}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                            doc.status === "completed" ? "bg-emerald-500/10 text-emerald-500" :
                            doc.status === "processing" ? "bg-amber-500/10 text-amber-500" :
                            doc.status === "failed" ? "bg-rose-500/10 text-rose-500" : "bg-slate-200 text-slate-500"
                          }`}>
                            {doc.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-slate-400">
                          <span className="flex items-center gap-1 font-mono text-[10px]">{(doc.file_size / 1024).toFixed(1)} KB</span>
                          <span className="flex items-center gap-1"><Database className="w-3.5 h-3.5 text-teal-500" /> {doc.chunk_count} Vector Chunks</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="p-2 rounded-xl text-rose-500 hover:bg-rose-500/10 transition-colors"
                          title="Delete Document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Ingest uploader */}
          <div className="space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">Upload Document</h2>
              <form onSubmit={handleUploadDocument} className="space-y-5">
                <div className="space-y-2">
                  <div className="border-2 border-dashed border-slate-200 dark:border-zinc-800 rounded-2xl p-8 text-center cursor-pointer hover:border-teal-500/50 transition-colors relative">
                    <input
                      type="file"
                      accept=".pdf,.txt"
                      onChange={handleFileChange}
                      className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                    />
                    <div className="flex flex-col items-center space-y-3">
                      <FileUp className="w-10 h-10 text-teal-500" />
                      <span className="text-xs font-bold text-slate-800 dark:text-white">
                        {uploadFile ? uploadFile.name : "Drag or select PDF / TXT"}
                      </span>
                      <span className="text-[10px] text-slate-400">Supported formats: PDF, TXT (Max 50MB)</span>
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={uploadLoading}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs shadow-lg shadow-teal-500/25 transition-all flex items-center justify-center space-x-2 cursor-pointer"
                >
                  {uploadLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <span>Ingest Document</span>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
