/* eslint-disable react/no-unescaped-entities */
"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Mail, Lock, User, Building, ArrowRight, Loader2 } from "lucide-react";
import { useAuth } from "@/components/Providers";

export default function SignupPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [loading, setLoading] = useState(false);

  // Verification state
  const [showVerify, setShowVerify] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [verifyLoading, setVerifyLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !fullName || !orgName) {
      toast.error("Please fill in all fields");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          org_name: orgName,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        toast.success("Account created! Verification code sent to email.");
        setShowVerify(true);
      } else {
        toast.error(data.detail || "Signup failed");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verificationCode || verificationCode.length !== 6) {
      toast.error("Please enter the 6-digit verification code");
      return;
    }

    setVerifyLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          code: verificationCode
        })
      });
      const data = await res.json();
      if (res.ok) {
        toast.success("Email verified! Logging in...");
        login(data.access_token, data.user_id, data.org_id);
      } else {
        toast.error(data.detail || "Invalid code or code expired");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error verifying code");
    } finally {
      setVerifyLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col justify-center items-center px-4 py-12 bg-gradient-soothing">
      <div className="w-full max-w-md glass rounded-2xl shadow-2xl overflow-hidden p-8 flex flex-col space-y-6">
        <div className="flex flex-col space-y-2 text-center">
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-fuchsia-500 via-purple-600 to-indigo-500 bg-clip-text text-transparent dark:from-fuchsia-400 dark:to-cyan-400">
            Auris
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Deploy your conversational voice AI receptionist in 5 minutes
          </p>
        </div>

        {!showVerify ? (
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Full Name</label>
              <div className="relative flex items-center">
                <User className="absolute left-3 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Venkat Karthik"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500 transition-all text-sm"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Email Address</label>
              <div className="relative flex items-center">
                <Mail className="absolute left-3 w-5 h-5 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@domain.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500 transition-all text-sm"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Organization Name</label>
              <div className="relative flex items-center">
                <Building className="absolute left-3 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="Acme Corp"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500 transition-all text-sm"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Password</label>
              <div className="relative flex items-center">
                <Lock className="absolute left-3 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500 transition-all text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl bg-gradient-to-r from-fuchsia-500 to-purple-600 hover:from-fuchsia-600 hover:to-purple-700 text-white font-semibold shadow-lg shadow-fuchsia-500/25 dark:shadow-none focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 transition-all duration-300 transform active:scale-[0.98] cursor-pointer disabled:opacity-75 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <span>Sign Up</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerify} className="space-y-4">
            <div className="space-y-2 text-center">
              <h3 className="text-lg font-bold">Verify Your Email</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                We&apos;ve sent a 6-digit verification code to <span className="font-semibold">{email}</span>.<br />
                <span className="text-purple-500 dark:text-purple-400 font-medium">(If testing locally, lookup the code in your server logs.)</span>
              </p>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">6-Digit Code</label>
              <input
                type="text"
                maxLength={6}
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ""))}
                placeholder="000000"
                className="w-full text-center tracking-widest text-lg font-mono py-2.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={verifyLoading}
              className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl bg-fuchsia-500 hover:bg-fuchsia-600 text-white font-semibold shadow-lg shadow-fuchsia-500/25 dark:shadow-none focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 transition-all cursor-pointer disabled:opacity-75"
            >
              {verifyLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <span>Verify Account</span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setShowVerify(false)}
              className="w-full text-xs text-slate-500 hover:underline text-center cursor-pointer"
            >
              Back to Sign Up
            </button>
          </form>
        )}

        <div className="text-center text-xs text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-zinc-800/80 pt-4">
          <span>Already have an account? </span>
          <Link href="/auth/login" className="text-fuchsia-600 dark:text-fuchsia-400 font-bold hover:underline">
            Log In
          </Link>
        </div>
      </div>
    </div>
  );
}
