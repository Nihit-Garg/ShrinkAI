"use client";

import { Phone, X, Heart } from 'lucide-react';
import { useState } from 'react';

const HELPLINES = [
  { name: 'iCall (TISS)', number: '9152987821', note: 'Mon–Sat, 8am–10pm' },
  { name: 'Vandrevala Foundation', number: '1860-2662-345', note: '24/7, free' },
  { name: 'AASRA', number: '9820466627', note: '24/7' },
];

export function CrisisBanner() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="mx-auto max-w-3xl w-full animate-fade-in-up my-4">
      <div className="rounded-2xl border border-amber-200/60 bg-amber-50/80 backdrop-blur-sm p-5 shadow-sm">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
              <Heart size={14} className="text-amber-600" />
            </div>
            <p className="text-sm font-semibold text-amber-900">
              You&apos;re not alone in this.
            </p>
          </div>
          <button
            onClick={() => setDismissed(true)}
            className="text-amber-400 hover:text-amber-600 transition-colors flex-shrink-0 mt-0.5"
            aria-label="Dismiss"
          >
            <X size={16} />
          </button>
        </div>

        <p className="text-sm text-amber-800/80 mb-4 leading-relaxed">
          If you&apos;re feeling overwhelmed, please reach out to a trained counsellor.
          These helplines are free and confidential.
        </p>

        {/* Helplines */}
        <div className="space-y-2">
          {HELPLINES.map((h) => (
            <a
              key={h.name}
              href={`tel:${h.number.replace(/-/g, '')}`}
              className="flex items-center justify-between px-4 py-2.5 rounded-xl bg-white/70 hover:bg-white border border-amber-100 hover:border-amber-200 transition-all duration-150 group"
            >
              <div>
                <span className="text-sm font-medium text-amber-900">{h.name}</span>
                <span className="text-xs text-amber-600/70 ml-2">{h.note}</span>
              </div>
              <div className="flex items-center gap-1.5 text-amber-700 group-hover:text-amber-900 transition-colors">
                <Phone size={13} />
                <span className="text-sm font-mono font-medium">{h.number}</span>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
