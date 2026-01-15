'use client'

import { useEffect } from 'react'
import { AlertTriangle, RefreshCcw, Home, Search } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function AnalyzeError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[Analyze Error]', {
      message: error.message,
      digest: error.digest,
      timestamp: new Date().toISOString(),
    })
  }, [error])

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-6">
      <div className="max-w-lg w-full">
        <div className="rounded-xl border border-red-500/30 bg-gradient-to-b from-red-500/10 to-transparent p-8 text-center">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-red-500/20 ring-4 ring-red-500/10">
            <AlertTriangle className="h-8 w-8 text-red-400" />
          </div>

          <h1 className="text-2xl font-bold text-white mb-2">
            Analysis Failed
          </h1>

          <p className="text-slate-400 mb-6">
            We encountered an error while analyzing this wallet. This might be due to network issues or an invalid address.
          </p>

          {error.digest && (
            <p className="text-xs text-slate-500 mb-6 font-mono">
              Error ID: {error.digest}
            </p>
          )}

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-6">
            <Button
              onClick={reset}
              className="inline-flex items-center gap-2"
            >
              <RefreshCcw className="h-4 w-4" />
              Try again
            </Button>

            <Link href="/">
              <Button variant="outline" className="inline-flex items-center gap-2">
                <Search className="h-4 w-4" />
                New Analysis
              </Button>
            </Link>
          </div>

          <p className="text-xs text-slate-500">
            If this keeps happening, please verify the wallet address is correct.
          </p>

          {process.env.NODE_ENV === 'development' && (
            <details className="mt-6 text-left">
              <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300">
                Developer Details
              </summary>
              <div className="mt-3 p-4 rounded-lg bg-slate-900 border border-slate-800">
                <p className="text-xs text-red-300 font-mono mb-2">
                  {error.message}
                </p>
                <pre className="text-xs text-slate-400 overflow-auto max-h-48 font-mono">
                  {error.stack}
                </pre>
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}
