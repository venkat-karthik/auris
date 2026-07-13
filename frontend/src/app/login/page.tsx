'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, KeyRound, Mail, User, Building, ShieldCheck, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { AurisAPI } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

type AuthStep = 'login' | 'register' | 'verify';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [step, setStep] = useState<AuthStep>('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form Fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [orgName, setOrgName] = useState('');
  const [code, setCode] = useState('');

  const clearMessages = () => {
    setError(null);
    setSuccessMsg(null);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    setLoading(true);

    try {
      const data = await AurisAPI.auth.login(email, password);
      if (data.access_token) {
        await login(data.access_token, data.org_id);
        router.push('/');
      } else {
        setError('Login failed: Token not received.');
      }
    } catch (err: any) {
      if (!err.response) {
        setError('Cannot connect to the backend server. Please check if the backend server is running.');
      } else if (err.response.status >= 500) {
        setError('Internal Server Error. Please ensure Docker is running and database containers are started.');
      } else {
        const detail = err.response.data?.detail;
        if (detail === 'Please verify your email before logging in.') {
          setSuccessMsg('Your account is registered but unverified. Please input the 6-digit code printed in the backend console.');
          setStep('verify');
        } else {
          setError(detail || 'Invalid email or password.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    setLoading(true);

    try {
      await AurisAPI.auth.register(email, password, fullName, orgName);
      setSuccessMsg('Registration successful! Please check your backend terminal logs for the 6-digit verification code.');
      setStep('verify');
    } catch (err: any) {
      if (!err.response) {
        setError('Cannot connect to the backend server. Please check if the backend server is running.');
      } else if (err.response.status >= 500) {
        setError('Internal Server Error. Please ensure Docker is running and database containers are started.');
      } else {
        setError(err.response.data?.detail || 'Registration failed.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    setLoading(true);

    try {
      const data = await AurisAPI.auth.verify(email, code);
      if (data.access_token) {
        await login(data.access_token, data.org_id);
        setSuccessMsg('Account verified successfully! Redirecting...');
        setTimeout(() => {
          router.push('/');
        }, 1500);
      } else {
        setError('Verification succeeded but session token is missing.');
      }
    } catch (err: any) {
      if (!err.response) {
        setError('Cannot connect to the backend server. Please check if the backend server is running.');
      } else if (err.response.status >= 500) {
        setError('Internal Server Error. Please ensure Docker is running and database containers are started.');
      } else {
        setError(err.response.data?.detail || 'Invalid or expired verification code.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080a0f] flex items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Decorative Orbs */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Main Glass Panel */}
      <div className="w-full max-w-md relative z-10">
        <div className="bg-slate-950/45 border border-slate-800/80 rounded-3xl p-8 backdrop-blur-2xl shadow-2xl space-y-6">
          
          {/* Logo & Header */}
          <div className="flex flex-col items-center text-center space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-[2px] shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-cyan-400" />
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-extrabold text-white tracking-tight">
                {step === 'login' && 'Welcome Back'}
                {step === 'register' && 'Create Your Account'}
                {step === 'verify' && 'Verify Account'}
              </h2>
              <p className="text-slate-400 text-xs mt-1">
                {step === 'login' && 'Access the Auris Voice AI Platform'}
                {step === 'register' && 'Start building local voice agents in minutes'}
                {step === 'verify' && 'Enter the 6-digit code from the backend console logs'}
              </p>
            </div>
          </div>

          {/* Feedback Messages */}
          {error && (
            <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs leading-relaxed">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs leading-relaxed">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Forms */}
          {step === 'login' && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm text-white placeholder-slate-500 transition-all outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Password</label>
                <div className="relative">
                  <KeyRound className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm text-white placeholder-slate-500 transition-all outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm shadow-xl shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all cursor-pointer disabled:opacity-50"
              >
                <span>{loading ? 'Logging in...' : 'Sign In'}</span>
                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>
            </form>
          )}

          {step === 'register' && (
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm text-white placeholder-slate-500 transition-all outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm text-white placeholder-slate-500 transition-all outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Organization Name</label>
                <div className="relative">
                  <Building className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    required
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="Auris Team"
                    className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm text-white placeholder-slate-500 transition-all outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Password</label>
                <div className="relative">
                  <KeyRound className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm text-white placeholder-slate-500 transition-all outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm shadow-xl shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all cursor-pointer disabled:opacity-50"
              >
                <span>{loading ? 'Creating Account...' : 'Register'}</span>
                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>
            </form>
          )}

          {step === 'verify' && (
            <form onSubmit={handleVerify} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm text-white placeholder-slate-500 transition-all outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">6-Digit Verification Code</label>
                <div className="relative">
                  <ShieldCheck className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="123456"
                    className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl text-sm text-white placeholder-slate-500 tracking-widest font-mono text-center outline-none transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm shadow-xl shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all cursor-pointer disabled:opacity-50"
              >
                <span>{loading ? 'Verifying...' : 'Verify & Log In'}</span>
                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>
            </form>
          )}

          {/* Toggle link */}
          <div className="pt-4 border-t border-slate-800/50 flex items-center justify-between text-xs text-slate-400">
            <span>
              {step === 'login' && "Don't have an account?"}
              {step === 'register' && 'Already have an account?'}
              {step === 'verify' && 'Need to verify another account?'}
            </span>
            <button
              onClick={() => {
                clearMessages();
                if (step === 'login') setStep('register');
                else if (step === 'register') setStep('login');
                else setStep('login');
              }}
              className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors cursor-pointer"
            >
              {step === 'login' && 'Sign Up'}
              {step === 'register' && 'Log In'}
              {step === 'verify' && 'Back to Login'}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
