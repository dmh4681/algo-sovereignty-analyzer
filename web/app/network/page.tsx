'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { getInfrastructureAudit } from '@/lib/api'
import { InfrastructureAudit } from '@/lib/types'
import {
  Server,
  Cloud,
  Shield,
  Globe,
  RefreshCw,
  Info,
  Building2,
  MapPin,
  Activity,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react'

export default function NetworkPage() {
  const [data, setData] = useState<InfrastructureAudit | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  const getHealthColor = (color: string) => {
    switch (color) {
      case 'green': return 'text-green-400'
      case 'yellow': return 'text-yellow-400'
      case 'orange': return 'text-orange-400'
      case 'red': return 'text-red-400'
      default: return 'text-slate-400'
    }
  }

  const getHealthBgColor = (color: string) => {
    switch (color) {
      case 'green': return 'bg-green-500'
      case 'yellow': return 'bg-yellow-500'
      case 'orange': return 'bg-orange-500'
      case 'red': return 'bg-red-500'
      default: return 'bg-slate-500'
    }
  }

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy': return <CheckCircle2 className="w-6 h-6 text-green-400" />
      case 'moderate': return <Activity className="w-6 h-6 text-yellow-400" />
      case 'concerning': return <AlertTriangle className="w-6 h-6 text-orange-400" />
      case 'critical': return <AlertTriangle className="w-6 h-6 text-red-400" />
      default: return <Activity className="w-6 h-6 text-slate-400" />
    }
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <Skeleton className="h-10 w-96 mx-auto" />
          <Skeleton className="h-6 w-64 mx-auto" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center space-y-6">
        <Server className="w-16 h-16 mx-auto text-red-400" />
        <h1 className="text-3xl font-bold">Network Audit Failed</h1>
        <p className="text-slate-400">{error || 'Failed to load infrastructure data'}</p>
        <button
          onClick={() => fetchAudit(true)}
          className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white font-medium transition-colors"
        >
          <RefreshCw className="w-4 h-4 inline mr-2" />
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold flex items-center justify-center gap-3">
          <Server className="w-10 h-10 text-cyan-400" />
          Network Sovereignty Audit
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          Real-time analysis of Algorand relay node infrastructure decentralization
        </p>
        <button
          onClick={() => fetchAudit(true)}
          disabled={refreshing}
          className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors disabled:opacity-50 flex items-center gap-1 mx-auto"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </div>

      {/* Main Score Card */}
      <Card className="bg-gradient-to-br from-cyan-500/20 via-blue-500/10 to-purple-500/20 border-cyan-500/40">
        <CardContent className="py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
            {/* Score */}
            <div className="text-center">
              <div className="text-6xl font-bold text-cyan-400 mb-2">
                {data.decentralization_score}
              </div>
              <div className="text-slate-400">Decentralization Score</div>
              <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden mt-4 max-w-xs mx-auto">
                <div
                  className={`h-full ${getHealthBgColor(data.interpretation.color)} transition-all duration-500`}
                  style={{ width: `${data.decentralization_score}%` }}
                />
              </div>
            </div>

            {/* Status */}
            <div className="text-center border-x border-slate-700/50 px-4">
              <div className="flex items-center justify-center gap-2 mb-2">
                {getHealthIcon(data.interpretation.health)}
                <span className={`text-2xl font-bold capitalize ${getHealthColor(data.interpretation.color)}`}>
                  {data.interpretation.health}
                </span>
              </div>
              <p className="text-slate-400 text-sm">
                {data.interpretation.message}
              </p>
            </div>

            {/* Node Count */}
            <div className="text-center">
              <div className="text-5xl font-bold text-slate-200 mb-2">
                {data.total_nodes}
              </div>
              <div className="text-slate-400">Relay Nodes Discovered</div>
              <div className="text-xs text-slate-500 mt-2">
                via DNS SRV records
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cloud vs Sovereign */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border-orange-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-400">
              <Cloud className="w-5 h-5" />
              Centralized Cloud
            </CardTitle>
            <CardDescription>
              Nodes running on AWS, Google, Microsoft, etc.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-bold text-orange-400">{data.cloud_percentage}%</span>
              <span className="text-slate-400">({data.cloud_nodes} nodes)</span>
            </div>
            <p className="text-sm text-slate-500 mt-4">
              These nodes depend on centralized infrastructure providers who can be pressured,
              censored, or experience coordinated outages.
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-400">
              <Shield className="w-5 h-5" />
              Sovereign Infrastructure
            </CardTitle>
            <CardDescription>
              Independent ISPs, residential, or self-hosted
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-bold text-green-400">{data.sovereign_percentage}%</span>
              <span className="text-slate-400">({data.sovereign_nodes} nodes)</span>
            </div>
            <p className="text-sm text-slate-500 mt-4">
              These nodes are harder to censor or pressure. They contribute to true network
              decentralization and resilience.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Provider & Country Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Providers */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-cyan-400" />
              Top Infrastructure Providers
            </CardTitle>
            <CardDescription>
              Organizations hosting relay nodes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(data.top_providers).map(([provider, count], index) => {
                const percentage = (count / data.total_nodes) * 100
                return (
                  <div key={provider}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-300 truncate max-w-[200px]" title={provider}>
                        {index + 1}. {provider}
                      </span>
                      <span className="text-slate-400">{count} ({percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-cyan-500/60"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Top Countries */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-cyan-400" />
              Geographic Distribution
            </CardTitle>
            <CardDescription>
              Countries hosting relay nodes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(data.top_countries).map(([country, count], index) => {
                const percentage = (count / data.total_nodes) * 100
                return (
                  <div key={country}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-300">
                        {index + 1}. {country}
                      </span>
                      <span className="text-slate-400">{count} ({percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-purple-500/60"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Interpretation & Recommendation */}
      <Card className="bg-gradient-to-r from-slate-900 to-slate-800 border-slate-700">
        <CardContent className="py-6">
          <div className="flex items-start gap-4">
            <Info className="w-6 h-6 text-cyan-400 flex-shrink-0 mt-1" />
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-lg text-slate-200 mb-1">Analysis</h3>
                <p className="text-slate-400">{data.interpretation.cloud_dependency}</p>
              </div>
              <div>
                <h3 className="font-semibold text-lg text-cyan-400 mb-1">Recommendation</h3>
                <p className="text-slate-300">{data.interpretation.recommendation}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Methodology */}
      <Card className="bg-slate-900/30 border-slate-800/50">
        <CardHeader>
          <CardTitle className="text-slate-400 text-sm">Methodology</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-500 space-y-2">
          <p>
            <strong className="text-slate-400">Discovery:</strong> Relay nodes are discovered by querying
            DNS SRV records at <code className="text-cyan-500">_algobootstrap._tcp.mainnet.algorand.network</code>
          </p>
          <p>
            <strong className="text-slate-400">Classification:</strong> Each node's IP is analyzed to determine
            the hosting provider. Nodes on AWS, Google Cloud, Microsoft Azure, and similar platforms are
            classified as "cloud". All others are "sovereign".
          </p>
          <p>
            <strong className="text-slate-400">Scoring:</strong> The decentralization score weighs sovereign
            node percentage (40%), provider diversity (30%), and geographic diversity (30%).
          </p>
          <p className="text-slate-600 pt-2">
            Data cached for 4 hours. Last updated: {new Date(data.timestamp).toLocaleString()}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
