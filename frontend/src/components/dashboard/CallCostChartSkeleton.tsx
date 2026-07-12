'use client';

import React from 'react';

export default function CallCostChartSkeleton() {
  return (
    <div className="glass-card rounded-3xl p-6 border border-slate-800/80 space-y-6 animate-pulse">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-2">
          <div className="h-4 w-44 bg-slate-800 rounded-lg" />
          <div className="h-6 w-56 bg-slate-800 rounded-xl" />
          <div className="h-3 w-72 bg-slate-800/60 rounded-md" />
        </div>
        <div className="h-8 w-44 bg-slate-800 rounded-xl" />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="h-3 w-28 bg-slate-800 rounded-md" />
          <div className="h-3 w-20 bg-slate-800 rounded-md" />
        </div>
        <div className="w-full h-4 rounded-xl bg-slate-800/80" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-3">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <div className="h-4 w-36 bg-slate-800 rounded-md" />
                <div className="h-3 w-20 bg-slate-800/60 rounded-md" />
              </div>
              <div className="h-5 w-10 bg-slate-800 rounded-lg" />
            </div>
            <div className="flex items-center justify-between pt-1 border-t border-slate-800/60">
              <div className="h-3 w-24 bg-slate-800 rounded-md" />
              <div className="h-3 w-24 bg-slate-800 rounded-md" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
