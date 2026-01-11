'use client'

import { useState, useEffect } from 'react'
import {
  getCBGoldSummary,
  getCBLeaderboard,
  getCBNetPurchases,
  getCBTopBuyers,
  getDeDollarizationScore,
  type CBGoldSummary,
  type CountryRanking,
  type NetPurchase,
  type DeDollarizationScore,
} from '@/lib/api'
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
  ArcElement,
} from 'chart.js'
import { Bar, Doughnut } from 'react-chartjs-2'
import {
  TrendingUp,
  TrendingDown,
  Globe,
  Building2,
  Scale,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  Landmark,
} from 'lucide-react'
import { DataDisclaimer } from '@/components/DataDisclaimer'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

type ViewType = 'overview' | 'leaderboard' | 'purchases' | 'buyers'

export function CentralBankTracker() {
  const [view, setView] = useState<ViewType>('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [summary, setSummary] = useState<CBGoldSummary | null>(null)
  const [leaderboard, setLeaderboard] = useState<CountryRanking[]>([])
  const [netPurchases, setNetPurchases] = useState<NetPurchase[]>([])
  const [purchaseSummary, setPurchaseSummary] = useState<{
    total_tonnes: number
    average_per_year: number
    recent_5yr_avg: number
    peak_year: string | null
    peak_tonnes: number
  } | null>(null)
  const [topBuyers, setTopBuyers] = useState<CountryRanking[]>([])
  const [dedollarization, setDedollarization] = useState<DeDollarizationScore | null>(null)

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)

      try {
        // Fetch summary and de-dollarization for all views
        const [summaryRes, dedollarRes] = await Promise.all([
          getCBGoldSummary(),
          getDeDollarizationScore(),
        ])
        setSummary(summaryRes.stats)
        setDedollarization(dedollarRes.score)

        if (view === 'leaderboard' || view === 'overview') {
          const leaderRes = await getCBLeaderboard(20)
          setLeaderboard(leaderRes.rankings)
        }

        if (view === 'purchases' || view === 'overview') {
          const purchasesRes = await getCBNetPurchases()
          setNetPurchases(purchasesRes.purchases)
          setPurchaseSummary(purchasesRes.summary)
        }

        if (view === 'buyers') {
          const buyersRes = await getCBTopBuyers(10)
          setTopBuyers(buyersRes.buyers)
        }
      } catch (err) {
        console.error('Error fetching CB gold data:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [view])

  // De-dollarization Gauge Component
  const DeDollarizationGauge = () => {
    if (!dedollarization) return null

    const score = dedollarization.score
    const circumference = 2 * Math.PI * 40
    const strokeDashoffset = circumference - (score / 100) * circumference * 0.75

    let color = 'text-red-400'
    if (score >= 70) color = 'text-green-400'
    else if (score >= 50) color = 'text-amber-400'
    else if (score >= 30) color = 'text-orange-400'

    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Scale className="h-5 w-5 text-purple-400" />
          De-Dollarization Score
        </h3>

        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32">
            <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
              <circle
                className="text-slate-700"
                strokeWidth="8"
                stroke="currentColor"
                fill="transparent"
                r="40"
                cx="50"
                cy="50"
                strokeDasharray={circumference * 0.75}
                strokeLinecap="round"
              />
              <circle
                className={color}
                strokeWidth="8"
                stroke="currentColor"
                fill="transparent"
                r="40"
                cx="50"
                cy="50"
                strokeDasharray={circumference * 0.75}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-3xl font-bold ${color}`}>{score.toFixed(0)}</span>
            </div>
          </div>

          <div className="flex-1">
            <p className="text-sm text-slate-300 mb-3">{dedollarization.interpretation}</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-slate-700/50 rounded px-2 py-1">
                <span className="text-slate-400">Buying Streak:</span>
                <span className="text-amber-400 ml-1 font-medium">
                  {dedollarization.components.consecutive_buying_years} yrs
                </span>
              </div>
              <div className="bg-slate-700/50 rounded px-2 py-1">
                <span className="text-slate-400">Avg Purchases:</span>
                <span className="text-amber-400 ml-1 font-medium">
                  {dedollarization.components.avg_recent_purchases}t/yr
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Overview render
  const renderOverview = () => {
    if (!summary) return null

    return (
      <div className="space-y-6">
        {/* Key Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
              <Globe className="h-4 w-4" />
              <span>Global CB Holdings</span>
            </div>
            <p className="text-3xl font-mono font-bold text-amber-400">
              {summary.total_holdings_tonnes.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500 mt-1">tonnes of gold</p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
              <TrendingUp className="h-4 w-4" />
              <span>2024 Net Purchases</span>
            </div>
            <p className="text-3xl font-mono font-bold text-green-400">
              +{summary.latest_year_purchases}
            </p>
            <p className="text-xs text-slate-500 mt-1">tonnes (YoY: {summary.yoy_change_tonnes > 0 ? '+' : ''}{summary.yoy_change_tonnes}t)</p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
              <Building2 className="h-4 w-4" />
              <span>Buying Streak</span>
            </div>
            <p className="text-3xl font-mono font-bold text-blue-400">
              {summary.consecutive_buying_years}
            </p>
            <p className="text-xs text-slate-500 mt-1">consecutive years</p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
              <Landmark className="h-4 w-4" />
              <span>Top Holder</span>
            </div>
            <p className="text-xl font-bold text-slate-200">{summary.top_holder}</p>
            <p className="text-xs text-slate-500 mt-1">{summary.top_holder_tonnes.toLocaleString()} tonnes</p>
          </div>
        </div>

        {/* De-dollarization Gauge */}
        <DeDollarizationGauge />

        {/* Net Purchases Chart */}
        {netPurchases.length > 0 && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h3 className="text-slate-200 font-medium mb-4">Global Central Bank Net Gold Purchases</h3>
            <div className="h-[250px]">
              <Bar
                data={{
                  labels: netPurchases.map(p => p.year),
                  datasets: [
                    {
                      label: 'Net Purchases (tonnes)',
                      data: netPurchases.map(p => p.tonnes),
                      backgroundColor: netPurchases.map(p =>
                        p.tonnes >= 1000 ? 'rgba(34, 197, 94, 0.8)' :
                        p.tonnes >= 500 ? 'rgba(251, 191, 36, 0.8)' :
                        'rgba(100, 116, 139, 0.8)'
                      ),
                      borderColor: netPurchases.map(p =>
                        p.tonnes >= 1000 ? 'rgb(34, 197, 94)' :
                        p.tonnes >= 500 ? 'rgb(251, 191, 36)' :
                        'rgb(100, 116, 139)'
                      ),
                      borderWidth: 1,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false },
                    tooltip: {
                      backgroundColor: 'rgba(15, 23, 42, 0.9)',
                      callbacks: {
                        label: (ctx) => `${ctx.raw} tonnes`,
                      },
                    },
                  },
                  scales: {
                    x: {
                      grid: { color: 'rgba(51, 65, 85, 0.5)' },
                      ticks: { color: '#64748b' },
                    },
                    y: {
                      grid: { color: 'rgba(51, 65, 85, 0.5)' },
                      ticks: {
                        color: '#64748b',
                        callback: (value: string | number) => `${value}t`,
                      },
                    },
                  },
                }}
              />
            </div>
            <p className="text-center text-xs text-slate-500 mt-3">
              2022 was a record year with 1,082 tonnes of net purchases
            </p>
          </div>
        )}

        {/* Top 10 Holders Table */}
        {leaderboard.length > 0 && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-slate-200 font-medium">Top 10 Gold Holders</h3>
              <button
                onClick={() => setView('leaderboard')}
                className="text-sm text-amber-400 hover:text-amber-300"
              >
                View Full Leaderboard
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-700">
                    <th className="text-left py-2">#</th>
                    <th className="text-left py-2">Country</th>
                    <th className="text-right py-2">Holdings</th>
                    <th className="text-right py-2">% Reserves</th>
                    <th className="text-right py-2">12m Change</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.slice(0, 10).map((country) => (
                    <tr key={country.country_code} className="border-b border-slate-700/50">
                      <td className="py-2 text-slate-500">{country.rank}</td>
                      <td className="py-2">
                        <span className="mr-2">{country.flag}</span>
                        <span className="text-slate-200">{country.country_name}</span>
                      </td>
                      <td className="py-2 text-right font-mono text-amber-400">
                        {country.tonnes.toLocaleString()}t
                      </td>
                      <td className="py-2 text-right text-slate-400">
                        {country.pct_of_reserves}%
                      </td>
                      <td className="py-2 text-right">
                        {country.change_12m !== null ? (
                          <span className={country.change_12m > 0 ? 'text-green-400' : country.change_12m < 0 ? 'text-red-400' : 'text-slate-400'}>
                            {country.change_12m > 0 ? '+' : ''}{country.change_12m}t
                          </span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Key Insight */}
        <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-amber-200 font-medium">Why Are Central Banks Buying Gold?</p>
              <p className="text-amber-100/80 text-sm mt-1">
                Central banks have been net buyers for {summary.consecutive_buying_years} consecutive years.
                This trend accelerated after 2022 as geopolitical tensions and de-dollarization efforts increased.
                Gold provides reserve diversification away from USD-denominated assets and protection against sanctions.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Leaderboard view
  const renderLeaderboard = () => {
    return (
      <div className="space-y-4">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <h3 className="text-lg font-medium text-slate-200 mb-4">Full Country Leaderboard</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-left py-2 px-2">Rank</th>
                  <th className="text-left py-2 px-2">Country</th>
                  <th className="text-left py-2 px-2">Region</th>
                  <th className="text-right py-2 px-2">Holdings (t)</th>
                  <th className="text-right py-2 px-2">% of Reserves</th>
                  <th className="text-right py-2 px-2">12m Change</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((country) => (
                  <tr key={country.country_code} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="py-3 px-2">
                      <span className={`font-bold ${
                        country.rank <= 3 ? 'text-amber-400' :
                        country.rank <= 10 ? 'text-slate-300' :
                        'text-slate-500'
                      }`}>
                        {country.rank}
                      </span>
                    </td>
                    <td className="py-3 px-2">
                      <span className="text-xl mr-2">{country.flag}</span>
                      <span className="text-slate-200 font-medium">{country.country_name}</span>
                    </td>
                    <td className="py-3 px-2 text-slate-400">{country.region}</td>
                    <td className="py-3 px-2 text-right font-mono text-amber-400 font-bold">
                      {country.tonnes.toLocaleString()}
                    </td>
                    <td className="py-3 px-2 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-20 bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-amber-500 rounded-full h-2"
                            style={{ width: `${Math.min(100, country.pct_of_reserves)}%` }}
                          />
                        </div>
                        <span className="text-slate-300 w-12 text-right">{country.pct_of_reserves}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-2 text-right">
                      {country.change_12m !== null ? (
                        <span className={`flex items-center justify-end gap-1 ${
                          country.change_12m > 0 ? 'text-green-400' :
                          country.change_12m < 0 ? 'text-red-400' :
                          'text-slate-400'
                        }`}>
                          {country.change_12m > 0 ? (
                            <ArrowUpRight className="h-4 w-4" />
                          ) : country.change_12m < 0 ? (
                            <ArrowDownRight className="h-4 w-4" />
                          ) : null}
                          {country.change_12m > 0 ? '+' : ''}{country.change_12m}t
                        </span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Reserve Distribution */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h4 className="text-slate-200 font-medium mb-4">Holdings Distribution</h4>
            <div className="h-[200px]">
              <Doughnut
                data={{
                  labels: leaderboard.slice(0, 5).map(c => c.country_name).concat(['Others']),
                  datasets: [
                    {
                      data: [
                        ...leaderboard.slice(0, 5).map(c => c.tonnes),
                        leaderboard.slice(5).reduce((sum, c) => sum + c.tonnes, 0),
                      ],
                      backgroundColor: [
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(148, 163, 184, 0.8)',
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(168, 85, 247, 0.8)',
                        'rgba(100, 116, 139, 0.5)',
                      ],
                      borderWidth: 0,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'right',
                      labels: { color: '#94a3b8', font: { size: 11 } },
                    },
                  },
                }}
              />
            </div>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h4 className="text-slate-200 font-medium mb-4">Quick Stats</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-400">Countries Tracked</span>
                <span className="text-slate-200 font-medium">{leaderboard.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Total Holdings</span>
                <span className="text-amber-400 font-medium">
                  {leaderboard.reduce((sum, c) => sum + c.tonnes, 0).toLocaleString()}t
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Avg % of Reserves</span>
                <span className="text-slate-200 font-medium">
                  {(leaderboard.reduce((sum, c) => sum + c.pct_of_reserves, 0) / leaderboard.length).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Countries Buying (12m)</span>
                <span className="text-green-400 font-medium">
                  {leaderboard.filter(c => c.change_12m && c.change_12m > 0).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Countries Selling (12m)</span>
                <span className="text-red-400 font-medium">
                  {leaderboard.filter(c => c.change_12m && c.change_12m < 0).length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Net Purchases view
  const renderPurchases = () => {
    if (!purchaseSummary) return null

    return (
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Total Since 2010</p>
            <p className="text-2xl font-mono font-bold text-amber-400 mt-1">
              {purchaseSummary.total_tonnes.toLocaleString()}t
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Avg Per Year</p>
            <p className="text-2xl font-mono font-bold text-blue-400 mt-1">
              {purchaseSummary.average_per_year}t
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Recent 5yr Avg</p>
            <p className="text-2xl font-mono font-bold text-green-400 mt-1">
              {purchaseSummary.recent_5yr_avg}t
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Peak Year</p>
            <p className="text-2xl font-mono font-bold text-purple-400 mt-1">
              {purchaseSummary.peak_year}
            </p>
            <p className="text-xs text-slate-500">{purchaseSummary.peak_tonnes}t</p>
          </div>
        </div>

        {/* Full Chart */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <h3 className="text-slate-200 font-medium mb-4">Annual Net Purchases (2010-2024)</h3>
          <div className="h-[350px]">
            <Bar
              data={{
                labels: netPurchases.map(p => p.year),
                datasets: [
                  {
                    label: 'Net Purchases (tonnes)',
                    data: netPurchases.map(p => p.tonnes),
                    backgroundColor: netPurchases.map(p =>
                      p.tonnes >= 1000 ? 'rgba(34, 197, 94, 0.8)' :
                      p.tonnes >= 500 ? 'rgba(251, 191, 36, 0.8)' :
                      p.tonnes >= 300 ? 'rgba(59, 130, 246, 0.8)' :
                      'rgba(100, 116, 139, 0.8)'
                    ),
                    borderColor: netPurchases.map(p =>
                      p.tonnes >= 1000 ? 'rgb(34, 197, 94)' :
                      p.tonnes >= 500 ? 'rgb(251, 191, 36)' :
                      p.tonnes >= 300 ? 'rgb(59, 130, 246)' :
                      'rgb(100, 116, 139)'
                    ),
                    borderWidth: 2,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                  },
                },
                scales: {
                  x: {
                    grid: { color: 'rgba(51, 65, 85, 0.5)' },
                    ticks: { color: '#94a3b8' },
                  },
                  y: {
                    grid: { color: 'rgba(51, 65, 85, 0.5)' },
                    ticks: {
                      color: '#64748b',
                      callback: (value: string | number) => `${value}t`,
                    },
                  },
                },
              }}
            />
          </div>
        </div>

        {/* Legend */}
        <div className="flex gap-4 justify-center text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-500" />
            <span className="text-slate-400">1,000+ tonnes</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-amber-500" />
            <span className="text-slate-400">500-999 tonnes</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-500" />
            <span className="text-slate-400">300-499 tonnes</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-slate-500" />
            <span className="text-slate-400">&lt;300 tonnes</span>
          </div>
        </div>

        {/* Context */}
        <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
          <h4 className="text-blue-200 font-medium mb-2">Historical Context</h4>
          <p className="text-blue-100/80 text-sm">
            Central banks turned from net sellers to net buyers in 2010 after decades of selling.
            The 2022 record of 1,082 tonnes was driven by emerging market central banks diversifying
            reserves following Russia sanctions. China, India, Turkey, and Poland led the buying.
          </p>
        </div>
      </div>
    )
  }

  // Top Buyers view
  const renderBuyers = () => {
    return (
      <div className="space-y-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <h3 className="text-lg font-medium text-slate-200 mb-4">Top Gold Buyers (12-Month Change)</h3>

          {topBuyers.length === 0 ? (
            <p className="text-slate-400 text-center py-8">Loading top buyers...</p>
          ) : (
            <div className="space-y-3">
              {topBuyers.map((buyer, index) => (
                <div
                  key={buyer.country_code}
                  className="flex items-center gap-4 p-3 bg-slate-700/30 rounded-lg"
                >
                  <span className={`text-xl font-bold ${
                    index === 0 ? 'text-amber-400' :
                    index === 1 ? 'text-slate-300' :
                    index === 2 ? 'text-amber-600' :
                    'text-slate-500'
                  }`}>
                    #{index + 1}
                  </span>
                  <span className="text-2xl">{buyer.flag}</span>
                  <div className="flex-1">
                    <p className="text-slate-200 font-medium">{buyer.country_name}</p>
                    <p className="text-xs text-slate-400">
                      Total: {buyer.tonnes.toLocaleString()}t ({buyer.pct_of_reserves}% of reserves)
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-mono font-bold text-green-400">
                      +{buyer.change_12m}t
                    </p>
                    <p className="text-xs text-slate-400">12-month change</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Notable Buyers Deep Dive */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/20 border border-red-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🇨🇳</span>
              <h4 className="text-red-200 font-medium">China: The Mystery Buyer</h4>
            </div>
            <p className="text-red-100/80 text-sm">
              China officially reports ~2,264 tonnes but estimates suggest actual holdings may be
              2-3x higher. The PBOC purchases through state banks, and domestic gold production
              (~380t/yr) never leaves the country.
            </p>
          </div>

          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🇷🇺</span>
              <h4 className="text-blue-200 font-medium">Russia: Sanctions Hedge</h4>
            </div>
            <p className="text-blue-100/80 text-sm">
              Russia accelerated gold buying after 2014 Crimea sanctions. With ~2,336 tonnes (27% of reserves),
              gold provides protection against USD-based financial restrictions.
            </p>
          </div>

          <div className="bg-gradient-to-br from-orange-900/30 to-orange-800/20 border border-orange-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🇮🇳</span>
              <h4 className="text-orange-200 font-medium">India: Steady Accumulator</h4>
            </div>
            <p className="text-orange-100/80 text-sm">
              The RBI has steadily increased gold reserves to ~855 tonnes (9% of reserves).
              India's cultural affinity for gold extends to its central bank policy.
            </p>
          </div>

          <div className="bg-gradient-to-br from-emerald-900/30 to-emerald-800/20 border border-emerald-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🇵🇱</span>
              <h4 className="text-emerald-200 font-medium">Poland: European Leader</h4>
            </div>
            <p className="text-emerald-100/80 text-sm">
              Poland has aggressively added gold, now holding ~420 tonnes (15% of reserves).
              Part of a broader European trend of repatriating and increasing gold holdings.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Central Bank Gold Tracker</h2>
          <p className="text-slate-400 mt-1">Global central bank gold holdings, purchases, and de-dollarization trends</p>
        </div>

        {/* View Selector */}
        <div className="flex gap-2 flex-wrap">
          {[
            { id: 'overview', label: 'Overview', icon: Globe },
            { id: 'leaderboard', label: 'Leaderboard', icon: Building2 },
            { id: 'purchases', label: 'Net Purchases', icon: TrendingUp },
            { id: 'buyers', label: 'Top Buyers', icon: ArrowUpRight },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setView(id as ViewType)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                view === id
                  ? 'bg-amber-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400"></div>
          <span className="ml-3 text-slate-400">Loading data...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-200">
          <p className="font-medium">Error loading data</p>
          <p className="text-sm text-red-300 mt-1">{error}</p>
        </div>
      )}

      {/* Content */}
      {!loading && !error && (
        <>
          {view === 'overview' && renderOverview()}
          {view === 'leaderboard' && renderLeaderboard()}
          {view === 'purchases' && renderPurchases()}
          {view === 'buyers' && renderBuyers()}
        </>
      )}

      {/* Disclaimer */}
      <DataDisclaimer className="mt-8" />
    </div>
  )
}
