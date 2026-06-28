"use client";

import Link from "next/link";
import { ArrowRight, Bot, Sparkles, Shield, Clock, Languages } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full flex flex-col bg-gradient-soothing text-slate-800 dark:text-slate-100">
      
      {/* Header Navigation */}
      <header className="h-20 max-w-7xl w-full mx-auto flex items-center justify-between px-6">
        <Link href="/" className="flex items-center space-x-2">
          <span className="text-2xl font-black bg-gradient-to-r from-fuchsia-500 via-purple-600 to-indigo-500 bg-clip-text text-transparent dark:from-fuchsia-400 dark:via-purple-400 dark:to-cyan-400">
            Auris
          </span>
        </Link>
        <div className="flex items-center space-x-4">
          <Link
            href="/auth/login"
            className="text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
          >
            Log In
          </Link>
          <Link
            href="/auth/signup"
            className="px-4 py-2 text-sm font-semibold rounded-xl bg-fuchsia-500 hover:bg-fuchsia-600 text-white shadow-md shadow-fuchsia-500/25 hover:shadow-lg transition-all cursor-pointer"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 max-w-5xl mx-auto py-12 md:py-24 space-y-8">
        
        {/* Pitch badge */}
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-fuchsia-500/10 text-fuchsia-600 dark:text-fuchsia-400 border border-fuchsia-500/20 text-xs font-bold animate-pulse">
          <Sparkles className="w-3.5 h-3.5" />
          <span>India&apos;s first multi-language voice AI receptionist</span>
        </div>

        {/* Hero title */}
        <div className="space-y-4">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight">
            We don&apos;t give you tools.<br />
            <span className="bg-gradient-to-r from-fuchsia-500 to-purple-500 bg-clip-text text-transparent dark:from-fuchsia-400 dark:to-purple-400">
              We give you an employee.
            </span>
          </h1>
          <p className="text-base md:text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto">
            Auris is a conversational voice AI platform that lets you deploy customized receptionist agents that answer calls in Hindi, Telugu, Tamil, and English in under 5 minutes.
          </p>
        </div>

        {/* Hero CTAs */}
        <div className="flex flex-col sm:sm:row gap-4 justify-center">
          <Link
            href="/auth/signup"
            className="flex items-center justify-center space-x-2 px-8 py-3.5 rounded-2xl bg-gradient-to-r from-fuchsia-500 to-purple-600 hover:from-fuchsia-600 hover:to-purple-700 text-white font-bold shadow-lg shadow-fuchsia-500/25 dark:shadow-none hover:shadow-xl hover:shadow-fuchsia-500/35 transition-all transform active:scale-95 cursor-pointer text-sm"
          >
            <span>Deploy Receptionist Now</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16 w-full text-left">
          {/* Feature 1 */}
          <div className="glass p-6 rounded-2xl space-y-3">
            <div className="w-10 h-10 rounded-xl bg-fuchsia-500/10 dark:bg-fuchsia-500/20 text-fuchsia-500 flex items-center justify-center">
              <Languages className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-lg">Vernacular Support</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              First-class support for Hindi, Telugu, Tamil, Marathi, and Kannada. Speak to customers in their own language.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="glass p-6 rounded-2xl space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 dark:bg-purple-500/20 text-purple-500 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-lg">Under 500ms Latency</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Proprietary pipeline built from scratch guarantees lightning-fast response times, eliminating awkward pauses.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="glass p-6 rounded-2xl space-y-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 dark:bg-cyan-500/20 text-cyan-500 flex items-center justify-center">
              <Shield className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-lg">Predictable INR Pricing</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Simple per-second billing with Razorpay. Top up credits instantly or contact our WhatsApp support for quotes.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="h-16 flex items-center justify-center border-t border-slate-200/50 dark:border-zinc-800/60 text-xs text-slate-400 mt-12">
        <span>© {new Date().getFullYear()} Auris Platform. Built from scratch. All rights reserved.</span>
      </footer>

    </div>
  );
}
