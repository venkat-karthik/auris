'use client';

import React from 'react';

export default function CallAnalyticsDashboardSkeleton() {
  return (
    <div className="glass-card rounded-3xl p-6 border border-slate-800/80 space-y-6 animate-pulse">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-2">
          <div className="h-4 w-48 bg-slate-800 rounded-lg" />
          <div className="h-6 w-64 bg-slate-800 rounded-xl" />
          <div className="h-3 w-80 bg-slate-800/60 rounded-md" />
        </div>
        <div className="h-8 w-44 bg-slate-800 rounded-xl" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-slate-800" />
              <div className="h-5 w-20 bg-slate-800 rounded-full" />
            </div>
            <div className="space-y-2">
              <div className="h-7 w-24 bg-slate-800 rounded-lg" />
              <div className="h-4 w-36 bg-slate-800 rounded-md" />
              <div className="h-3 w-full bg-slate-800/60 rounded-md" />
              <div className="h-3 w-4/5 bg-slate-800/60 rounded-md" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
