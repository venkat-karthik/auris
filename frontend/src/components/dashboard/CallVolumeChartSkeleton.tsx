'use client';

import React from 'react';

export default function CallVolumeChartSkeleton() {
  return (
    <div className="glass-card rounded-3xl p-6 border border-slate-800/80 space-y-5 animate-pulse">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-2">
          <div className="h-4 w-40 bg-slate-800 rounded-lg" />
          <div className="h-6 w-64 bg-slate-800 rounded-xl" />
          <div className="h-3 w-80 bg-slate-800/60 rounded-md" />
        </div>
        <div className="h-8 w-40 bg-slate-800 rounded-xl" />
      </div>

      <div className="pt-4 pb-2">
        <div className="flex items-end justify-between gap-3 h-52 px-2">
          {[60, 85, 100, 75, 90, 110, 80].map((h, idx) => (
            <div key={idx} className="flex-1 flex flex-col items-center gap-2">
              <div className="w-full max-w-[36px] bg-slate-800/60 rounded-xl" style={{ height: `${h}%` }} />
              <div className="h-3 w-8 bg-slate-800 rounded-md" />
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-slate-800/60">
        <div className="flex items-center gap-5">
          <div className="h-4 w-24 bg-slate-800 rounded-md" />
          <div className="h-4 w-24 bg-slate-800 rounded-md" />
          <div className="h-4 w-24 bg-slate-800 rounded-md" />
        </div>
        <div className="h-4 w-28 bg-slate-800 rounded-md" />
      </div>
    </div>
  );
}
