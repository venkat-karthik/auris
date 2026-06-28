/* eslint-disable react-hooks/exhaustive-deps, react-hooks/set-state-in-effect, @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/Providers";
import DashboardLayout from "@/components/DashboardLayout";
import { toast } from "sonner";
import {
  Coins,
  ArrowUpRight,
  TrendingUp,
  Loader2,
  Phone,
  CheckCircle2,
  Calendar,
  MessageSquare
} from "lucide-react";

interface Transaction {
  id: number;
  razorpay_order_id: string;
  amount_paise: number;
  credits_added: number;
  status: string;
  created_at: string;
}

export default function BillingPage() {
  const { token, user } = useAuth();
  const [balance, setBalance] = useState<number>(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Checkout states
  const [amount, setAmount] = useState<number>(500);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const fetchBillingData = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/billing/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setBalance(data.balance_credits || 0);
        setTransactions(data.transactions || []);
      } else {
        toast.error("Failed to load billing metrics");
      }
    } catch (err) {
      console.error(err);
      toast.error("Error retrieving balance details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBillingData();
  }, [token]);

  // Load Razorpay Script helper
  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handlePurchase = async () => {
    if (amount <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }

    // Check if amount is >= 5,000 -> Redirect to WhatsApp
    if (amount >= 5000) {
      toast.info("Opening WhatsApp for high-volume enterprise credit order...");
      const text = encodeURIComponent(
        `Hi Auris team! I'd like to purchase ₹${amount.toLocaleString()} worth of credits for my account.`
      );
      window.open(`https://wa.me/918309827125?text=${text}`, "_blank");
      return;
    }

    setCheckoutLoading(true);

    try {
      // 1. Load Razorpay script
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded) {
        toast.error("Razorpay SDK failed to load. Please check your connection.");
        setCheckoutLoading(false);
        return;
      }

      // 2. Create order in Backend
      const orderRes = await fetch(`${API_URL}/billing/razorpay/create-order`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ amount_inr: amount })
      });

      if (!orderRes.ok) {
        const errData = await orderRes.json();
        toast.error(errData.detail || "Failed to create payment order");
        setCheckoutLoading(false);
        return;
      }

      const orderData = await orderRes.json();

      // 3. Initiate checkout options
      const options = {
        key: orderData.key_id,
        amount: orderData.amount_paise,
        currency: orderData.currency,
        name: "Auris Platform",
        description: `Add ₹${amount} worth of credits`,
        order_id: orderData.order_id,
        handler: async function (response: any) {
          // 4. Verify payment in Backend
          setCheckoutLoading(true);
          try {
            const verifyRes = await fetch(`${API_URL}/billing/razorpay/verify-payment`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
              },
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              })
            });

            if (verifyRes.ok) {
              const verifyData = await verifyRes.json();
              toast.success(`Successfully added ₹${verifyData.credits_added} credits!`);
              fetchBillingData(); // reload balance
            } else {
              toast.error("Payment verification failed. Please contact support.");
            }
          } catch (err) {
            console.error(err);
            toast.error("Verification connection error");
          } finally {
            setCheckoutLoading(false);
          }
        },
        prefill: {
          email: user?.email || ""
        },
        theme: {
          color: "#d946ef" // fuchsia-500 brand color
        }
      };

      const razorpayInstance = new (window as any).Razorpay(options);
      razorpayInstance.open();
    } catch (err) {
      console.error(err);
      toast.error("Error setting up payment checkout flow");
    } finally {
      setCheckoutLoading(false);
    }
  };

  const presets = [100, 250, 500, 1000, 2500];

  if (loading) {
    return (
      <DashboardLayout>
        <div className="h-[70vh] w-full flex items-center justify-center">
          <Loader2 className="w-10 h-10 text-purple-500 animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-fade-in">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Coins className="text-purple-500 w-8 h-8" /> Billing & Balance
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Recharge your credit balance (1 rupee = 1 credit), buy pre-paid limits or request high volume B2B quotes.
          </p>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Purchase limits column */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Balance Indicator card */}
            <div className="glass p-6 md:p-8 rounded-3xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative overflow-hidden">
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Remaining Balance</span>
                <h2 className="text-5xl font-black text-fuchsia-600 dark:text-fuchsia-400">
                  ₹{balance.toLocaleString()}
                </h2>
                <p className="text-xs text-slate-400 dark:text-slate-500">
                  Usage price is calculated on a per-second basis dynamically.
                </p>
              </div>
              <div className="flex-shrink-0">
                <div className="w-20 h-20 rounded-2xl bg-fuchsia-500/10 dark:bg-fuchsia-500/20 text-fuchsia-500 flex items-center justify-center">
                  <Coins className="w-10 h-10 animate-bounce" />
                </div>
              </div>
            </div>

            {/* Select Recharge Amount Panel */}
            <div className="glass p-6 md:p-8 rounded-3xl shadow-sm space-y-6">
              <h3 className="font-bold text-lg">Purchase Credits</h3>

              {/* Preset Chips */}
              <div className="flex flex-wrap gap-3">
                {presets.map((p) => (
                  <button
                    key={p}
                    onClick={() => setAmount(p)}
                    className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all border cursor-pointer ${
                      amount === p
                        ? "bg-fuchsia-500 border-fuchsia-500 text-white shadow-md shadow-fuchsia-500/25"
                        : "border-slate-200 dark:border-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-900/50 text-slate-600 dark:text-slate-300"
                    }`}
                  >
                    ₹{p.toLocaleString()}
                  </button>
                ))}
              </div>

              {/* Custom Input */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Custom Amount (INR)</label>
                <div className="relative flex items-center max-w-sm">
                  <span className="absolute left-4 font-bold text-slate-400">₹</span>
                  <input
                    type="number"
                    value={amount || ""}
                    onChange={(e) => setAmount(Number(e.target.value))}
                    placeholder="Enter custom recharge value"
                    className="w-full pl-8 pr-4 py-3 rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500 transition-all text-sm font-bold"
                  />
                </div>
              </div>

              {/* Checkout Trigger button */}
              <button
                onClick={handlePurchase}
                disabled={checkoutLoading || amount <= 0}
                className="w-full flex items-center justify-center space-x-2 py-3.5 rounded-2xl bg-gradient-to-r from-fuchsia-500 to-purple-600 hover:from-fuchsia-600 hover:to-purple-700 text-white font-bold shadow-lg shadow-fuchsia-500/25 dark:shadow-none hover:shadow-xl hover:shadow-fuchsia-500/35 transition-all cursor-pointer disabled:opacity-75 disabled:cursor-not-allowed text-sm"
              >
                {checkoutLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : amount >= 5000 ? (
                  <>
                    <MessageSquare className="w-4 h-4" />
                    <span>Purchase via WhatsApp (₹5,000+)</span>
                  </>
                ) : (
                  <>
                    <ArrowUpRight className="w-4 h-4" />
                    <span>Initiate Recharge (₹{amount})</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Transaction listing column */}
          <div className="glass p-6 md:p-8 rounded-3xl shadow-sm flex flex-col space-y-4 h-[440px]">
            <div className="flex items-center space-x-2 pb-3 border-b border-slate-100 dark:border-zinc-800/80">
              <TrendingUp className="w-5 h-5 text-purple-500" />
              <h3 className="font-bold text-lg">Transactions</h3>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {transactions.length === 0 ? (
                <div className="h-full flex items-center justify-center text-sm text-slate-400">
                  No billing history recorded.
                </div>
              ) : (
                transactions.map((tx) => (
                  <div
                    key={tx.id}
                    className="p-3 rounded-xl bg-white/40 dark:bg-zinc-900/40 border border-slate-100 dark:border-zinc-800/50 flex items-center justify-between text-sm"
                  >
                    <div className="space-y-1">
                      <p className="font-bold text-xs">Recharge #{tx.id}</p>
                      <p className="text-[10px] text-slate-400 dark:text-slate-500">
                        {new Date(tx.created_at).toLocaleDateString([], {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit"
                        })}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-black text-purple-600 dark:text-purple-400">
                        + ₹{tx.credits_added}
                      </p>
                      <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-slate-400">
                        {tx.status === "completed" ? (
                          <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                        ) : (
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                        )}
                        {tx.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
