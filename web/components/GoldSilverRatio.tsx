'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { getGoldSilverRatio } from '@/lib/api'
import { GoldSilverRatio as GoldSilverRatioType } from '@/lib/types'
import { TrendingDown, TrendingUp, Info } from 'lucide-react'

export default function GoldSilverRatio() {
  const [data, setData] = useState<GoldSilverRatioType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    fetchRatio()
  }, [])

  const fetchRatio = async () => {
    try {
      const result = await getGoldSilverRatio()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch ratio')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className="bg-gradient-to-br from-yellow-500/10 via-orange-500/5 to-slate-400/10 border-yellow-500/30">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Gold/Silver Ratio</CardTitle>
            <Skeleton className="h-6 w-20" />
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>
    )
  }

  if (error || !data) {
    return null // Silently fail if ratio can't be fetched
  }

  const getStatusColor = () => {
    switch (data.color) {
      case 'red':
        return 'text-red-400 bg-red-500/10 border-red-500/30'
      case 'orange':
        return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
      case 'yellow':
        return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
      case 'green':
        return 'text-green-400 bg-green-500/10 border-green-500/30'
      default:
        return 'text-slate-400 bg-slate-500/10 border-slate-500/30'
    }
  }

  return (
    <Card className="bg-gradient-to-r from-yellow-500/20 via-orange-500/10 to-slate-300/20 border-yellow-500/40"
>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <span className="text-xl">🥇</span>
              <span className="text-xl">🥈</span>
              Gold/Silver Ratio
            </CardTitle>
            <CardDescription className="mt-1">
              {data.ratio > data.historical_mean ? 'Silver undervalued' : 'Silver fairly valued'}
            </CardDescription>
          </div>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-slate-400 hover:text-slate-200 transition-colors"
            aria-label="Show more info"
          >
            <Info className="w-4 h-4" />
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Main Ratio Display */}
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-bold text-yellow-400">{data.ratio}</span>
          <span className="text-lg text-slate-400">: 1</span>
          {data.ratio > data.historical_mean ? (
            <TrendingUp className="w-5 h-5 text-red-400 ml-2" />
          ) : (
            <TrendingDown className="w-5 h-5 text-green-400 ml-2" />
          )}
        </div>

        {/* Status Message */}
        <div className={`px-3 py-2 rounded-lg border ${getStatusColor()}`}>
          <p className="text-sm font-medium">{data.message}</p>
        </div>

        {/* Current Prices */}
        <div className="grid grid-cols-2 gap-2 pt-2">
          <div className="text-center p-3 bg-gradient-to-br from-yellow-500/20 to-yellow-600/10 rounded-lg border border-yellow-500/30">
            <div className="text-xs text-yellow-400/80 font-medium">🥇 Gold</div>
            <div className="text-xl font-bold text-yellow-400">${data.gold_price.toLocaleString()}</div>
            <div className="text-xs text-yellow-500/60">per oz</div>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-slate-400/20 to-slate-500/10 rounded-lg border border-slate-400/30">
            <div className="text-xs text-slate-300/80 font-medium">🥈 Silver</div>
            <div className="text-xl font-bold text-slate-300">${data.silver_price.toLocaleString()}</div>
            <div className="text-xs text-slate-400/60">per oz</div>
          </div>
        </div>

        {/* Expanded Details */}
        {showDetails && (
          <div className="pt-3 border-t border-slate-700/50 space-y-2">
            <div className="text-sm text-slate-300">
              <p className="font-medium text-slate-200 mb-1">What This Means:</p>
              <p className="text-xs text-slate-400">{data.interpretation.what_it_means}</p>
            </div>

            <div className="text-sm text-slate-300">
              <p className="font-medium text-slate-200 mb-1">Current Signal:</p>
              <p className="text-xs text-slate-400">{data.interpretation.current_signal}</p>
            </div>

            <div className="text-sm text-slate-300">
              <p className="font-medium text-slate-200 mb-1">Historical Context:</p>
              <p className="text-xs text-slate-400">{data.interpretation.historical_note}</p>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500 pt-2">
              <span>Historical Mean: {data.historical_mean}:1</span>
              <span>Range: {data.historical_range.low}-{data.historical_range.high}:1</span>
            </div>
          </div>
        )}

        {!showDetails && (
          <button
            onClick={() => setShowDetails(true)}
            className="text-xs text-yellow-500 hover:text-yellow-400 transition-colors pt-1"
          >
            Click info icon for historical context →
          </button>
        )}
      </CardContent>
    </Card>
  )
}
