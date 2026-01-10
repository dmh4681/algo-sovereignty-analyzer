'use client'

import { useState, useEffect, useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  BubbleController,
  ArcElement
} from 'chart.js'
import { Line, Bar, Bubble } from 'react-chartjs-2'
import {
  LayoutDashboard,
  TrendingUp,
  Database,
  Shield,
  Pickaxe,
  DollarSign,
  TrendingDown,
  Award,
  Crown,
  Target,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  getMinerMetrics,
  getSectorStats,
  type MinerMetric,
  type SectorStats
} from '@/lib/api'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  BubbleController,
  ArcElement
)

// --- Sovereignty Score Calculation ---

interface SovereigntyScore {
  ticker: string
  company: string
  totalScore: number
  jurisdictionScore: number  // 35% weight
  aiscScore: number          // 25% weight
  fcfYieldScore: number      // 20% weight
  productionTrendScore: number // 20% weight
  badge: string
  badgeColor: string
  tier1: number
  aisc: number
  fcfYield: number
  productionGrowth: number
}

function calculateSovereigntyScores(
  latestData: MinerMetric[],
  historicalData: MinerMetric[]
): SovereigntyScore[] {
  if (latestData.length === 0) return []

  // Get min/max values for normalization
  const aiscs = latestData.map(d => d.aisc)
  const minAisc = Math.min(...aiscs)
  const maxAisc = Math.max(...aiscs)

  const tier1s = latestData.map(d => d.tier1)
  const minTier1 = Math.min(...tier1s)
  const maxTier1 = Math.max(...tier1s)

  // Calculate FCF yield (FCF / Market Cap * 100)
  const fcfYields = latestData.map(d => (d.fcf / d.market_cap) * 100)
  const minFcfYield = Math.min(...fcfYields)
  const maxFcfYield = Math.max(...fcfYields)

  // Calculate production trends (% change from oldest to newest)
  const productionGrowths: Record<string, number> = {}
  latestData.forEach(miner => {
    const companyHistory = historicalData
      .filter(d => d.ticker === miner.ticker)
      .sort((a, b) => a.period.localeCompare(b.period))

    if (companyHistory.length >= 2) {
      const oldest = companyHistory[0].production
      const newest = companyHistory[companyHistory.length - 1].production
      productionGrowths[miner.ticker] = ((newest - oldest) / oldest) * 100
    } else {
      productionGrowths[miner.ticker] = 0
    }
  })

  const growthValues = Object.values(productionGrowths)
  const minGrowth = Math.min(...growthValues)
  const maxGrowth = Math.max(...growthValues)

  // Normalize function (0-100 scale)
  const normalize = (value: number, min: number, max: number, invert = false) => {
    if (max === min) return 50
    const normalized = ((value - min) / (max - min)) * 100
    return invert ? 100 - normalized : normalized
  }

  // Calculate scores for each miner
  const scores: SovereigntyScore[] = latestData.map((miner, idx) => {
    const fcfYield = fcfYields[idx]
    const productionGrowth = productionGrowths[miner.ticker]

    // Component scores (0-100)
    const jurisdictionScore = normalize(miner.tier1, minTier1, maxTier1)
    const aiscScore = normalize(miner.aisc, minAisc, maxAisc, true) // Lower is better
    const fcfYieldScore = normalize(fcfYield, minFcfYield, maxFcfYield)
    const productionTrendScore = normalize(productionGrowth, minGrowth, maxGrowth)

    // Weighted total (weights sum to 100)
    const totalScore = Math.round(
      jurisdictionScore * 0.35 +
      aiscScore * 0.25 +
      fcfYieldScore * 0.20 +
      productionTrendScore * 0.20
    )

    // Assign badge based on score
    let badge: string
    let badgeColor: string
    if (totalScore >= 80) {
      badge = 'Sovereignty Champion'
      badgeColor = 'bg-amber-500 text-amber-950'
    } else if (totalScore >= 65) {
      badge = 'Strong Operator'
      badgeColor = 'bg-emerald-500 text-emerald-950'
    } else if (totalScore >= 50) {
      badge = 'Steady Performer'
      badgeColor = 'bg-blue-500 text-blue-950'
    } else if (totalScore >= 35) {
      badge = 'High Risk/Reward'
      badgeColor = 'bg-orange-500 text-orange-950'
    } else {
      badge = 'Speculative'
      badgeColor = 'bg-red-500 text-red-950'
    }

    return {
      ticker: miner.ticker,
      company: miner.company,
      totalScore,
      jurisdictionScore: Math.round(jurisdictionScore),
      aiscScore: Math.round(aiscScore),
      fcfYieldScore: Math.round(fcfYieldScore),
      productionTrendScore: Math.round(productionTrendScore),
      badge,
      badgeColor,
      tier1: miner.tier1,
      aisc: miner.aisc,
      fcfYield: Math.round(fcfYield * 100) / 100,
      productionGrowth: Math.round(productionGrowth * 10) / 10
    }
  })

  // Sort by total score descending
  return scores.sort((a, b) => b.totalScore - a.totalScore)
}

