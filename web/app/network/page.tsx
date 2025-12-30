'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { getNetworkStats, getInfrastructureAudit, getParticipationStats } from '@/lib/api'
import { NetworkStatsResponse, InfrastructureAudit, ParticipationStats } from '@/lib/types'
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
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Zap,
  Target,
  Lock,
  Scale
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip
} from 'recharts'

// Dynamically import wallet-dependent component
const YourContributionSection = dynamic(
  () => import('./YourContributionSection'),
  { ssr: false, loading: () => <Skeleton className="h-64" /> }
)

// Format large numbers
function formatAlgo(amount: number): string {
  if (amount >= 1_000_000_000) {
    return `${(amount / 1_000_000_000).toFixed(2)}B`
  }
  if (amount >= 1_000_000) {
    return `${(amount / 1_000_000).toFixed(2)}M`
  }
  if (amount >= 1_000) {
    return `${(amount / 1_000).toFixed(1)}K`
  }
  return amount.toFixed(0)
}

export default function NetworkPage() {
  const [networkStats, setNetworkStats] = useState<NetworkStatsResponse | null>(null)
  const [infraData, setInfraData] = useState<InfrastructureAudit | null>(null)
  const [participationData, setParticipationData] = useState<ParticipationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showEducation, setShowEducation] = useState(false)

  useEffect(() => {
    fetchAllData()
    // Auto-refresh every 5 minutes
    const interval = setInterval(() => fetchAllData(), 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const fetchAllData = async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true)
      }

      // Fetch all data in parallel
      const [networkResult, infraResult, participationResult] = await Promise.allSettled([
        getNetworkStats(),
        getInfrastructureAudit(forceRefresh),
        getParticipationStats(forceRefresh)
      ])

      if (networkResult.status === 'fulfilled') {
        setNetworkStats(networkResult.value)
      }
      if (infraResult.status === 'fulfilled') {
        setInfraData(infraResult.value)
      }
      if (participationResult.status === 'fulfilled') {
        setParticipationData(participationResult.value)
      }

      // Only set error if all requests failed
      if (networkResult.status === 'rejected' && infraResult.status === 'rejected' && participationResult.status === 'rejected') {
        setError('Failed to fetch network data')
      } else {
        setError(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch network data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-green-400'
    if (score >= 45) return 'text-yellow-400'
    if (score >= 25) return 'text-orange-400'
    return 'text-red-400'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 75) return 'Healthy'
    if (score >= 45) return 'Moderate'
    if (score >= 25) return 'Concerning'
    return 'Critical'
  }

  const getParticipationColor = (rate: number) => {
    if (rate >= 30) return 'text-green-400'
    if (rate >= 20) return 'text-yellow-400'
    return 'text-red-400'
  }

  // Prepare chart data for stake distribution
  const getStakeChartData = () => {
    if (!networkStats) return []

    const offlineStake = networkStats.network.total_supply_algo - networkStats.network.online_stake_algo

    return [
      {
        name: 'Community Stake',
        value: networkStats.community.estimated_stake_algo,
        color: '#22c55e' // green
      },
      {
        name: 'Foundation Stake',
        value: networkStats.foundation.online_balance_algo,
        color: '#f97316' // orange
      },
      {
        name: 'Offline/Non-participating',
        value: offlineStake,
        color: '#475569' // slate
      },
    ]
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <Skeleton className="h-10 w-96 mx-auto" />
          <Skeleton className="h-6 w-64 mx-auto" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-80" />
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (error && !networkStats && !infraData && !participationData) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center space-y-6">
        <Server className="w-16 h-16 mx-auto text-red-400" />
        <h1 className="text-3xl font-bold">Network Data Unavailable</h1>
        <p className="text-slate-400">{error}</p>
        <Button
          onClick={() => fetchAllData(true)}
          className="bg-orange-600 hover:bg-orange-500"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  const chartData = getStakeChartData()

  return (
    <div className="max-w-6xl mx-auto space-y-10">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold flex items-center justify-center gap-3">
          <Globe className="w-10 h-10 text-orange-400" />
          Network Health
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          Real-time Algorand network participation and decentralization metrics
        </p>
        <button
          onClick={() => fetchAllData(true)}
          disabled={refreshing}
          className="text-sm text-orange-400 hover:text-orange-300 transition-colors disabled:opacity-50 flex items-center gap-1 mx-auto"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </div>

      {/* ============ NETWORK HEALTH DASHBOARD (4 Cards) ============ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Online Stake */}
        <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-2">
              <Coins className="w-5 h-5 text-green-400" />
              <span className="text-sm text-slate-400">Online Stake</span>
            </div>
            <div className="text-3xl font-bold text-green-400">
              {networkStats ? formatAlgo(networkStats.network.online_stake_algo) : '—'}
            </div>
            <div className="text-sm text-slate-500 mt-1">
              ALGO securing the network
            </div>
            <div className="mt-3 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-500"
                style={{ width: `${networkStats?.network.participation_rate || 0}%` }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Participation Rate */}
        <Card className="bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border-purple-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-purple-400" />
              <span className="text-sm text-slate-400">Participation Rate</span>
            </div>
            <div className={`text-3xl font-bold ${getParticipationColor(networkStats?.network.participation_rate || 0)}`}>
              {networkStats ? `${networkStats.network.participation_rate.toFixed(1)}%` : '—'}
            </div>
            <div className="text-sm text-slate-500 mt-1">
              of all ALGO participating
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs text-slate-500">
              <Info className="w-3 h-3" />
              {networkStats && networkStats.network.participation_rate >= 30 ? 'Healthy' :
               networkStats && networkStats.network.participation_rate >= 20 ? 'Moderate' : 'Low'}
            </div>
          </CardContent>
        </Card>

        {/* Card 3: Estimated Nodes */}
        <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-2">
              <Server className="w-5 h-5 text-cyan-400" />
              <span className="text-sm text-slate-400">Estimated Nodes</span>
            </div>
            <div className="text-3xl font-bold text-cyan-400">
              ~{networkStats?.estimated_node_count.toLocaleString() || '3,000'}+
            </div>
            <div className="text-sm text-slate-500 mt-1">
              Independent validators
            </div>
            <a
              href="https://nodely.io"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 mt-2 text-xs text-cyan-500 hover:text-cyan-400"
            >
              <ExternalLink className="w-3 h-3" />
              View live count
            </a>
          </CardContent>
        </Card>

        {/* Card 4: Decentralization Score */}
        <Card className="bg-gradient-to-br from-orange-500/10 to-amber-500/10 border-orange-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-5 h-5 text-orange-400" />
              <span className="text-sm text-slate-400">Decentralization Score</span>
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(networkStats?.decentralization_score || 0)}`}>
              {networkStats?.decentralization_score || infraData?.decentralization_score || '—'}/100
            </div>
            <div className="text-sm text-slate-500 mt-1">
              {getScoreLabel(networkStats?.decentralization_score || 0)} - Risks remain
            </div>
            <div className="mt-3 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  (networkStats?.decentralization_score || 0) >= 75 ? 'bg-green-500' :
                  (networkStats?.decentralization_score || 0) >= 45 ? 'bg-yellow-500' :
                  'bg-orange-500'
                }`}
                style={{ width: `${networkStats?.decentralization_score || infraData?.decentralization_score || 0}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ============ STAKE DISTRIBUTION CHART ============ */}
      {networkStats && (
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Scale className="w-5 h-5 text-orange-400" />
              Stake Distribution
            </CardTitle>
            <CardDescription>
              How online stake is distributed between Foundation and Community
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
              {/* Chart */}
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => [`${formatAlgo(value)} ALGO`, '']}
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend
                      formatter={(value) => <span className="text-slate-300">{value}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Stats */}
              <div className="space-y-4">
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Users className="w-5 h-5 text-green-400" />
                    <span className="font-medium text-green-400">Community Stake</span>
                  </div>
                  <div className="text-2xl font-bold text-slate-200">
                    {formatAlgo(networkStats.community.estimated_stake_algo)} ALGO
                  </div>
                  <div className="text-sm text-slate-400 mt-1">
                    {networkStats.community.pct_of_online_stake.toFixed(1)}% of online stake
                  </div>
                </div>

                <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Building2 className="w-5 h-5 text-orange-400" />
                    <span className="font-medium text-orange-400">Foundation Stake</span>
                  </div>
                  <div className="text-2xl font-bold text-slate-200">
                    {formatAlgo(networkStats.foundation.online_balance_algo)} ALGO
                  </div>
                  <div className="text-sm text-slate-400 mt-1">
                    {networkStats.foundation.pct_of_online_stake.toFixed(1)}% of online stake
                    <span className="text-slate-500 ml-1">
                      ({networkStats.foundation.address_count} addresses)
                    </span>
                  </div>
                  {networkStats.foundation.total_balance_algo > 0 && networkStats.foundation.online_balance_algo === 0 && (
                    <div className="mt-2 text-xs text-green-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Foundation holds {formatAlgo(networkStats.foundation.total_balance_algo)} ALGO but is NOT participating in consensus
                    </div>
                  )}
                </div>

                <div className="bg-slate-700/30 border border-slate-600/30 rounded-lg p-4">
                  <p className="text-sm text-slate-400">
                    <span className="text-slate-200 font-medium">For true decentralization,</span> community stake should exceed 80% of online participation.
                    {networkStats.community.pct_of_online_stake >= 80 ? (
                      <span className="text-green-400 ml-1">This target is currently met.</span>
                    ) : (
                      <span className="text-orange-400 ml-1">
                        Currently at {networkStats.community.pct_of_online_stake.toFixed(1)}%.
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ============ SCORE BREAKDOWN ============ */}
      {networkStats?.score_breakdown && (
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-orange-400" />
              Decentralization Score Breakdown
            </CardTitle>
            <CardDescription>
              How the score is calculated based on our strict methodology
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Positive Factors */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-green-400 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Positive Factors
                </h4>
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Community online stake ({networkStats.score_breakdown.community_online_pct.toFixed(1)}%)</span>
                    <span className="text-green-400 font-medium">+{networkStats.score_breakdown.community_online_score} pts</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Participation rate score</span>
                    <span className="text-green-400 font-medium">+{networkStats.score_breakdown.participation_rate_score} pts</span>
                  </div>
                  <div className="border-t border-green-500/30 pt-2 flex justify-between text-sm font-medium">
                    <span className="text-slate-300">Subtotal</span>
                    <span className="text-green-400">+{networkStats.score_breakdown.community_online_score + networkStats.score_breakdown.participation_rate_score} pts</span>
                  </div>
                </div>
              </div>

              {/* Risk Penalties */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-red-400 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Risk Penalties
                </h4>
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Foundation supply ({networkStats.score_breakdown.foundation_supply_pct.toFixed(1)}%)</span>
                    <span className="text-red-400 font-medium">-{networkStats.score_breakdown.foundation_supply_penalty} pts</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Potential control ({networkStats.score_breakdown.foundation_potential_control.toFixed(1)}%)</span>
                    <span className="text-red-400 font-medium">-{networkStats.score_breakdown.potential_control_penalty} pts</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Relay centralization</span>
                    <span className="text-red-400 font-medium">-{networkStats.score_breakdown.relay_centralization_penalty} pts</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Governance influence</span>
                    <span className="text-red-400 font-medium">-{networkStats.score_breakdown.governance_penalty} pts</span>
                  </div>
                  <div className="border-t border-red-500/30 pt-2 flex justify-between text-sm font-medium">
                    <span className="text-slate-300">Subtotal</span>
                    <span className="text-red-400">-{
                      networkStats.score_breakdown.foundation_supply_penalty +
                      networkStats.score_breakdown.potential_control_penalty +
                      networkStats.score_breakdown.relay_centralization_penalty +
                      networkStats.score_breakdown.governance_penalty
                    } pts</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Final Score Summary */}
            <div className="mt-6 bg-slate-800/50 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">Final Score</div>
                  <div className={`text-2xl font-bold ${getScoreColor(networkStats.score_breakdown.final_score)}`}>
                    {networkStats.score_breakdown.final_score}/100
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-medium ${getScoreColor(networkStats.score_breakdown.final_score)}`}>
                    {getScoreLabel(networkStats.score_breakdown.final_score)}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    {networkStats.score_breakdown.final_score >= 45
                      ? 'Progress being made, but risks remain'
                      : 'Significant centralization concerns'}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-500 mt-4">
              Our methodology penalizes Foundation supply concentration, potential control scenarios,
              relay node centralization, and governance influence. Score improves as community
              participation grows and infrastructure decentralizes.
            </p>
          </CardContent>
        </Card>
      )}

      {/* ============ YOUR CONTRIBUTION SECTION ============ */}
      <YourContributionSection />

      {/* ============ THE DECENTRALIZATION IMPERATIVE ============ */}
      <Card className="bg-gradient-to-br from-slate-900 via-slate-900 to-orange-900/20 border-orange-500/20">
        <CardHeader
          className="cursor-pointer"
          onClick={() => setShowEducation(!showEducation)}
        >
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-xl text-orange-400">
                <Lock className="w-5 h-5" />
                Why Decentralization Matters
              </CardTitle>
              <CardDescription className="text-slate-400 mt-1">
                The case for distributed consensus
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" className="text-slate-400">
              {showEducation ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </Button>
          </div>
        </CardHeader>

        {showEducation && (
          <CardContent className="space-y-6 text-slate-300">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  <span className="font-semibold text-red-400">Single Points of Failure</span>
                </div>
                <p className="text-sm text-slate-400">
                  Centralized systems create systemic risk. One compromised server, one court order,
                  one Terms of Service change can halt an entire network.
                </p>
              </div>

              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Scale className="w-5 h-5 text-yellow-400" />
                  <span className="font-semibold text-yellow-400">Regulatory Pressure</span>
                </div>
                <p className="text-sm text-slate-400">
                  Centralized entities can be coerced. Governments can pressure companies to censor
                  transactions, freeze accounts, or shut down services.
                </p>
              </div>

              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-5 h-5 text-green-400" />
                  <span className="font-semibold text-green-400">True Sovereignty</span>
                </div>
                <p className="text-sm text-slate-400">
                  Real sovereignty requires distributed control. No single entity should have the power
                  to unilaterally change the rules or deny access.
                </p>
              </div>

              <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-cyan-400" />
                  <span className="font-semibold text-cyan-400">Every Node Counts</span>
                </div>
                <p className="text-sm text-slate-400">
                  Each participation node strengthens the network. Your node validates transactions,
                  making the network more resistant to attack and censorship.
                </p>
              </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
              <p className="text-sm text-slate-400 italic">
                &quot;A network running on 1,000 Raspberry Pis in 1,000 different homes is infinitely more robust
                than a network running on 10,000 virtual machines in one Virginia data center.
                The former is a revolution; the latter is just a database.&quot;
              </p>
            </div>
          </CardContent>
        )}
      </Card>

      {/* ============ CALL TO ACTION CARDS ============ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Run a Node */}
        <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/30 hover:border-cyan-500/50 transition-colors">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-cyan-500/20 flex items-center justify-center">
                <Server className="w-8 h-8 text-cyan-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-cyan-400">Run a Node</h3>
                <p className="text-sm text-slate-400 mt-1">
                  Contribute to decentralization and earn rewards
                </p>
              </div>
              <a
                href="https://developer.algorand.org/docs/run-a-node/participate/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white text-sm font-medium transition-colors"
              >
                Get Started
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </CardContent>
        </Card>

        {/* Analyze Holdings */}
        <Card className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border-orange-500/30 hover:border-orange-500/50 transition-colors">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-orange-500/20 flex items-center justify-center">
                <Target className="w-8 h-8 text-orange-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-orange-400">Stack Hard Money</h3>
                <p className="text-sm text-slate-400 mt-1">
                  Build your sovereignty ratio with real assets
                </p>
              </div>
              <Link
                href="/analyze"
                className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-500 rounded-lg text-white text-sm font-medium transition-colors"
              >
                Analyze Wallet
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ============ DETAILED PARTICIPATION DATA ============ */}
      {participationData && (
        <>
          <div className="border-t border-slate-800 pt-8">
            <h2 className="text-2xl font-bold text-center mb-6 flex items-center justify-center gap-2">
              <Users className="w-7 h-7 text-purple-400" />
              Validator Details
            </h2>
          </div>

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
                  Accounts eligible for consensus rewards (30k+ ALGO)
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
                  Stake Concentration
                </CardTitle>
                <CardDescription>
                  How stake is distributed among validators
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
                        return formatAlgo(sum)
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

          {/* 3-Tier Infrastructure Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tier 1: Sovereign */}
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
              </CardContent>
            </Card>

            {/* Tier 2: Corporate */}
            <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-cyan-400 text-lg">
                  <Building2 className="w-5 h-5" />
                  Tier 2: Data Centers
                </CardTitle>
                <CardDescription className="text-xs">
                  OVH, Hetzner, Vultr, etc.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-cyan-400">{infraData.corporate_percentage}%</span>
                  <span className="text-slate-400 text-sm">({infraData.corporate_nodes})</span>
                </div>
              </CardContent>
            </Card>

            {/* Tier 3: Hyperscale */}
            <Card className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-red-400 text-lg">
                  <Cloud className="w-5 h-5" />
                  Tier 3: Hyperscale
                </CardTitle>
                <CardDescription className="text-xs">
                  AWS, Google, Azure
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-red-400">{infraData.hyperscale_percentage}%</span>
                  <span className="text-slate-400 text-sm">({infraData.hyperscale_nodes})</span>
                </div>
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
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(infraData.top_providers).slice(0, 5).map(([provider, count], index) => {
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
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(infraData.top_countries).slice(0, 5).map(([country, count], index) => {
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
            <strong className="text-slate-400">Network Stats:</strong> Online stake and participation rate from algod{' '}
            <code className="text-cyan-500">/v2/ledger/supply</code>. Foundation addresses are tracked separately.
          </div>
          <div>
            <strong className="text-slate-400">Decentralization Score:</strong> Based on community vs foundation stake distribution,
            infrastructure tier breakdown, and geographic diversity.
          </div>
          <div className="text-slate-600 pt-2 flex flex-wrap gap-4">
            <span>Network stats cached: 5 minutes</span>
            <span>Infrastructure data cached: 4 hours</span>
            {networkStats && (
              <span>Last updated: {new Date(networkStats.fetched_at).toLocaleString()}</span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
