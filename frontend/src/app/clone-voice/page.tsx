"use client";

import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Mic,
  Upload,
  Play,
  CheckCircle,
  HelpCircle,
  Volume2,
  Trash2,
  Loader2
} from "lucide-react";

interface ClonedVoice {
  id: string;
  name: string;
  samplesCount: number;
  status: "ready" | "processing";
  created_at: string;
}

export default function CloneVoicePage() {
  const [voices, setVoices] = useState<ClonedVoice[]>([
    {
      id: "voice-1",
      name: "Karthik Professional Voice",
      samplesCount: 1,
      status: "ready",
      created_at: "2 days ago"
    }
  ]);

  const [voiceName, setVoiceName] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [cloningLoading, setCloningLoading] = useState(false);

  const startRecording = () => {
    setIsRecording(true);
    toast.info("Recording microphone audio... Speak clearly.");
  };

  const stopRecording = () => {
    setIsRecording(false);
    toast.success("Voice sample recorded successfully!");
    setRecordedBlob(new Blob());
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
      toast.success(`Voice sample file loaded: ${e.target.files[0].name}`);
    }
  };

  const handleCloneVoice = (e: React.FormEvent) => {
    e.preventDefault();
    if (!voiceName.trim()) {
      toast.error("Please enter a name for the cloned voice");
      return;
    }
    if (!recordedBlob && !uploadFile) {
      toast.error("Please record audio or upload a voice sample first");
      return;
    }

    setCloningLoading(true);
    setTimeout(() => {
      const newVoice: ClonedVoice = {
        id: `voice-${Date.now()}`,
        name: voiceName,
        samplesCount: 1,
        status: "processing",
        created_at: "Just now"
      };
      setVoices((prev) => [newVoice, ...prev]);
      setVoiceName("");
      setUploadFile(null);
      setRecordedBlob(null);
      setCloningLoading(false);
      toast.success("AI voice cloning request initialized!");
    }, 1200);
  };

  const handleDeleteVoice = (id: string) => {
    setVoices((prev) => prev.filter((v) => v.id !== id));
    toast.success("Cloned voice deleted");
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 font-sans">
        {/* Title Block */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Mic className="text-teal-500 w-8 h-8" /> Clone Voice
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Create custom AI voices by uploading audio samples. Minimum 20 seconds, recommended 30–60 seconds of clear speech.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main workspace */}
          <div className="lg:col-span-2 space-y-6">
            <form onSubmit={handleCloneVoice} className="glass rounded-2xl p-6 space-y-6">
              <h2 className="text-lg font-bold">Clone Your Voice</h2>
              
              <div className="space-y-3">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Upload sample or record live</label>
                <div className="flex gap-4">
                  <button
                    type="button"
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                      isRecording 
                        ? "bg-rose-500/20 text-rose-500 border-rose-500" 
                        : "bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-white border-slate-200 dark:border-zinc-700"
                    }`}
                  >
                    <Mic className="w-4 h-4" />
                    <span>{isRecording ? "Stop Recording" : "Record Voice"}</span>
                  </button>
                  <label className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-white border border-slate-200 dark:border-zinc-700 hover:border-teal-500/50 transition-all cursor-pointer">
                    <Upload className="w-4 h-4 text-teal-400" />
                    <span>{uploadFile ? uploadFile.name : "Upload File"}</span>
                    <input type="file" accept="audio/*" onChange={handleFileUpload} className="hidden" />
                  </label>
                </div>
              </div>

              {/* Record status visualizer */}
              {isRecording && (
                <div className="p-8 border border-rose-500/30 bg-rose-500/5 rounded-2xl flex flex-col items-center justify-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-rose-500 animate-ping flex items-center justify-center text-white">
                    <Mic className="w-6 h-6" />
                  </div>
                  <p className="text-xs font-bold text-rose-500">Speaking... Speak for at least 20 seconds.</p>
                  <p className="text-[10px] text-slate-400">Keep a quiet room, 15-30 cm away from your mic, speak in normal pace.</p>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Voice Name *</label>
                <input
                  type="text"
                  required
                  value={voiceName}
                  onChange={(e) => setVoiceName(e.target.value)}
                  placeholder="e.g. My Professional Voice"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-1 focus:ring-teal-500 text-xs"
                />
              </div>

              <button
                type="submit"
                disabled={cloningLoading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-semibold text-xs shadow-lg shadow-teal-500/25 transition-all flex items-center justify-center space-x-2 cursor-pointer"
              >
                {cloningLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Clone voice</span>}
              </button>
            </form>
          </div>

          {/* Voices list */}
          <div className="space-y-6">
            <div className="glass rounded-2xl p-6 space-y-4">
              <h2 className="text-lg font-bold">My Cloned Voices</h2>
              {voices.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center">
                  You haven't cloned any custom voices yet.
                </p>
              ) : (
                <div className="space-y-3">
                  {voices.map((v) => (
                    <div key={v.id} className="p-3 rounded-xl border border-slate-150 dark:border-zinc-800/80 bg-slate-50/50 dark:bg-zinc-900/40 flex items-center justify-between gap-3 text-xs">
                      <div>
                        <p className="font-bold text-slate-800 dark:text-white flex items-center gap-1.5">
                          <span>{v.name}</span>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                            v.status === "ready" ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500"
                          }`}>
                            {v.status}
                          </span>
                        </p>
                        <p className="text-[10px] text-slate-400 mt-1">Created {v.created_at}</p>
                      </div>
                      <button
                        onClick={() => handleDeleteVoice(v.id)}
                        className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-500/10 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