// --- Score Display Components ---

interface ScoreBarProps {
  label: string
  score: number
  weight: string
  color: string
}

function ScoreBar({ label, score, weight, color }: ScoreBarProps) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-500">{weight}</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
      <div className="text-right text-xs font-mono text-slate-300">{score}/100</div>
    </div>
  )
}

interface LeaderboardCardProps {
  score: SovereigntyScore
  rank: number
}

function LeaderboardCard({ score, rank }: LeaderboardCardProps) {
  const getRankIcon = () => {
    if (rank === 1) return <Crown className="text-amber-400" size={24} />
    if (rank === 2) return <Award className="text-slate-300" size={22} />
    if (rank === 3) return <Award className="text-amber-600" size={20} />
    return <span className="text-slate-500 font-bold text-lg">#{rank}</span>
  }

  const getScoreColor = () => {
    if (score.totalScore >= 80) return 'text-amber-400'
    if (score.totalScore >= 65) return 'text-emerald-400'
    if (score.totalScore >= 50) return 'text-blue-400'
    if (score.totalScore >= 35) return 'text-orange-400'
    return 'text-red-400'
  }

  return (
    <Card className="border-slate-700 hover:border-slate-600 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Rank */}
          <div className="flex items-center justify-center w-10 h-10">
            {getRankIcon()}
          </div>

          {/* Main Info */}
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h3 className="font-bold text-slate-100">{score.ticker}</h3>
                <p className="text-xs text-slate-500">{score.company}</p>
              </div>
              <div className="text-right">
                <p className={`text-3xl font-bold ${getScoreColor()}`}>
                  {score.totalScore}
                </p>
                <p className="text-xs text-slate-500">/ 100</p>
              </div>
            </div>

            {/* Badge */}
            <span className={`inline-block px-2 py-1 rounded-full text-xs font-bold ${score.badgeColor}`}>
              {score.badge}
            </span>

            {/* Score Breakdown */}
            <div className="mt-4 space-y-3">
              <ScoreBar
                label="Jurisdiction Safety"
                score={score.jurisdictionScore}
                weight="35%"
                color="bg-emerald-500"
              />
              <ScoreBar
                label="Cost Efficiency (AISC)"
                score={score.aiscScore}
                weight="25%"
                color="bg-blue-500"
              />
              <ScoreBar
                label="FCF Yield"
                score={score.fcfYieldScore}
                weight="20%"
                color="bg-purple-500"
              />
              <ScoreBar
                label="Production Trend"
                score={score.productionTrendScore}
                weight="20%"
                color="bg-amber-500"
              />
            </div>

            {/* Raw Metrics */}
            <div className="mt-4 grid grid-cols-4 gap-2 text-center">
              <div className="bg-slate-800 rounded p-2">
                <p className="text-xs text-slate-500">Tier 1</p>
                <p className="font-mono font-bold text-slate-200">{score.tier1}%</p>
              </div>
              <div className="bg-slate-800 rounded p-2">
                <p className="text-xs text-slate-500">AISC</p>
                <p className="font-mono font-bold text-slate-200">${score.aisc}</p>
              </div>
              <div className="bg-slate-800 rounded p-2">
                <p className="text-xs text-slate-500">FCF Yield</p>
                <p className="font-mono font-bold text-slate-200">{score.fcfYield}%</p>
              </div>
              <div className="bg-slate-800 rounded p-2">
                <p className="text-xs text-slate-500">Prod Δ</p>
                <p className={`font-mono font-bold ${score.productionGrowth >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {score.productionGrowth >= 0 ? '+' : ''}{score.productionGrowth}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// --- Helper Components ---

interface StatCardProps {
  title: string
  value: string
  subtext?: string
  icon: React.ElementType
  colorClass: string
}

function StatCard({ title, value, subtext, icon: Icon, colorClass }: StatCardProps) {
  return (
    <Card className="border-slate-700">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-400">{title}</p>
            <h3 className="text-2xl font-bold text-slate-100 mt-1">{value}</h3>
            {subtext && <p className="text-xs text-slate-500 mt-1">{subtext}</p>}
          </div>
          <div className={`p-3 rounded-lg ${colorClass}`}>
            <Icon size={20} className="text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// --- Chart Components ---

interface EfficiencyScatterProps {
  data: MinerMetric[]
}

function EfficiencyScatter({ data }: EfficiencyScatterProps) {
  const chartData = {
    datasets: data.map(d => ({
      label: d.ticker,
      data: [{ x: d.production, y: d.aisc, r: Math.sqrt(d.market_cap) * 3 }],
      backgroundColor: d.aisc < 1200 ? '#10b981' : d.aisc > 1350 ? '#ef4444' : '#f59e0b',
    }))
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'right' as const, labels: { color: '#94a3b8' } },
      tooltip: {
        callbacks: {
          label: (ctx: unknown) => {
            const item = ctx as { raw: { x: number; y: number } }
            return `${item.raw.x} Moz @ $${item.raw.y}/oz AISC`
          }
        }
      }
    },
    scales: {
      y: {
        title: { display: true, text: 'AISC ($/oz) - Lower is Better', color: '#94a3b8' },
        min: 800,
        max: 1800,
        ticks: { color: '#94a3b8' },
        grid: { color: '#334155' }
      },
      x: {
        title: { display: true, text: 'Quarterly Production (Moz)', color: '#94a3b8' },
        min: 0,
        ticks: { color: '#94a3b8' },
        grid: { color: '#334155' }
      }
    }
  }

  return <Bubble data={chartData} options={options} />
}

interface TrendLineChartProps {
  historicalData: MinerMetric[]
  metric: keyof MinerMetric
  title: string
  yAxisTitle: string
}

function TrendLineChart({ historicalData, metric, title, yAxisTitle }: TrendLineChartProps) {
  const companies = [...new Set(historicalData.map(d => d.ticker))]
  const sortedHistory = [...historicalData].sort((a, b) => a.period.localeCompare(b.period))
  const periods = [...new Set(sortedHistory.map(d => d.period))]

  const colors = ['#1e3a8a', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  const datasets = companies.map((ticker, idx) => {
    const companyData = sortedHistory.filter(d => d.ticker === ticker)
    const dataPoints = periods.map(p => {
      const entry = companyData.find(d => d.period === p)
      return entry ? (entry[metric] as number) : null
    })

    return {
      label: ticker,
      data: dataPoints,
      borderColor: colors[idx % colors.length],
      backgroundColor: colors[idx % colors.length],
      tension: 0.3
    }
  })

  const data = { labels: periods, datasets }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8' } }
    },
    scales: {
      y: {
        title: { display: true, text: yAxisTitle, color: '#94a3b8' },
        ticks: { color: '#94a3b8' },
        grid: { color: '#334155' }
      },
      x: {
        ticks: { color: '#94a3b8' },
        grid: { color: '#334155' }
      }
    }
  }

  return (
    <div className="h-80">
      <h3 className="text-sm font-bold text-slate-400 mb-4">{title}</h3>
      <Line data={data} options={options} />
    </div>
  )
}

// --- Main Component ---

type ViewType = 'dashboard' | 'scores' | 'trends'

export function GoldTracker() {
  const [view, setView] = useState<ViewType>('dashboard')
  const [rawData, setRawData] = useState<MinerMetric[]>([])
  const [stats, setStats] = useState<SectorStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [metricsRes, statsRes] = await Promise.all([
          getMinerMetrics(100),
          getSectorStats()
        ])
        setRawData(metricsRes.metrics)
        setStats(statsRes.stats)
        setError(null)
      } catch (err) {
        console.error('Error fetching data:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  // Derived: Latest data per company for dashboard
  const latestData = useMemo(() => {
    const uniqueCompanies: Record<string, MinerMetric> = {}
    const sorted = [...rawData].sort((a, b) => b.period.localeCompare(a.period))

    sorted.forEach(item => {
      if (!uniqueCompanies[item.ticker]) {
        uniqueCompanies[item.ticker] = item
      }
    })
    return Object.values(uniqueCompanies)
  }, [rawData])

  // Sovereignty Scores
  const sovereigntyScores = useMemo(() => {
    return calculateSovereigntyScores(latestData, rawData)
  }, [latestData, rawData])

  // Navigation
  const Navigation = () => (
    <nav className="flex items-center space-x-2 bg-slate-800 p-1 rounded-lg">
      <button
        onClick={() => setView('dashboard')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'dashboard'
            ? 'bg-amber-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <LayoutDashboard size={16} /> Dashboard
      </button>
      <button
        onClick={() => setView('scores')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'scores'
            ? 'bg-amber-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <Target size={16} /> Scores
      </button>
      <button
        onClick={() => setView('trends')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'trends'
            ? 'bg-amber-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <TrendingUp size={16} /> Trends
      </button>
    </nav>
  )

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-400">{error}</p>
        <Button onClick={() => window.location.reload()} className="mt-4">
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header with Navigation */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-amber-500 p-2 rounded-lg">
            <Pickaxe size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">
              Gold Sector <span className="text-amber-500">Analyst</span>
            </h1>
            <p className="text-sm text-slate-400">Track major gold miners quarterly performance</p>
          </div>
        </div>
        <Navigation />
      </div>

      {/* Dashboard View */}
      {view === 'dashboard' && (
        <div className="space-y-8">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="Avg Sector AISC"
              value={`$${stats?.avg_aisc || 0}`}
              subtext="Per Ounce (Weighted)"
              icon={TrendingDown}
              colorClass="bg-blue-600"
            />
            <StatCard
              title="Total Production"
              value={`${stats?.total_production?.toFixed(1) || 0} Moz`}
              subtext="Current Quarter"
              icon={Database}
              colorClass="bg-amber-500"
            />
            <StatCard
              title="Avg Dividend Yield"
              value={`${stats?.avg_yield || 0}%`}
              subtext="Sector Average"
              icon={DollarSign}
              colorClass="bg-emerald-600"
            />
            <StatCard
              title="Safe Haven Exposure"
              value={`${stats?.tier1_exposure || 0}%`}
              subtext="Assets in Tier 1 Jurisdictions"
              icon={Shield}
              colorClass="bg-indigo-600"
            />
          </div>

          {/* Efficiency Frontier & Rankings */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <Card className="h-[500px] border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100">Efficiency Frontier</CardTitle>
                  <p className="text-sm text-slate-400">
                    Production Volume vs. All-In Sustaining Costs (Latest Quarter)
                  </p>
                </CardHeader>
                <CardContent className="h-[400px]">
                  {latestData.length > 0 ? (
                    <EfficiencyScatter data={latestData} />
                  ) : (
                    <div className="flex items-center justify-center h-full text-slate-500">
                      {loading ? 'Loading...' : 'No data available'}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Cost Leaders Sidebar */}
            <Card className="h-[500px] border-slate-700 overflow-hidden">
              <CardHeader>
                <CardTitle className="text-slate-100">Cost Leaders</CardTitle>
              </CardHeader>
              <CardContent className="overflow-y-auto h-[400px] pr-2 space-y-3">
                {[...latestData].sort((a, b) => a.aisc - b.aisc).map((miner, i) => (
                  <div
                    key={miner.ticker}
                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700"
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-700 text-xs font-bold text-slate-300">
                        {i + 1}
                      </span>
                      <div>
                        <p className="font-bold text-sm text-slate-200">{miner.ticker}</p>
                        <p className="text-xs text-slate-500">{miner.company}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-mono font-bold text-sm ${
                        miner.aisc < 1200 ? 'text-emerald-400' : 'text-slate-300'
                      }`}>
                        ${miner.aisc}
                      </p>
                      <p className="text-xs text-slate-500">AISC/oz</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Financial Health Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card className="border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100">Financial Health (Rev vs FCF)</CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                <Bar
                  data={{
                    labels: latestData.map(d => d.ticker),
                    datasets: [
                      {
                        label: 'Revenue ($B)',
                        data: latestData.map(d => d.revenue),
                        backgroundColor: '#93c5fd'
                      },
                      {
                        label: 'FCF ($B)',
                        data: latestData.map(d => d.fcf),
                        backgroundColor: '#10b981'
                      }
                    ]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: {
                      y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                      x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                  }}
                />
              </CardContent>
            </Card>

            <Card className="border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-100">Jurisdictional Risk</CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                <Bar
                  data={{
                    labels: latestData.map(d => d.ticker),
                    datasets: [
                      {
                        label: 'Tier 1 (Safe)',
                        data: latestData.map(d => d.tier1),
                        backgroundColor: '#10b981'
                      },
                      {
                        label: 'Tier 2 (Mod)',
                        data: latestData.map(d => d.tier2),
                        backgroundColor: '#f59e0b'
                      },
                      {
                        label: 'Tier 3 (High)',
                        data: latestData.map(d => d.tier3),
                        backgroundColor: '#ef4444'
                      }
                    ]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#94a3b8' } } },
                    scales: {
                      x: { stacked: true, ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                      y: { stacked: true, ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    }
                  }}
                />
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Scores View */}
      {view === 'scores' && (
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-100">
              Sovereignty <span className="text-amber-500">Scores</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto mt-2">
              Proprietary ranking based on jurisdictional safety (35%), cost efficiency (25%),
              FCF yield (20%), and production trends (20%)
            </p>
          </div>

          {/* Methodology Card */}
          <Card className="border-slate-700 bg-slate-800/50">
            <CardContent className="py-4">
              <div className="flex items-center gap-6 justify-center flex-wrap">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="text-sm text-slate-400">Jurisdiction Safety (35%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span className="text-sm text-slate-400">AISC Efficiency (25%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500" />
                  <span className="text-sm text-slate-400">FCF Yield (20%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <span className="text-sm text-slate-400">Production Trend (20%)</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Leaderboard */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {sovereigntyScores.map((score, idx) => (
              <LeaderboardCard key={score.ticker} score={score} rank={idx + 1} />
            ))}
          </div>

          {/* Badge Legend */}
          <Card className="border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-100 text-lg">Badge Legend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-amber-500 text-amber-950">
                    Sovereignty Champion
                  </span>
                  <p className="text-xs text-slate-500 mt-2">Score 80+</p>
                </div>
                <div className="text-center">
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-emerald-500 text-emerald-950">
                    Strong Operator
                  </span>
                  <p className="text-xs text-slate-500 mt-2">Score 65-79</p>
                </div>
                <div className="text-center">
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-blue-500 text-blue-950">
                    Steady Performer
                  </span>
                  <p className="text-xs text-slate-500 mt-2">Score 50-64</p>
                </div>
                <div className="text-center">
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-orange-500 text-orange-950">
                    High Risk/Reward
                  </span>
                  <p className="text-xs text-slate-500 mt-2">Score 35-49</p>
                </div>
                <div className="text-center">
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-red-500 text-red-950">
                    Speculative
                  </span>
                  <p className="text-xs text-slate-500 mt-2">Score 0-34</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Trends View */}
      {view === 'trends' && (
        <div className="space-y-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-100">Historical Performance</h2>
            <p className="text-slate-400">Tracking metrics quarter-over-quarter (2023-2025)</p>
          </div>

          <div className="grid grid-cols-1 gap-8">
            <Card className="border-slate-700">
              <CardContent className="pt-6">
                <TrendLineChart
                  historicalData={rawData}
                  metric="aisc"
                  title="AISC Cost Inflation Trends"
                  yAxisTitle="AISC ($/oz)"
                />
              </CardContent>
            </Card>

            <Card className="border-slate-700">
              <CardContent className="pt-6">
                <TrendLineChart
                  historicalData={rawData}
                  metric="production"
                  title="Production Stability (Moz)"
                  yAxisTitle="Million Ounces"
                />
              </CardContent>
            </Card>

            <Card className="border-slate-700">
              <CardContent className="pt-6">
                <TrendLineChart
                  historicalData={rawData}
                  metric="market_cap"
                  title="Market Cap Evolution"
                  yAxisTitle="Billions USD"
                />
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}

export default GoldTracker
