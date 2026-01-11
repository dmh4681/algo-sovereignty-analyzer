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
  ArcElement,
  RadialLinearScale,
  Filler
} from 'chart.js'
import { Line, Bar, Bubble, Radar, Doughnut } from 'react-chartjs-2'
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
  Calculator,
  AlertTriangle,
  Coins,
  GitCompare,
  Check,
  X,
  Briefcase,
  Newspaper,
  PieChart,
  Minus,
  Plus
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  getSilverMetrics,
  getSilverSectorStats,
  type MinerMetric,
  type SectorStats
} from '@/lib/api'
import NewsCurator from './NewsCurator'

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
  ArcElement,
  RadialLinearScale,
  Filler
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
      badgeColor = 'bg-slate-400 text-slate-950'
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

// --- Silver Price Sensitivity Calculation ---

const CURRENT_SILVER_PRICE = 79 // Current silver price per oz
const MIN_SILVER_PRICE = 15
const MAX_SILVER_PRICE = 500

interface MinerSensitivity {
  ticker: string
  company: string
  aisc: number
  production: number // Quarterly Moz
  currentMargin: number // $ per oz at current price
  projectedMargin: number // $ per oz at slider price
  marginChange: number // % change in margin
  breakEvenPrice: number // Silver price where margin = 0 (equals AISC)
  marginOfSafety: number // % silver can drop before unprofitable
  quarterlyProfit: number // Projected profit in $M at slider price
  profitChange: number // % change in quarterly profit
}

