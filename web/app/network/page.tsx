'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { getInfrastructureAudit, getParticipationStats } from '@/lib/api'
import { InfrastructureAudit, ParticipationStats } from '@/lib/types'
import {
  Server,
  Cloud,
  Shield,
  Globe,
  RefreshCw,
  Info,
  Building2,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Users,
  Coins,
  TrendingUp,
  Award,
  ExternalLink
} from 'lucide-react'

export default function NetworkPage() {
  const [infraData, setInfraData] = useState<InfrastructureAudit | null>(null)
  const [participationData, setParticipationData] = useState<ParticipationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true)
      }

      // Fetch both in parallel
      const [infraResult, participationResult] = await Promise.all([
        getInfrastructureAudit(forceRefresh),
        getParticipationStats(forceRefresh)
      ])

      setInfraData(infraResult)
      setParticipationData(participationResult)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch network data')
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
      case 'healthy':
      case 'strong':
        return <CheckCircle2 className="w-6 h-6 text-green-400" />
      case 'moderate':
        return <Activity className="w-6 h-6 text-yellow-400" />
      case 'concerning':
      case 'low':
        return <AlertTriangle className="w-6 h-6 text-orange-400" />
      case 'critical':
        return <AlertTriangle className="w-6 h-6 text-red-400" />
      default:
        return <Activity className="w-6 h-6 text-slate-400" />
    }
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <Skeleton className="h-10 w-96 mx-auto" />
          <Skeleton className="h-6 w-64 mx-auto" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (error || (!infraData && !participationData)) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center space-y-6">
        <Server className="w-16 h-16 mx-auto text-red-400" />
        <h1 className="text-3xl font-bold">Network Audit Failed</h1>
        <p className="text-slate-400">{error || 'Failed to load network data'}</p>
        <button
          onClick={() => fetchAllData(true)}
          className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white font-medium transition-colors"
        >
          <RefreshCw className="w-4 h-4 inline mr-2" />
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-10">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold flex items-center justify-center gap-3">
          <Server className="w-10 h-10 text-cyan-400" />
          Network Sovereignty Audit
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          Real-time analysis of Algorand network decentralization
        </p>
        <button
          onClick={() => fetchAllData(true)}
          disabled={refreshing}
          className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors disabled:opacity-50 flex items-center gap-1 mx-auto"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </div>

      {/* ============ PARTICIPATION SECTION ============ */}
      {participationData && (
        <>
          <div className="border-t border-slate-800 pt-8">
            <h2 className="text-2xl font-bold text-center mb-6 flex items-center justify-center gap-2">
              <Users className="w-7 h-7 text-purple-400" />
              Consensus Participation
            </h2>
          </div>

          {/* Online Stake Card */}
          <Card className="bg-gradient-to-br from-purple-500/20 via-indigo-500/10 to-blue-500/20 border-purple-500/40">
            <CardContent className="py-8">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                {/* Online Stake */}
                <div className="text-center">
                  <div className="text-5xl font-bold text-purple-400 mb-2">
                    {participationData.online_stake.formatted}
                  </div>
                  <div className="text-slate-400">ALGO Online</div>
                  <div className="text-sm text-purple-400/80 mt-1">
                    {participationData.online_stake.percentage.toFixed(1)}% of supply
                  </div>
                </div>

                {/* Status */}
                <div className="text-center border-x border-slate-700/50 px-4">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    {getHealthIcon(participationData.interpretation.health)}
                    <span className={`text-2xl font-bold capitalize ${getHealthColor(participationData.interpretation.color)}`}>
                      {participationData.interpretation.health}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm">
                    {participationData.interpretation.message}
                  </p>
                </div>

                {/* Total Supply */}
                <div className="text-center">
                  <div className="text-4xl font-bold text-slate-300 mb-2">
                    {participationData.total_supply.formatted}
                  </div>
                  <div className="text-slate-400">Total ALGO Supply</div>
                  <div className="text-xs text-slate-500 mt-1">
                    Round #{participationData.current_round.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Online Stake Progress */}
              <div className="mt-6 max-w-2xl mx-auto">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-400">Online Stake</span>
                  <span className="text-purple-400">{participationData.online_stake.percentage.toFixed(1)}%</span>
                </div>
                <div className="h-4 bg-slate-700/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-500"
                    style={{ width: `${participationData.online_stake.percentage}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Incentive Eligible & Top Validators */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Incentive Eligible */}
            <Card className="bg-gradient-to-br from-yellow-500/10 to-amber-500/10 border-yellow-500/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-yellow-400">
                  <Award className="w-5 h-5" />
                  Incentive Eligible Validators
                </CardTitle>
                <CardDescription>
                  Accounts eligible for consensus rewards
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-bold text-yellow-400">
                    {participationData.validators.incentive_eligible_count}
                  </span>
                  <span className="text-slate-400">validators</span>
                </div>
                <div className="text-sm text-slate-400">
                  Combined stake: <span className="text-yellow-400 font-medium">
                    {participationData.validators.incentive_eligible_stake}
                  </span> ALGO
                </div>
              </CardContent>
            </Card>

            {/* Stake Distribution */}
            <Card className="bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-indigo-500/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-indigo-400">
                  <TrendingUp className="w-5 h-5" />
                  Stake Distribution
                </CardTitle>
                <CardDescription>
                  How participation is distributed
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Top Validator</span>
                    <span className="text-indigo-400 font-medium">
                      {participationData.validators.top_validators[0]?.stake_formatted || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Top 10 Combined</span>
                    <span className="text-indigo-400 font-medium">
                      {(() => {
                        const top10 = participationData.validators.top_validators.slice(0, 10)
                        const sum = top10.reduce((acc, v) => acc + v.stake_algo, 0)
                        if (sum >= 1_000_000) return `${(sum / 1_000_000).toFixed(1)}M`
                        if (sum >= 1_000) return `${(sum / 1_000).toFixed(1)}K`
                        return sum.toFixed(0)
                      })()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Active Validators (24h)</span>
                    <span className="text-green-400 font-medium">
                      {participationData.validators.top_validators.filter(v => v.recently_active).length}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Validators Table */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Coins className="w-5 h-5 text-purple-400" />
                Top Validators by Stake
              </CardTitle>
              <CardDescription>
                Largest participating accounts (sampled from {'>'}1M ALGO holders)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800">
                      <th className="text-left py-3 px-2 text-slate-400 font-medium">#</th>
                      <th className="text-left py-3 px-2 text-slate-400 font-medium">Address</th>
                      <th className="text-right py-3 px-2 text-slate-400 font-medium">Stake</th>
                      <th className="text-center py-3 px-2 text-slate-400 font-medium">Incentive</th>
                      <th className="text-center py-3 px-2 text-slate-400 font-medium">Keys Valid</th>
                      <th className="text-center py-3 px-2 text-slate-400 font-medium">Active</th>
                    </tr>
                  </thead>
                  <tbody>
                    {participationData.validators.top_validators.slice(0, 10).map((validator, idx) => (
                      <tr key={validator.address} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                        <td className="py-3 px-2 text-slate-500">{idx + 1}</td>
                        <td className="py-3 px-2">
                          <a
                            href={`https://explorer.perawallet.app/address/${validator.address}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-purple-400 hover:text-purple-300 font-mono text-xs flex items-center gap-1"
                          >
                            {validator.address_short}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </td>
                        <td className="py-3 px-2 text-right font-medium text-slate-200">
                          {validator.stake_formatted}
                        </td>
                        <td className="py-3 px-2 text-center">
                          {validator.incentive_eligible ? (
                            <span className="text-yellow-400">Yes</span>
                          ) : (
                            <span className="text-slate-500">No</span>
                          )}
                        </td>
                        <td className="py-3 px-2 text-center">
                          {validator.keys_valid ? (
                            <CheckCircle2 className="w-4 h-4 text-green-400 inline" />
                          ) : (
                            <AlertTriangle className="w-4 h-4 text-orange-400 inline" />
                          )}
                        </td>
                        <td className="py-3 px-2 text-center">
                          {validator.recently_active ? (
                            <span className="inline-block w-2 h-2 bg-green-400 rounded-full" />
                          ) : (
                            <span className="inline-block w-2 h-2 bg-slate-600 rounded-full" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* ============ RELAY INFRASTRUCTURE SECTION ============ */}
      {infraData && (
        <>
          <div className="border-t border-slate-800 pt-8">
            <h2 className="text-2xl font-bold text-center mb-6 flex items-center justify-center gap-2">
              <Server className="w-7 h-7 text-cyan-400" />
              Relay Node Infrastructure
            </h2>
          </div>

          {/* Main Score Card */}
          <Card className="bg-gradient-to-br from-cyan-500/20 via-blue-500/10 to-purple-500/20 border-cyan-500/40">
            <CardContent className="py-8">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                {/* Score */}
                <div className="text-center">
                  <div className="text-6xl font-bold text-cyan-400 mb-2">
                    {infraData.decentralization_score}
                  </div>
                  <div className="text-slate-400">Decentralization Score</div>
                  <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden mt-4 max-w-xs mx-auto">
                    <div
                      className={`h-full ${getHealthBgColor(infraData.interpretation.color)} transition-all duration-500`}
                      style={{ width: `${infraData.decentralization_score}%` }}
                    />
                  </div>
                </div>

                {/* Status */}
                <div className="text-center border-x border-slate-700/50 px-4">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    {getHealthIcon(infraData.interpretation.health)}
                    <span className={`text-2xl font-bold capitalize ${getHealthColor(infraData.interpretation.color)}`}>
                      {infraData.interpretation.health}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm">
                    {infraData.interpretation.message}
                  </p>
                </div>

                {/* Node Count */}
                <div className="text-center">
                  <div className="text-5xl font-bold text-slate-200 mb-2">
                    {infraData.total_nodes}
                  </div>
                  <div className="text-slate-400">Relay Nodes Discovered</div>
                  <div className="text-xs text-slate-500 mt-2">
                    via DNS SRV records
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 3-Tier Infrastructure Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tier 1: Sovereign (Green) */}
            <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-green-400 text-lg">
                  <Shield className="w-5 h-5" />
                  Tier 1: Sovereign
                </CardTitle>
                <CardDescription className="text-xs">
                  Residential ISPs & self-hosted
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-green-400">{infraData.sovereign_percentage}%</span>
                  <span className="text-slate-400 text-sm">({infraData.sovereign_nodes})</span>
                </div>
                <p className="text-xs text-slate-500 mt-3">
                  True decentralization. Residential connections are harder to shut down en masse.
                </p>
              </CardContent>
            </Card>

            {/* Tier 2: Corporate (Yellow) */}
            <Card className="bg-gradient-to-br from-yellow-500/10 to-amber-500/10 border-yellow-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-yellow-400 text-lg">
                  <Building2 className="w-5 h-5" />
                  Tier 2: Corporate
                </CardTitle>
                <CardDescription className="text-xs">
                  Data centers (OVH, Hetzner, TeraSwitch)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-yellow-400">{infraData.corporate_percentage}%</span>
                  <span className="text-slate-400 text-sm">({infraData.corporate_nodes})</span>
                </div>
                <p className="text-xs text-slate-500 mt-3">
                  Better than hyperscale, but single points of failure. Corporate billing can shut down nodes.
                </p>
              </CardContent>
            </Card>

            {/* Tier 3: Hyperscale (Red) */}
            <Card className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-red-400 text-lg">
                  <Cloud className="w-5 h-5" />
                  Tier 3: Hyperscale
                </CardTitle>
                <CardDescription className="text-xs">
                  AWS, Google, Microsoft Azure
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-red-400">{infraData.hyperscale_percentage}%</span>
                  <span className="text-slate-400 text-sm">({infraData.hyperscale_nodes})</span>
                </div>
                <p className="text-xs text-slate-500 mt-3">
                  &quot;Kill switch&quot; zone. Government pressure or coordinated action can disable these nodes.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Risk Assessment Banner */}
          <Card className={`border ${
            infraData.sovereign_percentage < 10 ? 'bg-red-500/10 border-red-500/40' :
            infraData.sovereign_percentage < 30 ? 'bg-yellow-500/10 border-yellow-500/40' :
            'bg-green-500/10 border-green-500/40'
          }`}>
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className={`w-5 h-5 mt-0.5 ${
                  infraData.sovereign_percentage < 10 ? 'text-red-400' :
                  infraData.sovereign_percentage < 30 ? 'text-yellow-400' :
                  'text-green-400'
                }`} />
                <div>
                  <p className="font-medium text-slate-200">
                    {infraData.interpretation.risk_assessment}
                  </p>
                  <p className="text-sm text-slate-400 mt-1">
                    {infraData.interpretation.sovereign_status}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

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
                  {Object.entries(infraData.top_providers).map(([provider, count], index) => {
                    const percentage = (count / infraData.total_nodes) * 100
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
                  {Object.entries(infraData.top_countries).map(([country, count], index) => {
                    const percentage = (count / infraData.total_nodes) * 100
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
        </>
      )}

      {/* Philosophy Section */}
      <Card className="bg-gradient-to-br from-slate-900 via-slate-900 to-orange-900/20 border-orange-500/20">
        <CardHeader>
          <CardTitle className="text-xl text-orange-400">
            The Protocol of Physical Reality
          </CardTitle>
          <CardDescription className="text-slate-400 italic">
            &quot;Code is Law&quot; is a delusion if the hardware is rented.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 text-slate-300">
          <p>
            We often measure sovereignty in cryptographic terms: keys, signatures, and ledger immutability.
            But the digital world does not float in the ether; it lives on metal, silicon, and fiber optics.
          </p>

          {/* The Sovereignty Stack */}
          <div className="space-y-3">
            <h3 className="font-semibold text-slate-200">The Sovereignty Stack</h3>
            <p className="text-sm text-slate-400">True autonomy requires ownership at every layer:</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                <div className="text-orange-400 font-bold mb-1">Layer 1: Financial</div>
                <div className="text-xs text-slate-400">The Asset</div>
                <p className="text-sm mt-2">Holding Bitcoin or Gold. You own the value.</p>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <div className="text-yellow-400 font-bold mb-1">Layer 2: Digital</div>
                <div className="text-xs text-slate-400">The Keys</div>
                <p className="text-sm mt-2">Holding your own private keys. You own the access.</p>
              </div>
              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <div className="text-green-400 font-bold mb-1">Layer 3: Physical</div>
                <div className="text-xs text-slate-400">The Node</div>
                <p className="text-sm mt-2">Owning the hardware that validates the truth.</p>
              </div>
            </div>
          </div>

          {/* Cloud Feudalism */}
          <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4">
            <h3 className="font-semibold text-red-400 mb-2">The &quot;Cloud Feudalism&quot; Trap</h3>
            <p className="text-sm">
              If a blockchain runs primarily on Amazon AWS or Google Cloud, it is not a sovereign nation; it is a tenant.
              It exists at the pleasure of a corporate landlord. If the landlord changes the Terms of Service,
              the &quot;immutable&quot; ledger vanishes.
            </p>
          </div>

          {/* Why We Audit */}
          <div>
            <h3 className="font-semibold text-slate-200 mb-2">Why We Audit</h3>
            <p className="text-sm text-slate-400">
              On this platform, we track the <span className="text-orange-400">Sovereignty Premium</span>.
              We distinguish between networks that are merely &quot;decentralized in software&quot; (governance)
              and those that are <span className="text-green-400">&quot;decentralized in physics&quot;</span> (hardware).
            </p>
            <p className="text-sm text-slate-500 mt-3 italic">
              A network running on 1,000 Raspberry Pis in 1,000 different homes is infinitely more robust
              than a network running on 10,000 virtual machines in one Virginia data center.
              The former is a revolution; the latter is just a database.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Methodology & Info */}
      <Card className="bg-slate-900/30 border-slate-800/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-slate-400 text-sm">
            <Info className="w-4 h-4" />
            Methodology
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-500 space-y-3">
          <div>
            <strong className="text-slate-400">Relay Nodes:</strong> Discovered via DNS SRV records at{' '}
            <code className="text-cyan-500">_algobootstrap._tcp.mainnet.algorand.network</code>.
            Each IP is classified into 3 tiers: <span className="text-green-400">Sovereign</span> (residential ISPs),{' '}
            <span className="text-yellow-400">Corporate</span> (data centers like OVH, Hetzner), or{' '}
            <span className="text-red-400">Hyperscale</span> (AWS, Google, Azure).
          </div>
          <div>
            <strong className="text-slate-400">Participation:</strong> Online stake from algod{' '}
            <code className="text-cyan-500">/v2/ledger/supply</code>. Top validators sampled from
            indexer accounts with {'>'}1M ALGO that are marked &quot;Online&quot; with valid participation keys.
          </div>
          <div>
            <strong className="text-slate-400">Scoring:</strong> Infrastructure tier (50% weight: sovereign=full,
            corporate=half, hyperscale=zero), provider diversity (25%), and geographic diversity (25%).
            Concentration penalties apply if any provider exceeds 15% share.
          </div>
          <div className="text-slate-600 pt-2 flex flex-wrap gap-4">
            <span>Relay data cached: 4 hours</span>
            <span>Participation data cached: 15 minutes</span>
            {infraData && (
              <span>Last updated: {new Date(infraData.timestamp).toLocaleString()}</span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
