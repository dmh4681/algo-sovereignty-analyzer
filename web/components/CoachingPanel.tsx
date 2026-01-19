'use client'

import { useState, useEffect } from 'react'
import { getSovereigntyCoaching, ApiError } from '@/lib/api'
import { AnalysisResponse } from '@/lib/types'
import { ChevronDown, ChevronUp, Brain, RefreshCw, AlertTriangle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface CoachingPanelProps {
  address: string
  analysis: AnalysisResponse
}

export function CoachingPanel({ address, analysis }: CoachingPanelProps) {
  const [advice, setAdvice] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(true)
  const [hasAttempted, setHasAttempted] = useState(false)

  const fetchCoaching = async () => {
    setLoading(true)
    setError(null)
    setHasAttempted(true)

    try {
      const response = await getSovereigntyCoaching({
        address,
        analysis: analysis as unknown as Record<string, unknown>,
      })
      setAdvice(response.advice)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to get coaching advice. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  // Auto-fetch on mount
  useEffect(() => {
    if (!hasAttempted && analysis) {
      fetchCoaching()
    }
  }, [analysis, hasAttempted])

  return (
    <div className="rounded-lg border border-purple-500/30 bg-purple-500/5 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-purple-500/10 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/20">
            <Brain className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-purple-300">Sovereignty Coach</h3>
            <p className="text-xs text-slate-400">AI-powered portfolio analysis</p>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-purple-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-purple-400" />
        )}
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4 pt-0 space-y-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-8 space-y-3">
              <div className="relative">
                <Brain className="w-8 h-8 text-purple-400 animate-pulse" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full animate-ping" />
              </div>
              <p className="text-sm text-slate-400">Analyzing your sovereignty...</p>
              <p className="text-xs text-slate-500">This may take a few seconds</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center py-6 space-y-3">
              <AlertTriangle className="w-8 h-8 text-amber-400" />
              <p className="text-sm text-slate-300">{error}</p>
              <button
                onClick={fetchCoaching}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors text-sm"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
            </div>
          ) : advice ? (
            <div className="space-y-4">
              {/* Markdown content */}
              <div className="prose prose-invert prose-sm max-w-none prose-headings:text-purple-300 prose-strong:text-purple-200 prose-p:text-slate-300 prose-li:text-slate-300">
                <ReactMarkdown>{advice}</ReactMarkdown>
              </div>

              {/* Refresh button */}
              <div className="pt-4 border-t border-purple-500/20">
                <button
                  onClick={fetchCoaching}
                  className="flex items-center gap-2 text-xs text-slate-400 hover:text-purple-300 transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  Refresh Analysis
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center py-6 space-y-3">
              <p className="text-sm text-slate-400">Ready to analyze your portfolio</p>
              <button
                onClick={fetchCoaching}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors text-sm"
              >
                <Brain className="w-4 h-4" />
                Get Coaching
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function CoachingPanelSkeleton() {
  return (
    <div className="rounded-lg border border-purple-500/30 bg-purple-500/5 p-4 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-purple-500/20" />
        <div className="space-y-2">
          <div className="h-4 w-32 bg-purple-500/20 rounded" />
          <div className="h-3 w-48 bg-purple-500/10 rounded" />
        </div>
      </div>
    </div>
  )
}