function calculateSensitivity(
  latestData: MinerMetric[],
  silverPrice: number
): MinerSensitivity[] {
  return latestData.map(miner => {
    const currentMargin = CURRENT_SILVER_PRICE - miner.aisc
    const projectedMargin = silverPrice - miner.aisc
    const marginChange = currentMargin > 0
      ? ((projectedMargin - currentMargin) / currentMargin) * 100
      : projectedMargin > 0 ? 100 : 0

    const breakEvenPrice = miner.aisc
    const marginOfSafety = ((silverPrice - miner.aisc) / silverPrice) * 100

    // Quarterly profit = margin * production (in Moz) * 1,000,000 / 1,000,000 = margin * production in $M
    const quarterlyProfit = projectedMargin * miner.production
    const currentProfit = currentMargin * miner.production
    const profitChange = currentProfit > 0
      ? ((quarterlyProfit - currentProfit) / currentProfit) * 100
      : quarterlyProfit > 0 ? 100 : 0

    return {
      ticker: miner.ticker,
      company: miner.company,
      aisc: miner.aisc,
      production: miner.production,
      currentMargin,
      projectedMargin,
      marginChange,
      breakEvenPrice,
      marginOfSafety,
      quarterlyProfit,
      profitChange
    }
  }).sort((a, b) => b.marginOfSafety - a.marginOfSafety)
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
    if (rank === 1) return <Crown className="text-slate-300" size={24} />
    if (rank === 2) return <Award className="text-slate-400" size={22} />
    if (rank === 3) return <Award className="text-slate-500" size={20} />
    return <span className="text-slate-500 font-bold text-lg">#{rank}</span>
  }

  const getScoreColor = () => {
    if (score.totalScore >= 80) return 'text-slate-300'
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
                color="bg-slate-400"
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
                <p className="text-xs text-slate-500">Prod</p>
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

// Distinct colors for each silver miner - easily distinguishable
const MINER_COLORS: Record<string, string> = {
  'PAAS': '#94a3b8',  // Slate - Pan American Silver
  'HL': '#f97316',    // Orange - Hecla Mining
  'AG': '#22c55e',    // Green - First Majestic Silver
  'EXK': '#06b6d4',   // Cyan - Endeavour Silver
  'CDE': '#3b82f6',   // Blue - Coeur Mining
  'MAG': '#8b5cf6',   // Purple - MAG Silver
  'ASM': '#ec4899',   // Pink - Avino Silver & Gold
  'SILV': '#eab308',  // Yellow - SilverCrest Metals
  'FSM': '#14b8a6',   // Teal - Fortuna Silver Mines
  'SSRM': '#ef4444',  // Red - SSR Mining
}

function EfficiencyScatter({ data }: EfficiencyScatterProps) {
  const chartData = {
    datasets: data.map(d => ({
      label: d.ticker,
      data: [{ x: d.production, y: d.aisc, r: Math.sqrt(d.market_cap) * 5, ticker: d.ticker, company: d.company }],
      backgroundColor: MINER_COLORS[d.ticker] || '#94a3b8',
      borderColor: MINER_COLORS[d.ticker] || '#94a3b8',
      borderWidth: 2,
    }))
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'right' as const, labels: { color: '#94a3b8' } },
      tooltip: {
        callbacks: {
          title: (ctx: unknown) => {
            const items = ctx as Array<{ dataset: { label: string } }>
            if (items.length > 0) {
              const ticker = items[0].dataset.label
              const miner = data.find(d => d.ticker === ticker)
              return miner ? `${ticker} - ${miner.company}` : ticker
            }
            return ''
          },
          label: (ctx: unknown) => {
            const item = ctx as { raw: { x: number; y: number }; dataset: { label: string } }
            return [
              `Production: ${item.raw.x.toFixed(2)} Moz/Qtr`,
              `AISC: $${item.raw.y}/oz`
            ]
          }
        }
      }
    },
    scales: {
      y: {
        title: { display: true, text: 'AISC ($/oz) - Lower is Better', color: '#94a3b8' },
        min: 8,
        max: 28,
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

  const datasets = companies.map((ticker) => {
    const companyData = sortedHistory.filter(d => d.ticker === ticker)
    const dataPoints = periods.map(p => {
      const entry = companyData.find(d => d.period === p)
      return entry ? (entry[metric] as number) : null
    })

    const color = MINER_COLORS[ticker] || '#94a3b8'

    return {
      label: ticker,
      data: dataPoints,
      borderColor: color,
      backgroundColor: color,
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

type ViewType = 'dashboard' | 'scores' | 'calculator' | 'compare' | 'portfolio' | 'news' | 'trends'

export function SilverTracker() {
  const [view, setView] = useState<ViewType>('dashboard')
  const [rawData, setRawData] = useState<MinerMetric[]>([])
  const [stats, setStats] = useState<SectorStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [silverPrice, setSilverPrice] = useState(CURRENT_SILVER_PRICE)
  const [selectedMiners, setSelectedMiners] = useState<string[]>([])
  const [portfolioAllocations, setPortfolioAllocations] = useState<Record<string, number>>({})

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [metricsRes, statsRes] = await Promise.all([
          getSilverMetrics(150),
          getSilverSectorStats()
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

  // Price Sensitivity Analysis
  const sensitivityData = useMemo(() => {
    return calculateSensitivity(latestData, silverPrice)
  }, [latestData, silverPrice])

  // Toggle miner selection for comparison
  const toggleMinerSelection = (ticker: string) => {
    setSelectedMiners(prev => {
      if (prev.includes(ticker)) {
        return prev.filter(t => t !== ticker)
      }
      if (prev.length >= 3) {
        return [...prev.slice(1), ticker] // Replace oldest selection
      }
      return [...prev, ticker]
    })
  }

  // Get comparison data for selected miners
  const comparisonData = useMemo(() => {
    return latestData.filter(m => selectedMiners.includes(m.ticker))
  }, [latestData, selectedMiners])

  // Get sovereignty scores for selected miners
  const comparisonScores = useMemo(() => {
    return sovereigntyScores.filter(s => selectedMiners.includes(s.ticker))
  }, [sovereigntyScores, selectedMiners])

  // Portfolio allocation helpers
  const updateAllocation = (ticker: string, value: number) => {
    setPortfolioAllocations(prev => ({
      ...prev,
      [ticker]: Math.max(0, Math.min(100, value))
    }))
  }

  const totalAllocation = useMemo(() => {
    return Object.values(portfolioAllocations).reduce((sum, val) => sum + val, 0)
  }, [portfolioAllocations])

  const normalizedAllocations = useMemo(() => {
    if (totalAllocation === 0) return {}
    const normalized: Record<string, number> = {}
    for (const [ticker, value] of Object.entries(portfolioAllocations)) {
      normalized[ticker] = (value / totalAllocation) * 100
    }
    return normalized
  }, [portfolioAllocations, totalAllocation])

  // Blended portfolio metrics
  const portfolioMetrics = useMemo(() => {
    const allocatedMiners = latestData.filter(m => (portfolioAllocations[m.ticker] || 0) > 0)
    if (allocatedMiners.length === 0 || totalAllocation === 0) return null

    let blendedAisc = 0
    let blendedTier1 = 0
    let blendedDividend = 0
    let blendedFcfYield = 0
    let blendedSovereigntyScore = 0

    allocatedMiners.forEach(miner => {
      const weight = (portfolioAllocations[miner.ticker] || 0) / totalAllocation
      const score = sovereigntyScores.find(s => s.ticker === miner.ticker)

      blendedAisc += miner.aisc * weight
      blendedTier1 += miner.tier1 * weight
      blendedDividend += miner.dividend_yield * weight
      blendedFcfYield += (miner.fcf / miner.market_cap) * 100 * weight
      blendedSovereigntyScore += (score?.totalScore || 50) * weight
    })

    const blendedMargin = CURRENT_SILVER_PRICE - blendedAisc
    const blendedMarginOfSafety = ((CURRENT_SILVER_PRICE - blendedAisc) / CURRENT_SILVER_PRICE) * 100

    return {
      aisc: Math.round(blendedAisc * 100) / 100,
      tier1: Math.round(blendedTier1),
      dividend: Math.round(blendedDividend * 100) / 100,
      fcfYield: Math.round(blendedFcfYield * 100) / 100,
      sovereigntyScore: Math.round(blendedSovereigntyScore),
      margin: Math.round(blendedMargin * 100) / 100,
      marginOfSafety: Math.round(blendedMarginOfSafety),
      minerCount: allocatedMiners.length
    }
  }, [latestData, portfolioAllocations, totalAllocation, sovereigntyScores])

  // Navigation
  const Navigation = () => (
    <nav className="flex items-center space-x-2 bg-slate-800 p-1 rounded-lg">
      <button
        onClick={() => setView('dashboard')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'dashboard'
            ? 'bg-slate-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <LayoutDashboard size={16} /> Dashboard
      </button>
      <button
        onClick={() => setView('scores')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'scores'
            ? 'bg-slate-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <Target size={16} /> Scores
      </button>
      <button
        onClick={() => setView('calculator')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'calculator'
            ? 'bg-slate-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <Calculator size={16} /> Calculator
      </button>
      <button
        onClick={() => setView('compare')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'compare'
            ? 'bg-slate-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <GitCompare size={16} /> Compare
        {selectedMiners.length > 0 && (
          <span className="bg-slate-600 px-1.5 py-0.5 rounded-full text-xs">
            {selectedMiners.length}
          </span>
        )}
      </button>
      <button
        onClick={() => setView('portfolio')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'portfolio'
            ? 'bg-slate-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <Briefcase size={16} /> Portfolio
      </button>
      <button
        onClick={() => setView('news')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'news'
            ? 'bg-slate-500 text-white shadow-sm'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <Newspaper size={16} /> News
      </button>
      <button
        onClick={() => setView('trends')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          view === 'trends'
            ? 'bg-slate-500 text-white shadow-sm'
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
          <div className="bg-slate-500 p-2 rounded-lg">
            <Pickaxe size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">
              Silver Sector <span className="text-slate-400">Analyst</span>
            </h1>
            <p className="text-sm text-slate-400">Track major silver miners quarterly performance</p>
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
              value={`$${stats?.avg_aisc?.toFixed(2) || 0}`}
              subtext="Per Ounce (Weighted)"
              icon={TrendingDown}
              colorClass="bg-blue-600"
            />
            <StatCard
              title="Total Production"
              value={`${stats?.total_production?.toFixed(1) || 0} Moz`}
              subtext="Current Quarter"
              icon={Database}
              colorClass="bg-slate-500"
            />
            <StatCard
              title="Avg Dividend Yield"
              value={`${stats?.avg_yield?.toFixed(2) || 0}%`}
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
                        miner.aisc < 14 ? 'text-emerald-400' : 'text-slate-300'
                      }`}>
                        ${miner.aisc.toFixed(2)}
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
              Sovereignty <span className="text-slate-400">Scores</span>
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
                  <div className="w-3 h-3 rounded-full bg-slate-400" />
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
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-slate-400 text-slate-950">
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

      {/* Calculator View */}
      {view === 'calculator' && (
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-100">
              Silver Price <span className="text-slate-400">Calculator</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto mt-2">
              Explore how silver price changes affect miner profitability and margins
            </p>
          </div>

          {/* Silver Price Slider */}
          <Card className="border-slate-700 bg-gradient-to-br from-slate-700/20 to-slate-900">
            <CardContent className="py-6">
              <div className="flex flex-col items-center space-y-4">
                <div className="flex items-center gap-3">
                  <Coins className="text-slate-400" size={28} />
                  <span className="text-4xl font-bold text-slate-300">
                    ${silverPrice.toLocaleString()}
                  </span>
                  <span className="text-slate-400">/oz</span>
                </div>

                <div className="w-full max-w-2xl px-4">
                  <input
                    type="range"
                    min={MIN_SILVER_PRICE}
                    max={MAX_SILVER_PRICE}
                    step={1}
                    value={silverPrice}
                    onChange={(e) => setSilverPrice(Number(e.target.value))}
                    className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-slate-400"
                  />
                  <div className="flex justify-between text-xs text-slate-500 mt-2">
                    <span>${MIN_SILVER_PRICE}</span>
                    <span className="text-slate-400 font-medium">Current: ${CURRENT_SILVER_PRICE}</span>
                    <span>${MAX_SILVER_PRICE}</span>
                  </div>
                </div>

                {/* Quick Presets */}
                <div className="flex gap-2 flex-wrap justify-center mt-4">
                  {[50, 79, 100, 150, 250, 500].map(price => (
                    <button
                      key={price}
                      onClick={() => setSilverPrice(price)}
                      className={`px-3 py-1 text-sm rounded-full transition-colors ${
                        silverPrice === price
                          ? 'bg-slate-500 text-white'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      ${price}
                    </button>
                  ))}
                </div>

                {/* Price Change Indicator */}
                <div className={`flex items-center gap-2 text-sm ${
                  silverPrice > CURRENT_SILVER_PRICE ? 'text-emerald-400' :
                  silverPrice < CURRENT_SILVER_PRICE ? 'text-red-400' : 'text-slate-400'
                }`}>
                  {silverPrice !== CURRENT_SILVER_PRICE && (
                    <>
                      {silverPrice > CURRENT_SILVER_PRICE ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                      <span>
                        {silverPrice > CURRENT_SILVER_PRICE ? '+' : ''}
                        {(((silverPrice - CURRENT_SILVER_PRICE) / CURRENT_SILVER_PRICE) * 100).toFixed(1)}% from current
                      </span>
                    </>
                  )}
                  {silverPrice === CURRENT_SILVER_PRICE && <span>Current market price</span>}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Sector Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-slate-700">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-400">Avg Margin</p>
                    <h3 className={`text-2xl font-bold mt-1 ${
                      sensitivityData.length > 0 && sensitivityData.reduce((s, d) => s + d.projectedMargin, 0) / sensitivityData.length > 0
                        ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      ${sensitivityData.length > 0
                        ? (sensitivityData.reduce((s, d) => s + d.projectedMargin, 0) / sensitivityData.length).toFixed(2)
                        : 0}/oz
                    </h3>
                  </div>
                  <div className="p-3 rounded-lg bg-emerald-600">
                    <DollarSign size={20} className="text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-700">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-400">Profitable Miners</p>
                    <h3 className="text-2xl font-bold text-slate-100 mt-1">
                      {sensitivityData.filter(d => d.projectedMargin > 0).length} / {sensitivityData.length}
                    </h3>
                  </div>
                  <div className="p-3 rounded-lg bg-blue-600">
                    <Pickaxe size={20} className="text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-700">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-400">Total Sector Profit</p>
                    <h3 className={`text-2xl font-bold mt-1 ${
                      sensitivityData.reduce((s, d) => s + d.quarterlyProfit, 0) > 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      ${sensitivityData.length > 0
                        ? sensitivityData.reduce((s, d) => s + d.quarterlyProfit, 0).toFixed(1)
                        : 0}M
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">Quarterly estimate</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-500">
                    <Coins size={20} className="text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-700">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-400">At Risk</p>
                    <h3 className="text-2xl font-bold text-orange-400 mt-1">
                      {sensitivityData.filter(d => d.marginOfSafety < 20).length}
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">Margin of safety &lt;20%</p>
                  </div>
                  <div className="p-3 rounded-lg bg-orange-600">
                    <AlertTriangle size={20} className="text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sensitivity Table */}
          <Card className="border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-100">Miner Profitability Analysis</CardTitle>
              <p className="text-sm text-slate-400">
                Sorted by margin of safety (how far silver can drop before unprofitable)
              </p>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-2 text-slate-400 font-medium">Miner</th>
                      <th className="text-right py-3 px-2 text-slate-400 font-medium">AISC</th>
                      <th className="text-right py-3 px-2 text-slate-400 font-medium">Margin/oz</th>
                      <th className="text-right py-3 px-2 text-slate-400 font-medium">Margin</th>
                      <th className="text-right py-3 px-2 text-slate-400 font-medium">Safety</th>
                      <th className="text-right py-3 px-2 text-slate-400 font-medium">Qtr Profit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sensitivityData.map((miner) => (
                      <tr key={miner.ticker} className="border-b border-slate-800 hover:bg-slate-800/50">
                        <td className="py-3 px-2">
                          <div>
                            <p className="font-bold text-slate-200">{miner.ticker}</p>
                            <p className="text-xs text-slate-500">{miner.company}</p>
                          </div>
                        </td>
                        <td className="text-right py-3 px-2 font-mono text-slate-300">
                          ${miner.aisc.toFixed(2)}
                        </td>
                        <td className={`text-right py-3 px-2 font-mono font-bold ${
                          miner.projectedMargin > 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          ${miner.projectedMargin.toFixed(2)}
                        </td>
                        <td className={`text-right py-3 px-2 font-mono ${
                          miner.marginChange > 0 ? 'text-emerald-400' :
                          miner.marginChange < 0 ? 'text-red-400' : 'text-slate-400'
                        }`}>
                          {miner.marginChange > 0 ? '+' : ''}{miner.marginChange.toFixed(1)}%
                        </td>
                        <td className="text-right py-3 px-2">
                          <div className="flex items-center justify-end gap-2">
                            <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full transition-all ${
                                  miner.marginOfSafety >= 60 ? 'bg-emerald-500' :
                                  miner.marginOfSafety >= 40 ? 'bg-blue-500' :
                                  miner.marginOfSafety >= 20 ? 'bg-amber-500' :
                                  miner.marginOfSafety > 0 ? 'bg-orange-500' : 'bg-red-500'
                                }`}
                                style={{ width: `${Math.max(0, Math.min(100, miner.marginOfSafety))}%` }}
                              />
                            </div>
                            <span className={`font-mono text-xs ${
                              miner.marginOfSafety >= 40 ? 'text-emerald-400' :
                              miner.marginOfSafety >= 20 ? 'text-amber-400' :
                              miner.marginOfSafety > 0 ? 'text-orange-400' : 'text-red-400'
                            }`}>
                              {miner.marginOfSafety.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className={`text-right py-3 px-2 font-mono ${
                          miner.quarterlyProfit > 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          ${miner.quarterlyProfit.toFixed(1)}M
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Margin Bar Chart */}
          <Card className="border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-100">Profit Margins by Miner</CardTitle>
              <p className="text-sm text-slate-400">
                $ per ounce profit at ${silverPrice}/oz silver
              </p>
            </CardHeader>
            <CardContent className="h-80">
              <Bar
                data={{
                  labels: sensitivityData.map(d => d.ticker),
                  datasets: [
                    {
                      label: 'Margin ($/oz)',
                      data: sensitivityData.map(d => d.projectedMargin),
                      backgroundColor: sensitivityData.map(d =>
                        d.projectedMargin > 20 ? '#10b981' :
                        d.projectedMargin > 10 ? '#3b82f6' :
                        d.projectedMargin > 0 ? '#f59e0b' : '#ef4444'
                      ),
                    }
                  ]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false },
                    tooltip: {
                      callbacks: {
                        label: (ctx) => `Margin: $${(ctx.raw as number)?.toFixed(2)}/oz`
                      }
                    }
                  },
                  scales: {
                    y: {
                      title: { display: true, text: 'Margin ($/oz)', color: '#94a3b8' },
                      ticks: { color: '#94a3b8' },
                      grid: { color: '#334155' }
                    },
                    x: {
                      ticks: { color: '#94a3b8' },
                      grid: { color: '#334155' }
                    }
                  }
                }}
              />
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card className="border-slate-700 bg-slate-800/50">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="text-slate-400 flex-shrink-0 mt-0.5" size={20} />
                <div className="text-sm text-slate-400">
                  <p className="font-medium text-slate-300 mb-1">About This Calculator</p>
                  <p>
                    Margin of Safety shows the percentage silver prices can fall before a miner becomes unprofitable.
                    Quarterly profit estimates are based on production x margin. AISC (All-In Sustaining Cost) includes
                    mining, processing, G&A, and sustaining capital expenditures. Silver AISC is typically $12-22/oz.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Compare View */}
      {view === 'compare' && (
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-100">
              Peer <span className="text-slate-400">Comparison</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto mt-2">
              Select up to 3 miners to compare side-by-side across key metrics
            </p>
          </div>

          {/* Miner Selection */}
          <Card className="border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-100">Select Miners to Compare</CardTitle>
              <p className="text-sm text-slate-400">
                Click to select/deselect. Maximum 3 miners.
              </p>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {latestData.map(miner => {
                  const isSelected = selectedMiners.includes(miner.ticker)
                  return (
                    <button
                      key={miner.ticker}
                      onClick={() => toggleMinerSelection(miner.ticker)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all ${
                        isSelected
                          ? 'bg-slate-500 border-slate-400 text-white'
                          : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-500'
                      }`}
                    >
                      {isSelected ? <Check size={16} /> : <div className="w-4" />}
                      <span className="font-bold">{miner.ticker}</span>
                      <span className="text-xs opacity-75">{miner.company}</span>
                    </button>
                  )
                })}
              </div>
              {selectedMiners.length > 0 && (
                <button
                  onClick={() => setSelectedMiners([])}
                  className="mt-4 text-sm text-slate-400 hover:text-slate-200 flex items-center gap-1"
                >
                  <X size={14} /> Clear selection
                </button>
              )}
            </CardContent>
          </Card>

          {/* Comparison Content */}
          {selectedMiners.length === 0 ? (
            <Card className="border-slate-700 border-dashed">
              <CardContent className="py-16 text-center">
                <GitCompare className="mx-auto text-slate-600 mb-4" size={48} />
                <p className="text-slate-400">Select miners above to start comparing</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Radar Chart */}
              <Card className="border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100">Multi-Dimensional Comparison</CardTitle>
                  <p className="text-sm text-slate-400">
                    Normalized scores across key dimensions (higher is better)
                  </p>
                </CardHeader>
                <CardContent className="h-96">
                  <Radar
                    data={{
                      labels: ['Jurisdiction Safety', 'Cost Efficiency', 'FCF Yield', 'Production Trend', 'Scale'],
                      datasets: comparisonScores.map((score, idx) => {
                        const miner = comparisonData.find(m => m.ticker === score.ticker)
                        const colors = [
                          { bg: 'rgba(148, 163, 184, 0.2)', border: '#94a3b8' },
                          { bg: 'rgba(16, 185, 129, 0.2)', border: '#10b981' },
                          { bg: 'rgba(59, 130, 246, 0.2)', border: '#3b82f6' },
                        ]
                        const color = colors[idx % colors.length]
                        // Normalize scale (production) to 0-100
                        const maxProd = Math.max(...latestData.map(m => m.production))
                        const scaleScore = miner ? (miner.production / maxProd) * 100 : 0

                        return {
                          label: score.ticker,
                          data: [
                            score.jurisdictionScore,
                            score.aiscScore,
                            score.fcfYieldScore,
                            score.productionTrendScore,
                            scaleScore
                          ],
                          backgroundColor: color.bg,
                          borderColor: color.border,
                          borderWidth: 2,
                          pointBackgroundColor: color.border,
                          pointBorderColor: '#fff',
                          pointHoverBackgroundColor: '#fff',
                          pointHoverBorderColor: color.border
                        }
                      })
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                          labels: { color: '#94a3b8' }
                        }
                      },
                      scales: {
                        r: {
                          beginAtZero: true,
                          max: 100,
                          ticks: { color: '#64748b', backdropColor: 'transparent' },
                          grid: { color: '#334155' },
                          pointLabels: { color: '#94a3b8', font: { size: 12 } },
                          angleLines: { color: '#334155' }
                        }
                      }
                    }}
                  />
                </CardContent>
              </Card>

              {/* Side-by-Side Cards */}
              <div className={`grid gap-6 ${
                selectedMiners.length === 1 ? 'grid-cols-1 max-w-xl mx-auto' :
                selectedMiners.length === 2 ? 'grid-cols-1 md:grid-cols-2' :
                'grid-cols-1 md:grid-cols-3'
              }`}>
                {comparisonData.map(miner => {
                  const score = comparisonScores.find(s => s.ticker === miner.ticker)
                  const margin = CURRENT_SILVER_PRICE - miner.aisc
                  const marginOfSafety = ((CURRENT_SILVER_PRICE - miner.aisc) / CURRENT_SILVER_PRICE) * 100

                  return (
                    <Card key={miner.ticker} className="border-slate-700">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-slate-100 text-xl">{miner.ticker}</CardTitle>
                            <p className="text-sm text-slate-500">{miner.company}</p>
                          </div>
                          {score && (
                            <div className="text-right">
                              <p className="text-3xl font-bold text-slate-300">{score.totalScore}</p>
                              <p className="text-xs text-slate-500">Sov. Score</p>
                            </div>
                          )}
                        </div>
                        {score && (
                          <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-bold ${score.badgeColor}`}>
                            {score.badge}
                          </span>
                        )}
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* Key Metrics */}
                        <div className="grid grid-cols-2 gap-3">
                          <div className="bg-slate-800 rounded-lg p-3">
                            <p className="text-xs text-slate-500">AISC</p>
                            <p className="font-mono font-bold text-lg text-slate-200">${miner.aisc.toFixed(2)}</p>
                            <p className="text-xs text-slate-500">/oz</p>
                          </div>
                          <div className="bg-slate-800 rounded-lg p-3">
                            <p className="text-xs text-slate-500">Production</p>
                            <p className="font-mono font-bold text-lg text-slate-200">{miner.production.toFixed(2)}</p>
                            <p className="text-xs text-slate-500">Moz/Qtr</p>
                          </div>
                          <div className="bg-slate-800 rounded-lg p-3">
                            <p className="text-xs text-slate-500">Market Cap</p>
                            <p className="font-mono font-bold text-lg text-slate-200">${miner.market_cap}B</p>
                          </div>
                          <div className="bg-slate-800 rounded-lg p-3">
                            <p className="text-xs text-slate-500">Dividend</p>
                            <p className="font-mono font-bold text-lg text-emerald-400">{miner.dividend_yield}%</p>
                          </div>
                        </div>

                        {/* Margin Analysis */}
                        <div className="bg-slate-800/50 rounded-lg p-3">
                          <p className="text-xs text-slate-500 mb-2">Profit Margin @ $79/oz</p>
                          <div className="flex items-center justify-between">
                            <span className={`font-mono font-bold text-xl ${margin > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              ${margin.toFixed(2)}/oz
                            </span>
                            <span className={`text-sm ${marginOfSafety >= 40 ? 'text-emerald-400' : 'text-amber-400'}`}>
                              {marginOfSafety.toFixed(0)}% safety
                            </span>
                          </div>
                        </div>

                        {/* Jurisdictional Breakdown */}
                        <div className="space-y-2">
                          <p className="text-xs text-slate-500">Jurisdictional Mix</p>
                          <div className="flex h-4 rounded-full overflow-hidden">
                            <div
                              className="bg-emerald-500"
                              style={{ width: `${miner.tier1}%` }}
                              title={`Tier 1: ${miner.tier1}%`}
                            />
                            <div
                              className="bg-amber-500"
                              style={{ width: `${miner.tier2}%` }}
                              title={`Tier 2: ${miner.tier2}%`}
                            />
                            <div
                              className="bg-red-500"
                              style={{ width: `${miner.tier3}%` }}
                              title={`Tier 3: ${miner.tier3}%`}
                            />
                          </div>
                          <div className="flex justify-between text-xs text-slate-500">
                            <span>T1: {miner.tier1}%</span>
                            <span>T2: {miner.tier2}%</span>
                            <span>T3: {miner.tier3}%</span>
                          </div>
                        </div>

                        {/* Financial Health */}
                        <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-700">
                          <div>
                            <p className="text-xs text-slate-500">Revenue</p>
                            <p className="font-mono font-bold text-slate-200">${miner.revenue}B</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500">FCF</p>
                            <p className={`font-mono font-bold ${miner.fcf >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              ${miner.fcf}B
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>

              {/* Comparison Table */}
              <Card className="border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100">Metric Comparison Table</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-3 px-2 text-slate-400 font-medium">Metric</th>
                          {comparisonData.map(m => (
                            <th key={m.ticker} className="text-right py-3 px-2 text-slate-300 font-bold">
                              {m.ticker}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b border-slate-800">
                          <td className="py-3 px-2 text-slate-400">AISC ($/oz)</td>
                          {comparisonData.map(m => {
                            const best = Math.min(...comparisonData.map(x => x.aisc))
                            return (
                              <td key={m.ticker} className={`text-right py-3 px-2 font-mono ${m.aisc === best ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
                                ${m.aisc.toFixed(2)}
                              </td>
                            )
                          })}
                        </tr>
                        <tr className="border-b border-slate-800">
                          <td className="py-3 px-2 text-slate-400">Production (Moz)</td>
                          {comparisonData.map(m => {
                            const best = Math.max(...comparisonData.map(x => x.production))
                            return (
                              <td key={m.ticker} className={`text-right py-3 px-2 font-mono ${m.production === best ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
                                {m.production.toFixed(2)}
                              </td>
                            )
                          })}
                        </tr>
                        <tr className="border-b border-slate-800">
                          <td className="py-3 px-2 text-slate-400">Market Cap ($B)</td>
                          {comparisonData.map(m => (
                            <td key={m.ticker} className="text-right py-3 px-2 font-mono text-slate-300">
                              ${m.market_cap}
                            </td>
                          ))}
                        </tr>
                        <tr className="border-b border-slate-800">
                          <td className="py-3 px-2 text-slate-400">Tier 1 Exposure (%)</td>
                          {comparisonData.map(m => {
                            const best = Math.max(...comparisonData.map(x => x.tier1))
                            return (
                              <td key={m.ticker} className={`text-right py-3 px-2 font-mono ${m.tier1 === best ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
                                {m.tier1}%
                              </td>
                            )
                          })}
                        </tr>
                        <tr className="border-b border-slate-800">
                          <td className="py-3 px-2 text-slate-400">Dividend Yield (%)</td>
                          {comparisonData.map(m => {
                            const best = Math.max(...comparisonData.map(x => x.dividend_yield))
                            return (
                              <td key={m.ticker} className={`text-right py-3 px-2 font-mono ${m.dividend_yield === best ? 'text-emerald-400 font-bold' : 'text-slate-300'}`}>
                                {m.dividend_yield}%
                              </td>
                            )
                          })}
                        </tr>
                        <tr className="border-b border-slate-800">
                          <td className="py-3 px-2 text-slate-400">FCF ($B)</td>
                          {comparisonData.map(m => {
                            const best = Math.max(...comparisonData.map(x => x.fcf))
                            return (
                              <td key={m.ticker} className={`text-right py-3 px-2 font-mono ${m.fcf === best ? 'text-emerald-400 font-bold' : m.fcf < 0 ? 'text-red-400' : 'text-slate-300'}`}>
                                ${m.fcf}
                              </td>
                            )
                          })}
                        </tr>
                        <tr>
                          <td className="py-3 px-2 text-slate-400">Sovereignty Score</td>
                          {comparisonData.map(m => {
                            const score = comparisonScores.find(s => s.ticker === m.ticker)
                            const best = Math.max(...comparisonScores.map(s => s.totalScore))
                            return (
                              <td key={m.ticker} className={`text-right py-3 px-2 font-mono font-bold ${score?.totalScore === best ? 'text-slate-300' : 'text-slate-300'}`}>
                                {score?.totalScore || '-'}
                              </td>
                            )
                          })}
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}

      {/* Portfolio View */}
      {view === 'portfolio' && (
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-100">
              Portfolio <span className="text-slate-400">Builder</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto mt-2">
              Model your ideal silver miner portfolio and see blended metrics
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Allocation Controls */}
            <div className="lg:col-span-2 space-y-4">
              <Card className="border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-100">Set Allocations</CardTitle>
                  <p className="text-sm text-slate-400">
                    Adjust weights for each miner (will be normalized to 100%)
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  {latestData.map(miner => {
                    const allocation = portfolioAllocations[miner.ticker] || 0
                    const normalized = normalizedAllocations[miner.ticker] || 0
                    const score = sovereigntyScores.find(s => s.ticker === miner.ticker)

                    return (
                      <div key={miner.ticker} className="flex items-center gap-4 p-3 bg-slate-800/50 rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <span className="font-bold text-slate-200">{miner.ticker}</span>
                              <span className="text-xs text-slate-500 ml-2">{miner.company}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              {score && (
                                <span className={`text-xs px-2 py-0.5 rounded ${score.badgeColor}`}>
                                  {score.totalScore}
                                </span>
                              )}
                              <span className="text-sm font-mono text-slate-300 w-16 text-right">
                                {normalized.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => updateAllocation(miner.ticker, allocation - 5)}
                              className="p-1 bg-slate-700 rounded hover:bg-slate-600 text-slate-400"
                            >
                              <Minus size={14} />
                            </button>
                            <input
                              type="range"
                              min={0}
                              max={100}
                              value={allocation}
                              onChange={(e) => updateAllocation(miner.ticker, Number(e.target.value))}
                              className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-slate-400"
                            />
                            <button
                              onClick={() => updateAllocation(miner.ticker, allocation + 5)}
                              className="p-1 bg-slate-700 rounded hover:bg-slate-600 text-slate-400"
                            >
                              <Plus size={14} />
                            </button>
                            <input
                              type="number"
                              min={0}
                              max={100}
                              value={allocation}
                              onChange={(e) => updateAllocation(miner.ticker, Number(e.target.value))}
                              className="w-16 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-center text-sm font-mono text-slate-200"
                            />
                          </div>
                        </div>
                      </div>
                    )
                  })}

                  {/* Quick Actions */}
                  <div className="flex gap-2 pt-4 border-t border-slate-700">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const equal: Record<string, number> = {}
                        latestData.forEach(m => { equal[m.ticker] = 10 })
                        setPortfolioAllocations(equal)
                      }}
                    >
                      Equal Weight
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const byScore: Record<string, number> = {}
                        sovereigntyScores.forEach(s => { byScore[s.ticker] = s.totalScore })
                        setPortfolioAllocations(byScore)
                      }}
                    >
                      Score Weighted
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPortfolioAllocations({})}
                    >
                      Clear All
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Portfolio Summary */}
            <div className="space-y-4">
              {/* Pie Chart */}
              <Card className="border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                    <PieChart size={18} /> Allocation
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {totalAllocation > 0 ? (
                    <div className="h-48">
                      <Doughnut
                        data={{
                          labels: Object.keys(normalizedAllocations),
                          datasets: [{
                            data: Object.values(normalizedAllocations),
                            backgroundColor: [
                              '#94a3b8', '#10b981', '#3b82f6', '#8b5cf6', '#ef4444',
                              '#f97316', '#eab308', '#06b6d4', '#14b8a6', '#ec4899'
                            ],
                            borderColor: '#1e293b',
                            borderWidth: 2
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'bottom',
                              labels: { color: '#94a3b8', padding: 8, font: { size: 11 } }
                            }
                          }
                        }}
                      />
                    </div>
                  ) : (
                    <div className="h-48 flex items-center justify-center text-slate-500">
                      <p className="text-center">
                        <PieChart className="mx-auto mb-2 opacity-50" size={32} />
                        Set allocations to see chart
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Blended Metrics */}
              <Card className="border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-slate-100 text-lg">Blended Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  {portfolioMetrics ? (
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-2 bg-slate-800 rounded">
                        <span className="text-slate-400 text-sm">Sovereignty Score</span>
                        <span className="font-bold text-xl text-slate-300">{portfolioMetrics.sovereigntyScore}</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-slate-800 rounded">
                        <span className="text-slate-400 text-sm">Blended AISC</span>
                        <span className="font-mono font-bold text-slate-200">${portfolioMetrics.aisc}/oz</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-slate-800 rounded">
                        <span className="text-slate-400 text-sm">Profit Margin</span>
                        <span className={`font-mono font-bold ${portfolioMetrics.margin > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          ${portfolioMetrics.margin}/oz
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-slate-800 rounded">
                        <span className="text-slate-400 text-sm">Margin of Safety</span>
                        <span className={`font-mono font-bold ${portfolioMetrics.marginOfSafety >= 40 ? 'text-emerald-400' : 'text-amber-400'}`}>
                          {portfolioMetrics.marginOfSafety}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-slate-800 rounded">
                        <span className="text-slate-400 text-sm">Tier 1 Exposure</span>
                        <span className="font-mono font-bold text-emerald-400">{portfolioMetrics.tier1}%</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-slate-800 rounded">
                        <span className="text-slate-400 text-sm">Dividend Yield</span>
                        <span className="font-mono font-bold text-slate-200">{portfolioMetrics.dividend}%</span>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-slate-800 rounded">
                        <span className="text-slate-400 text-sm">FCF Yield</span>
                        <span className="font-mono font-bold text-slate-200">{portfolioMetrics.fcfYield}%</span>
                      </div>
                      <div className="pt-2 border-t border-slate-700 text-center">
                        <span className="text-xs text-slate-500">
                          {portfolioMetrics.minerCount} miner{portfolioMetrics.minerCount > 1 ? 's' : ''} in portfolio
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="py-8 text-center text-slate-500">
                      <Briefcase className="mx-auto mb-2 opacity-50" size={32} />
                      <p>Set allocations to see blended metrics</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Info Card */}
          <Card className="border-slate-700 bg-slate-800/50">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="text-slate-400 flex-shrink-0 mt-0.5" size={20} />
                <div className="text-sm text-slate-400">
                  <p className="font-medium text-slate-300 mb-1">About the Portfolio Builder</p>
                  <p>
                    This tool helps you model a hypothetical silver miner portfolio. Blended metrics are weighted
                    averages based on your allocation percentages. The Sovereignty Score is a proprietary ranking
                    considering jurisdiction safety, cost efficiency, FCF yield, and production trends.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* News View */}
      {view === 'news' && (
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-100">
              Silver Mining <span className="text-slate-400">News</span>
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto mt-2">
              AI-curated precious metals news analyzed through a sovereignty lens
            </p>
          </div>

          {/* NewsCurator Component */}
          <NewsCurator />
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
                  title="AISC Cost Trends"
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

export default SilverTracker
