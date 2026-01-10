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
  TrendingDown
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

type ViewType = 'dashboard' | 'trends'

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
