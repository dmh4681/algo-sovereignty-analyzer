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
