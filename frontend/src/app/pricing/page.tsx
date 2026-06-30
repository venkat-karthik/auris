/* eslint-disable react/no-unescaped-entities */
"use client";

import Link from "next/link";
import { Check, Sparkles, Flame, Shield, ArrowLeft } from "lucide-react";
import { useAuth } from "@/components/Providers";

export default function PricingPage() {
  const { user } = useAuth();

  const plans = [
    {
      name: "Vernacular Plan",
      price: "₹5.00",
      description: "Optimized for localized customer interaction in Indian languages.",
      features: [
        "First-class Hindi, Telugu & Tamil",
        "Sarvam AI speech translation",
        "Local caller memory injection",
        "Outbound campaign dialer",
        "WebRTC live voice testing",
        "DTMF keypress tracking",
      ],
      cta: "Deploy Indian Agent",
      popular: false,
      color: "from-cyan-500 to-blue-500",
    },
    {
      name: "Standard English",
      price: "₹6.50",
      description: "The default business assistant for general customer receptionist duties.",
      features: [
        "100% fluent English conversation",
        "Under 500ms response latency",
        "GPT-4o-mini cognitive intelligence",
        "ElevenLabs expressive voice engine",
        "Custom knowledge base files (up to 100MB)",
        "API webhook context actions",
      ],
      cta: "Get Started Free",
      popular: true,
      color: "from-fuchsia-500 to-purple-600",
    },
    {
      name: "Premium English",
      price: "₹10.00",
      description: "Advanced intelligence tier for complex logic and negotiations.",
      features: [
        "Unrestricted GPT-4o reasoning",
        "Deepgram premium STT engine",
        "ElevenLabs HD voice selection",
        "Warm transfers to human lines",
        "Voicemail detection triggers",
        "Priority developer API keys",
      ],
      cta: "Deploy Advanced Agent",
      popular: false,
      color: "from-purple-600 to-indigo-600",
    },
  ];

  return (
    <div className="min-h-screen w-full flex flex-col bg-gradient-soothing text-slate-800 dark:text-slate-100">
      {/* Header Navigation */}
      <header className="h-20 max-w-7xl w-full mx-auto flex items-center justify-between px-6">
        <Link href="/" className="flex items-center space-x-2">
          <span className="text-2xl font-black bg-gradient-to-r from-fuchsia-500 via-purple-600 to-indigo-500 bg-clip-text text-transparent dark:from-fuchsia-400 dark:to-cyan-400">
            Auris
          </span>
        </Link>
        <div className="flex items-center space-x-6">
          <Link
            href="/"
            className="text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
          >
            Home
          </Link>
          {user ? (
            <Link
              href="/dashboard"
              className="px-4 py-2 text-sm font-semibold rounded-xl bg-fuchsia-500 hover:bg-fuchsia-600 text-white shadow-md shadow-fuchsia-500/25 hover:shadow-lg transition-all cursor-pointer"
            >
              Dashboard
            </Link>
          ) : (
            <>
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
            </>
          )}
        </div>
      </header>

      {/* Main Pricing Grid */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-12 flex flex-col items-center justify-center space-y-12">
        <div className="text-center space-y-4 max-w-3xl">
          <span className="text-xs font-bold uppercase tracking-widest text-fuchsia-500 dark:text-fuchsia-400">Simple Per-Minute Billing</span>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight leading-none">
            Pay only for the seconds you use.
          </h1>
          <p className="text-base text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            No subscription tiers, no setup fees, and no minimum contracts. Recharge your wallet via Razorpay and scale call volume on demand.
          </p>
        </div>

        {/* Plan Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full items-stretch">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative glass rounded-3xl p-6 md:p-8 flex flex-col justify-between shadow-lg transition-all duration-300 hover:scale-[1.02] border ${
                plan.popular
                  ? "border-fuchsia-500 dark:border-fuchsia-500/50 shadow-fuchsia-500/5"
                  : "border-slate-200/50 dark:border-zinc-800/60"
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-3.5 left-1/2 transform -translate-x-1/2 px-3 py-1 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 text-white text-[10px] font-black uppercase tracking-wider flex items-center gap-1 shadow-md shadow-fuchsia-500/20">
                  <Flame className="w-3.5 h-3.5" /> Most Popular
                </span>
              )}

              <div className="space-y-6">
                {/* Title and price */}
                <div className="space-y-2">
                  <h3 className="font-extrabold text-xl">{plan.name}</h3>
                  <div className="flex items-baseline space-x-1">
                    <span className="text-4xl font-black tracking-tight">{plan.price}</span>
                    <span className="text-xs text-slate-400 font-semibold">/ minute</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed min-h-[40px]">
                    {plan.description}
                  </p>
                </div>

                {/* Features List */}
                <ul className="space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start space-x-2.5 text-xs text-slate-600 dark:text-slate-300">
                      <Check className="w-4 h-4 text-fuchsia-500 shrink-0 mt-0.5" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* CTA button */}
              <div className="pt-8">
                <Link
                  href={user ? "/dashboard" : "/auth/signup"}
                  className={`w-full py-3 rounded-2xl flex items-center justify-center font-bold text-sm transition-all transform active:scale-95 cursor-pointer ${
                    plan.popular
                      ? "bg-gradient-to-r from-fuchsia-500 to-purple-600 hover:from-fuchsia-600 hover:to-purple-700 text-white shadow-lg shadow-fuchsia-500/20"
                      : "bg-slate-100 dark:bg-zinc-900 hover:bg-slate-200 dark:hover:bg-zinc-800/80 text-slate-800 dark:text-slate-200"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* Bring Your Own Keys (BYOK) Section */}
        <div className="w-full glass p-6 md:p-8 rounded-3xl border border-slate-200/50 dark:border-zinc-800/60 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl text-left">
            <h3 className="font-extrabold text-lg flex items-center gap-2">
              <Shield className="w-5 h-5 text-fuchsia-500" /> Bring Your Own Keys (BYOK)
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Have your own developer accounts with Twilio, Telnyx, OpenAI, or ElevenLabs? Plug them into your settings panel and pay a flat routing platform fee of only **₹2.00 / minute** for the workflow pipeline.
            </p>
          </div>
          <Link
            href={user ? "/settings" : "/auth/signup"}
            className="flex-shrink-0 px-6 py-3 rounded-2xl border border-fuchsia-500/20 hover:bg-fuchsia-500/10 text-fuchsia-500 font-bold text-xs hover:border-fuchsia-500/40 transition-all text-center cursor-pointer"
          >
            Configure Custom Credentials
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="h-16 flex items-center justify-center border-t border-slate-200/50 dark:border-zinc-800/60 text-xs text-slate-400 mt-12">
        <span>© {new Date().getFullYear()} Auris Platform. Built from scratch. All rights reserved.</span>
      </footer>
    </div>
  );
}
