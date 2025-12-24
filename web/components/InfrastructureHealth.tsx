'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { getInfrastructureAudit } from '@/lib/api'
import { InfrastructureAudit } from '@/lib/types'
import { Server, Cloud, Shield, Globe, RefreshCw, Info, ChevronDown, ChevronUp } from 'lucide-react'

export default function InfrastructureHealth() {
  const [data, setData] = useState<InfrastructureAudit | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    fetchAudit()
  }, [])

  const fetchAudit = async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true)
      }
      const result = await getInfrastructureAudit(forceRefresh)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch infrastructure data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  if (loading) {
    return (
      <Card className="bg-gradient-to-br from-cyan-500/10 via-blue-500/5 to-purple-500/10 border-cyan-500/30">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Server className="w-5 h-5" />
              Network Infrastructure
            </CardTitle>
            <Skeleton className="h-6 w-20" />
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-full mb-4" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>
    )
  }

  if (error || !data) {
    return (
      <Card className="bg-gradient-to-br from-red-500/10 via-orange-500/5 to-yellow-500/10 border-red-500/30">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Server className="w-5 h-5" />
            Network Infrastructure
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-400 text-sm">{error || 'Failed to load data'}</p>
          <button
            onClick={() => fetchAudit(true)}
            className="mt-2 text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        </CardContent>
      </Card>
    )
  }

  const getHealthColor = () => {
    switch (data.interpretation.color) {
      case 'green':
        return 'text-green-400'
      case 'yellow':
        return 'text-yellow-400'
      case 'orange':
        return 'text-orange-400'
      case 'red':
        return 'text-red-400'
      default:
        return 'text-slate-400'
    }
  }

  const getHealthBgColor = () => {
    switch (data.interpretation.color) {
      case 'green':
        return 'bg-green-500'
      case 'yellow':
        return 'bg-yellow-500'
      case 'orange':
        return 'bg-orange-500'
      case 'red':
        return 'bg-red-500'
      default:
        return 'bg-slate-500'
    }
  }

  const getGradient = () => {
    switch (data.interpretation.color) {
      case 'green':
        return 'from-green-500/20 via-emerald-500/10 to-cyan-500/20'
      case 'yellow':
        return 'from-yellow-500/20 via-amber-500/10 to-orange-500/20'
      case 'orange':
        return 'from-orange-500/20 via-red-500/10 to-pink-500/20'
      case 'red':
        return 'from-red-500/20 via-rose-500/10 to-pink-500/20'
      default:
        return 'from-cyan-500/20 via-blue-500/10 to-purple-500/20'
    }
  }

  return (
    <Card className={`bg-gradient-to-br ${getGradient()} border-cyan-500/40`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Server className="w-5 h-5 text-cyan-400" />
              Relay Node Sovereignty
            </CardTitle>
            <CardDescription className="mt-1">
              {data.total_nodes} relay nodes audited
            </CardDescription>
          </div>
          <button
            onClick={() => fetchAudit(true)}
            disabled={refreshing}
            className="text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
            aria-label="Refresh data"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Decentralization Score Gauge */}
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-slate-400">Decentralization Score</span>
            <span className={`text-2xl font-bold ${getHealthColor()}`}>
              {data.decentralization_score}/100
            </span>
          </div>

          {/* Progress Bar */}
          <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden">
            <div
              className={`h-full ${getHealthBgColor()} transition-all duration-500 ease-out`}
              style={{ width: `${data.decentralization_score}%` }}
            />
          </div>

          {/* Status Message */}
          <p className={`text-sm ${getHealthColor()}`}>
            {data.interpretation.message}
          </p>
        </div>

        {/* Cloud vs Sovereign Split */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-orange-500/10 rounded-lg border border-orange-500/30 text-center">
            <div className="flex items-center justify-center gap-1 text-orange-400 mb-1">
              <Cloud className="w-4 h-4" />
              <span className="text-xs font-medium">Cloud</span>
            </div>
            <div className="text-2xl font-bold text-orange-400">
              {data.cloud_percentage}%
            </div>
            <div className="text-xs text-orange-400/60">
              {data.cloud_nodes} nodes
            </div>
          </div>

          <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/30 text-center">
            <div className="flex items-center justify-center gap-1 text-green-400 mb-1">
              <Shield className="w-4 h-4" />
              <span className="text-xs font-medium">Sovereign</span>
            </div>
            <div className="text-2xl font-bold text-green-400">
              {data.sovereign_percentage}%
            </div>
            <div className="text-xs text-green-400/60">
              {data.sovereign_nodes} nodes
            </div>
          </div>
        </div>

        {/* Expandable Details */}
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="w-full flex items-center justify-center gap-1 text-sm text-slate-400 hover:text-slate-200 transition-colors py-1"
        >
          {showDetails ? (
            <>
              <ChevronUp className="w-4 h-4" /> Hide Details
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" /> Show Details
            </>
          )}
        </button>

        {showDetails && (
          <div className="space-y-4 pt-2 border-t border-slate-700/50">
            {/* Top Providers */}
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <Cloud className="w-4 h-4" /> Top Providers
              </h4>
              <div className="space-y-1">
                {Object.entries(data.top_providers).slice(0, 5).map(([provider, count]) => (
                  <div key={provider} className="flex justify-between text-xs">
                    <span className="text-slate-400 truncate max-w-[180px]" title={provider}>
                      {provider}
                    </span>
                    <span className="text-slate-300 font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Countries */}
            <div>
              <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <Globe className="w-4 h-4" /> Geographic Distribution
              </h4>
              <div className="space-y-1">
                {Object.entries(data.top_countries).slice(0, 5).map(([country, count]) => (
                  <div key={country} className="flex justify-between text-xs">
                    <span className="text-slate-400">{country}</span>
                    <span className="text-slate-300 font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Interpretation */}
            <div className="p-3 bg-slate-800/50 rounded-lg space-y-2">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                <div className="text-xs text-slate-400">
                  <p className="mb-1">{data.interpretation.cloud_dependency}</p>
                  <p className="text-cyan-400">{data.interpretation.recommendation}</p>
                </div>
              </div>
            </div>

            {/* Cache Info */}
            <div className="text-xs text-slate-500 text-center">
              Data refreshes every 4 hours
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
