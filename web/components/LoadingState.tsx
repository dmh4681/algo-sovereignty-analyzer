'use client'

import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'

export function LoadingState() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-6 w-32" />
      </div>

      {/* Main score skeleton */}
      <Skeleton className="h-48 w-full rounded-xl" />

      {/* Category cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-64 rounded-xl" />
        ))}
      </div>

      {/* Calculator skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    </div>
  )
}

export function LoadingSpinner({ text = 'Analyzing wallet...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 space-y-4">
      <div className="relative">
        <div className="absolute inset-0 rounded-full bg-orange-500/20 animate-ping" />
        <Loader2 className="h-12 w-12 text-orange-500 animate-spin relative" />
      </div>
      <p className="text-slate-400 animate-pulse">{text}</p>
    </div>
  )
}

export function LoadingDots() {
  return (
    <span className="inline-flex gap-1">
      <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </span>
  )
}

// Content-aware skeleton for sovereignty score display
export function SovereigntyScoreSkeleton() {
  return (
    <div className="rounded-xl bg-slate-800 p-6 animate-pulse">
      <div className="flex flex-col sm:flex-row items-center gap-6">
        {/* Score circle skeleton */}
        <div className="relative">
          <Skeleton className="h-28 w-28 rounded-full" />
          <div className="absolute inset-0 flex items-center justify-center">
            <Skeleton className="h-8 w-12" />
          </div>
        </div>
        {/* Score details */}
        <div className="flex-1 space-y-3 text-center sm:text-left">
          <Skeleton className="h-8 w-48 mx-auto sm:mx-0" />
          <Skeleton className="h-5 w-64 mx-auto sm:mx-0" />
          <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
            <Skeleton className="h-6 w-24 rounded-full" />
            <Skeleton className="h-6 w-32 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  )
}

// Content-aware skeleton for asset breakdown cards
export function AssetBreakdownSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="rounded-xl bg-slate-800 p-4 animate-pulse">
          {/* Category header */}
          <div className="flex items-center gap-2 mb-4">
            <Skeleton className="h-6 w-6 rounded" />
            <Skeleton className="h-5 w-24" />
          </div>
          {/* Value */}
          <Skeleton className="h-8 w-28 mb-4" />
          {/* Asset list */}
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        </div>
      ))}
    </div>
  )
}

// Combined dashboard skeleton with all sections
export function DashboardLoadingSkeleton() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <Skeleton className="h-8 w-64" />
        <div className="flex gap-2">
          <Skeleton className="h-10 w-32 rounded-lg" />
          <Skeleton className="h-10 w-10 rounded-lg" />
        </div>
      </div>

      {/* Sovereignty Score */}
      <SovereigntyScoreSkeleton />

      {/* Asset Breakdown */}
      <AssetBreakdownSkeleton />

      {/* Calculator section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl bg-slate-800 p-4 animate-pulse">
          <Skeleton className="h-6 w-32 mb-4" />
          <Skeleton className="h-10 w-full mb-3" />
          <Skeleton className="h-10 w-full" />
        </div>
        <div className="rounded-xl bg-slate-800 p-4 animate-pulse">
          <Skeleton className="h-6 w-40 mb-4" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
      </div>
    </div>
  )
}

// Section loading indicator - subtle inline loading for individual sections
interface SectionLoadingProps {
  title?: string
  description?: string
}

export function SectionLoading({ title, description }: SectionLoadingProps) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
      <Loader2 className="h-5 w-5 text-orange-500 animate-spin flex-shrink-0" />
      <div className="flex-1 min-w-0">
        {title && <div className="text-sm font-medium text-slate-200">{title}</div>}
        {description && <div className="text-xs text-slate-400">{description}</div>}
      </div>
    </div>
  )
}

// Progressive loading indicator showing what's loaded and what's pending
interface ProgressiveLoadingIndicatorProps {
  stages: {
    id: string
    label: string
    status: 'pending' | 'loading' | 'complete' | 'error'
  }[]
}

export function ProgressiveLoadingIndicator({ stages }: ProgressiveLoadingIndicatorProps) {
  return (
    <div className="space-y-2 p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
      <div className="text-sm font-medium text-slate-300 mb-3">Loading Analysis</div>
      {stages.map((stage) => (
        <div key={stage.id} className="flex items-center gap-3">
          {stage.status === 'loading' && (
            <Loader2 className="h-4 w-4 text-orange-500 animate-spin" />
          )}
          {stage.status === 'complete' && (
            <div className="h-4 w-4 rounded-full bg-green-500/20 flex items-center justify-center">
              <div className="h-2 w-2 rounded-full bg-green-500" />
            </div>
          )}
          {stage.status === 'pending' && (
            <div className="h-4 w-4 rounded-full bg-slate-600/50" />
          )}
          {stage.status === 'error' && (
            <div className="h-4 w-4 rounded-full bg-red-500/20 flex items-center justify-center">
              <div className="h-2 w-2 rounded-full bg-red-500" />
            </div>
          )}
          <span className={`text-sm ${
            stage.status === 'complete' ? 'text-slate-400' :
            stage.status === 'loading' ? 'text-orange-400' :
            stage.status === 'error' ? 'text-red-400' :
            'text-slate-500'
          }`}>
            {stage.label}
          </span>
        </div>
      ))}
    </div>
  )
}

// Category summary loading skeleton for quick view
export function CategorySummarySkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="rounded-lg bg-slate-800 p-4 animate-pulse">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Skeleton className="h-6 w-6 rounded" />
              <Skeleton className="h-5 w-20" />
            </div>
            <Skeleton className="h-6 w-16" />
          </div>
          <Skeleton className="h-4 w-12 mt-2 ml-auto" />
        </div>
      ))}
    </div>
  )
}
