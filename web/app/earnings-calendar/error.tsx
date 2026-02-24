'use client'

import { AlertTriangle, RefreshCcw, Home } from 'lucide-react'
import Link from 'next/link'

export default function EarningsCalendarError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="max-w-2xl mx-auto py-16 px-4 text-center">
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-8">
        <AlertTriangle className="h-10 w-10 text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-red-300 mb-2">
          Earnings Calendar Error
        </h2>
        <p className="text-sm text-slate-400 mb-6">
          {error.message || 'Failed to load miner earnings data. The data source may be temporarily unavailable.'}
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white transition-colors"
          >
            <RefreshCcw className="h-4 w-4" />
            Try again
          </button>
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            <Home className="h-4 w-4" />
            Go Home
          </Link>
        </div>
      </div>
    </div>
  )
}
