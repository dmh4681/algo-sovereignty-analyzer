'use client'

import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'

/**
 * Full-page loading skeleton that mimics the layout of the analysis dashboard.
 *
 * Renders placeholder blocks for:
 * - Header row (title + badge)
 * - Main sovereignty score card
 * - 4-column asset category grid
 * - 2-column calculator section
 *
 * Uses `animate-in fade-in` for a smooth appearance transition. Intended as the
 * initial loading state while the wallet analysis API call is in progress.
 */
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

/**
 * Centered loading spinner with a pulsing ring effect and customizable text.
 * Used for full-section loading states where a skeleton layout is not appropriate.
 *
 * @param props - Component props
 * @param props.text - Text displayed below the spinner. Defaults to "Analyzing wallet..."
 */
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

/**
 * Inline animated loading indicator showing three bouncing dots.
 * Used within text content or buttons to indicate an ongoing operation
 * without taking up significant vertical space.
 */
export function LoadingDots() {
  return (
    <span className="inline-flex gap-1">
      <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </span>
  )
}

/**
 * Content-aware skeleton for the sovereignty score display. Mimics the layout
 * of the {@link SovereigntyScore} component with a circular score placeholder,
 * status text block, and tag pills. Provides a more accurate loading preview
 * than a generic rectangle skeleton.
 */
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

/**
 * Content-aware skeleton for the 4-column asset breakdown grid. Each card
 * mimics the {@link AssetBreakdown} category card layout with a header icon,
 * value placeholder, and three asset row skeletons.
 */
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

/**
 * Complete dashboard loading skeleton combining all section skeletons.
 * Renders the full page layout placeholder including header, sovereignty score,
 * asset breakdown, and calculator sections. Used as the initial loading state
 * for the `/analyze` page before any data has loaded.
 */
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

/**
 * Props for the {@link SectionLoading} component.
 *
 * @property title - Bold heading text for the loading section
 * @property description - Smaller description text below the title
 */
interface SectionLoadingProps {
  title?: string
  description?: string
}

/**
 * Subtle inline loading indicator for individual dashboard sections.
 * Shows a spinning icon with optional title and description text.
 * Used when a specific section is loading independently (e.g., coaching
 * panel or history chart) while the rest of the dashboard is already rendered.
 *
 * @param props - Component props
 */
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

/**
 * Props for the {@link ProgressiveLoadingIndicator} component.
 *
 * @property stages - Array of loading stage objects, each with:
 *   - `id`: Unique identifier for the stage
 *   - `label`: Human-readable description (e.g., "Loading sovereignty data")
 *   - `status`: Current state -- pending (not started), loading (in progress),
 *     complete (finished), or error (failed)
 */
interface ProgressiveLoadingIndicatorProps {
  stages: {
    id: string
    label: string
    status: 'pending' | 'loading' | 'complete' | 'error'
  }[]
}

/**
 * Multi-stage loading progress indicator showing which analysis steps are
 * pending, in progress, complete, or failed. Used during the progressive
 * loading flow where sovereignty data loads first, then full asset details.
 *
 * Visual indicators per stage:
 * - **Pending**: Gray circle
 * - **Loading**: Orange spinning icon
 * - **Complete**: Green filled circle
 * - **Error**: Red filled circle
 *
 * @param props - Component props
 */
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

/**
 * Loading skeleton for the 4-column category summary grid (quick view).
 * Each card shows a compact placeholder with icon, label, and value skeletons.
 * Used during progressive loading before category totals are available.
 */
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
