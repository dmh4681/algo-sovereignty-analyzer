'use client'

import { useState, useEffect, useMemo } from 'react'
import {
  getInflationSummary,
  getInflationAdjustedPrices,
  getM2Comparison,
  getPurchasingPower,
  type InflationSummary,
  type AdjustedPrice,
  type M2Comparison,
  type PurchasingPower,
} from '@/lib/api'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import { TrendingUp, TrendingDown, DollarSign, Scale, Banknote, AlertTriangle, Info, ChevronDown } from 'lucide-react'

ChartJS.register(
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

// View types
type ViewType = 'overview' | 'real-vs-nominal' | 'm2-comparison' | 'purchasing-power'

// Base year options
const BASE_YEAR_OPTIONS = [1970, 1980, 2000, 2020, 2024]

export function InflationCharts() {
  const [view, setView] = useState<ViewType>('overview')
  const [metal, setMetal] = useState<'gold' | 'silver'>('gold')
  const [baseYear, setBaseYear] = useState(2024)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [summary, setSummary] = useState<InflationSummary | null>(null)
  const [adjustedPrices, setAdjustedPrices] = useState<AdjustedPrice[]>([])
  const [m2Data, setM2Data] = useState<M2Comparison[]>([])
  const [m2Interpretation, setM2Interpretation] = useState<{
    peak_year: number
    peak_context: string
    current_pct_of_peak: number | null
    implication: string
  } | null>(null)
  const [purchasingPower, setPurchasingPower] = useState<PurchasingPower | null>(null)

  // Fetch data based on current view
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)

      try {
        // Always fetch summary for overview stats
        const summaryRes = await getInflationSummary()
        setSummary(summaryRes.stats)

        if (view === 'real-vs-nominal') {
          const adjustedRes = await getInflationAdjustedPrices(metal, baseYear)
          setAdjustedPrices(adjustedRes.data)
        } else if (view === 'm2-comparison') {
          const m2Res = await getM2Comparison()
          setM2Data(m2Res.data)
          setM2Interpretation(m2Res.interpretation)
        } else if (view === 'purchasing-power') {
          const ppRes = await getPurchasingPower(1970)
          setPurchasingPower(ppRes.purchasing_power)
        }
      } catch (err) {
        console.error('Error fetching inflation data:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [view, metal, baseYear])

  // Overview Stats Cards
  const renderOverview = () => {
    if (!summary) return null

    const pp = summary.purchasing_power

    return (
      <div className="space-y-6">
        {/* Key Insight Banner */}
        <div className="bg-gradient-to-r from-amber-900/30 to-amber-800/20 border border-amber-700/50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-amber-200 font-medium">Did Gold Beat Its 1980 High?</p>
              <p className="text-amber-100/80 text-sm mt-1">
                The 1980 gold peak of $675/oz equals <span className="font-mono font-bold text-amber-300">${summary.gold_1980_peak_in_todays_dollars.toLocaleString()}</span> in today's dollars.
                {summary.current_gold && summary.current_gold_vs_1980_real_pct < 100 ? (
                  <span> At ${summary.current_gold.toLocaleString()}, gold is only <span className="font-bold text-red-400">{summary.current_gold_vs_1980_real_pct.toFixed(0)}%</span> of its 1980 peak in real terms!</span>
                ) : (
                  <span> Gold has finally exceeded its 1980 peak in real terms.</span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Dollar Debasement */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
              <DollarSign className="h-4 w-4" />
              <span>$1 (1970) Now Worth</span>
            </div>
            <p className="text-3xl font-mono font-bold text-red-400">
              ${pp.dollar_value_today.toFixed(2)}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {pp.purchasing_power_lost_pct.toFixed(0)}% purchasing power lost
            </p>
          </div>

          {/* Cumulative Inflation */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
              <TrendingUp className="h-4 w-4" />
              <span>Cumulative Inflation</span>
            </div>
            <p className="text-3xl font-mono font-bold text-orange-400">
              {pp.cumulative_inflation_pct.toFixed(0)}%
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Since 1970 ({pp.average_annual_inflation_pct.toFixed(1)}%/yr avg)
            </p>
          </div>

          {/* Current Gold */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
              <Scale className="h-4 w-4" />
              <span>Gold Price</span>
            </div>
            <p className="text-3xl font-mono font-bold text-amber-400">
              ${summary.current_gold?.toLocaleString() || 'N/A'}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Current spot price
            </p>
          </div>

          {/* M2 Money Supply */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
              <Banknote className="h-4 w-4" />
              <span>M2 Money Supply</span>
            </div>
            <p className="text-3xl font-mono font-bold text-blue-400">
              ${(summary.current_m2_billions ? summary.current_m2_billions / 1000 : 0).toFixed(1)}T
            </p>
            <p className="text-xs text-slate-500 mt-1">
              US M2 (was $0.6T in 1970)
            </p>
          </div>
        </div>

        {/* Purchasing Power Visual */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-200 mb-4">Dollar Purchasing Power Since 1970</h3>
          <div className="relative h-8 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="absolute left-0 top-0 h-full bg-gradient-to-r from-green-600 to-red-600"
              style={{ width: '100%' }}
            />
            <div
              className="absolute right-0 top-0 h-full bg-slate-900/80"
              style={{ width: `${pp.purchasing_power_lost_pct}%` }}
            />
            <div className="absolute inset-0 flex items-center justify-between px-4 text-sm font-medium">
              <span className="text-green-300">$1.00 (1970)</span>
              <span className="text-red-300">${pp.dollar_value_today.toFixed(2)} (Today)</span>
            </div>
          </div>
          <p className="text-center text-slate-400 text-sm mt-3">
            The dollar has lost <span className="text-red-400 font-bold">{pp.purchasing_power_lost_pct.toFixed(0)}%</span> of its value since 1970
          </p>
        </div>

        {/* Quick Links to Other Views */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setView('real-vs-nominal')}
            className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-left hover:bg-slate-700/50 transition-colors"
          >
            <h4 className="font-medium text-amber-400">Real vs Nominal Prices</h4>
            <p className="text-sm text-slate-400 mt-1">See gold/silver adjusted for inflation</p>
          </button>
          <button
            onClick={() => setView('m2-comparison')}
            className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-left hover:bg-slate-700/50 transition-colors"
          >
            <h4 className="font-medium text-blue-400">M2 Money Supply</h4>
            <p className="text-sm text-slate-400 mt-1">Compare gold to money printing</p>
          </button>
          <button
            onClick={() => setView('purchasing-power')}
            className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-left hover:bg-slate-700/50 transition-colors"
          >
            <h4 className="font-medium text-red-400">Purchasing Power</h4>
            <p className="text-sm text-slate-400 mt-1">Track dollar debasement over time</p>
          </button>
        </div>
      </div>
    )
  }

  // Real vs Nominal Price Chart
  const renderRealVsNominal = () => {
    if (adjustedPrices.length === 0) {
      return <div className="text-slate-400 text-center py-8">No data available</div>
    }

    const chartData = {
      labels: adjustedPrices.map(d => d.date),
      datasets: [
        {
          label: `Nominal ${metal === 'gold' ? 'Gold' : 'Silver'} Price`,
          data: adjustedPrices.map(d => d.nominal_price),
          borderColor: metal === 'gold' ? 'rgb(251, 191, 36)' : 'rgb(148, 163, 184)',
          backgroundColor: metal === 'gold' ? 'rgba(251, 191, 36, 0.1)' : 'rgba(148, 163, 184, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          fill: false,
        },
        {
          label: `Real Price (${baseYear} Dollars)`,
          data: adjustedPrices.map(d => d.real_price),
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          borderWidth: 2,
          borderDash: [5, 5],
          tension: 0.3,
          fill: false,
        },
      ],
    }

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index' as const,
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top' as const,
          labels: { color: '#94a3b8' },
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleColor: '#f1f5f9',
          bodyColor: '#cbd5e1',
          borderColor: '#334155',
          borderWidth: 1,
          callbacks: {
            label: (context: any) => {
              const value = context.raw
              return `${context.dataset.label}: $${value.toLocaleString()}`
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(51, 65, 85, 0.5)' },
          ticks: { color: '#64748b', maxTicksLimit: 12 },
        },
        y: {
          type: 'logarithmic' as const,
          grid: { color: 'rgba(51, 65, 85, 0.5)' },
          ticks: {
            color: '#64748b',
            callback: (value: string | number) => `$${Number(value).toLocaleString()}`,
          },
        },
      },
    }

    // Find peak values
    const nominalPeak = Math.max(...adjustedPrices.map(d => d.nominal_price))
    const realPeak = Math.max(...adjustedPrices.map(d => d.real_price))
    const currentNominal = adjustedPrices[adjustedPrices.length - 1]?.nominal_price || 0
    const currentReal = adjustedPrices[adjustedPrices.length - 1]?.real_price || 0

    return (
      <div className="space-y-6">
        {/* Controls */}
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex gap-2">
            <button
              onClick={() => setMetal('gold')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                metal === 'gold'
                  ? 'bg-amber-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Gold
            </button>
            <button
              onClick={() => setMetal('silver')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                metal === 'silver'
                  ? 'bg-slate-500 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Silver
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">Base Year:</span>
            <select
              value={baseYear}
              onChange={e => setBaseYear(Number(e.target.value))}
              className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200"
            >
              {BASE_YEAR_OPTIONS.map(year => (
                <option key={year} value={year}>
                  {year} Dollars
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="h-[400px]">
            <Line data={chartData} options={options} />
          </div>
        </div>

        {/* Insights */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h4 className="text-slate-400 text-sm mb-2">Nominal Peak</h4>
            <p className="text-2xl font-mono font-bold text-amber-400">
              ${nominalPeak.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Current: ${currentNominal.toLocaleString()} ({((currentNominal / nominalPeak) * 100).toFixed(0)}% of peak)
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h4 className="text-slate-400 text-sm mb-2">Real Peak ({baseYear} $)</h4>
            <p className="text-2xl font-mono font-bold text-green-400">
              ${realPeak.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Current Real: ${currentReal.toLocaleString()} ({((currentReal / realPeak) * 100).toFixed(0)}% of peak)
            </p>
          </div>
        </div>

        {/* Explanation */}
        <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-200">
              <p className="font-medium">How to Read This Chart</p>
              <p className="mt-1 text-blue-300/80">
                The <span className="text-amber-400">solid line</span> shows the nominal (unadjusted) price.
                The <span className="text-green-400">dashed line</span> shows the real price adjusted for inflation to {baseYear} dollars.
                When the real line is above the nominal line, it means the historical price was worth more in today's purchasing power than its face value suggests.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // M2 Comparison Chart
  const renderM2Comparison = () => {
    if (m2Data.length === 0) {
      return <div className="text-slate-400 text-center py-8">No data available</div>
    }

    const chartData = {
      labels: m2Data.map(d => d.date),
      datasets: [
        {
          label: 'Gold Price ($)',
          data: m2Data.map(d => d.gold_price),
          borderColor: 'rgb(251, 191, 36)',
          backgroundColor: 'rgba(251, 191, 36, 0.1)',
          borderWidth: 2,
          yAxisID: 'y',
          tension: 0.3,
        },
        {
          label: 'M2 Money Supply ($B)',
          data: m2Data.map(d => d.m2_billions),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          yAxisID: 'y1',
          tension: 0.3,
        },
      ],
    }

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index' as const,
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top' as const,
          labels: { color: '#94a3b8' },
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleColor: '#f1f5f9',
          bodyColor: '#cbd5e1',
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(51, 65, 85, 0.5)' },
          ticks: { color: '#64748b', maxTicksLimit: 12 },
        },
        y: {
          type: 'logarithmic' as const,
          position: 'left' as const,
          grid: { color: 'rgba(51, 65, 85, 0.5)' },
          ticks: {
            color: '#fbbf24',
            callback: (value: string | number) => `$${Number(value).toLocaleString()}`,
          },
          title: {
            display: true,
            text: 'Gold Price',
            color: '#fbbf24',
          },
        },
        y1: {
          type: 'logarithmic' as const,
          position: 'right' as const,
          grid: { display: false },
          ticks: {
            color: '#3b82f6',
            callback: (value: string | number) => `$${(Number(value) / 1000).toFixed(0)}T`,
          },
          title: {
            display: true,
            text: 'M2 Money Supply',
            color: '#3b82f6',
          },
        },
      },
    }

    // Gold/M2 Ratio Chart
    const ratioChartData = {
      labels: m2Data.map(d => d.date),
      datasets: [
        {
          label: 'Gold/M2 Ratio (% of 1980 Peak)',
          data: m2Data.map(d => d.gold_m2_ratio_pct_of_peak),
          borderColor: 'rgb(168, 85, 247)',
          backgroundColor: 'rgba(168, 85, 247, 0.2)',
          borderWidth: 2,
          fill: true,
          tension: 0.3,
        },
      ],
    }

    const ratioOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
          labels: { color: '#94a3b8' },
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          callbacks: {
            label: (context: any) => `${context.raw.toFixed(1)}% of 1980 peak ratio`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(51, 65, 85, 0.5)' },
          ticks: { color: '#64748b', maxTicksLimit: 12 },
        },
        y: {
          grid: { color: 'rgba(51, 65, 85, 0.5)' },
          ticks: {
            color: '#64748b',
            callback: (value: string | number) => `${value}%`,
          },
          suggestedMin: 0,
          suggestedMax: 100,
        },
      },
    }

    const currentRatioPct = m2Data[m2Data.length - 1]?.gold_m2_ratio_pct_of_peak || 0
    const currentM2 = m2Data[m2Data.length - 1]?.m2_billions || 0
    const currentGold = m2Data[m2Data.length - 1]?.gold_price || 0

    // Calculate what gold would be at 1980 ratio
    const goldAt1980Ratio = currentRatioPct > 0 ? (currentGold / currentRatioPct) * 100 : 0

    return (
      <div className="space-y-6">
        {/* Key Insight */}
        <div className="bg-purple-900/30 border border-purple-700/50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <TrendingUp className="h-5 w-5 text-purple-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-purple-200 font-medium">Gold vs Money Printing</p>
              <p className="text-purple-100/80 text-sm mt-1">
                Gold's ratio to M2 money supply is at <span className="font-mono font-bold text-purple-300">{currentRatioPct.toFixed(1)}%</span> of its 1980 peak.
                If gold returned to that ratio, it would be priced at <span className="font-bold text-green-400">${goldAt1980Ratio.toLocaleString()}</span>/oz.
              </p>
            </div>
          </div>
        </div>

        {/* Gold vs M2 Chart */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <h3 className="text-slate-200 font-medium mb-4">Gold Price vs M2 Money Supply (Log Scale)</h3>
          <div className="h-[350px]">
            <Line data={chartData} options={options} />
          </div>
        </div>

        {/* Ratio Chart */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <h3 className="text-slate-200 font-medium mb-4">Gold/M2 Ratio (% of 1980 Peak)</h3>
          <div className="h-[250px]">
            <Line data={ratioChartData} options={ratioOptions} />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h4 className="text-slate-400 text-sm mb-2">Current M2</h4>
            <p className="text-2xl font-mono font-bold text-blue-400">
              ${(currentM2 / 1000).toFixed(1)}T
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Was $0.6T in 1970 (35x increase)
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h4 className="text-slate-400 text-sm mb-2">Current Gold/M2 Ratio</h4>
            <p className="text-2xl font-mono font-bold text-purple-400">
              {currentRatioPct.toFixed(1)}%
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Of 1980 peak ratio
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h4 className="text-slate-400 text-sm mb-2">Gold at 1980 Ratio</h4>
            <p className="text-2xl font-mono font-bold text-green-400">
              ${goldAt1980Ratio.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Implied price at peak ratio
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Purchasing Power View
  const renderPurchasingPower = () => {
    if (!purchasingPower) {
      return <div className="text-slate-400 text-center py-8">No data available</div>
    }

    const pp = purchasingPower

    // Create a simple bar chart showing dollar value over decades
    const decades = [
      { year: 1970, value: 1.0 },
      { year: 1980, value: 0.44 },
      { year: 1990, value: 0.27 },
      { year: 2000, value: 0.21 },
      { year: 2010, value: 0.17 },
      { year: 2020, value: 0.14 },
      { year: 2025, value: pp.dollar_value_today },
    ]

    const chartData = {
      labels: decades.map(d => d.year.toString()),
      datasets: [
        {
          label: 'Dollar Value (1970 = $1.00)',
          data: decades.map(d => d.value),
          backgroundColor: decades.map(d =>
            d.value > 0.5 ? 'rgba(34, 197, 94, 0.8)' :
            d.value > 0.3 ? 'rgba(251, 191, 36, 0.8)' :
            d.value > 0.2 ? 'rgba(249, 115, 22, 0.8)' :
            'rgba(239, 68, 68, 0.8)'
          ),
          borderColor: decades.map(d =>
            d.value > 0.5 ? 'rgb(34, 197, 94)' :
            d.value > 0.3 ? 'rgb(251, 191, 36)' :
            d.value > 0.2 ? 'rgb(249, 115, 22)' :
            'rgb(239, 68, 68)'
          ),
          borderWidth: 2,
        },
      ],
    }

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          callbacks: {
            label: (context: any) => `$${context.raw.toFixed(2)} purchasing power`,
          },
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
            callback: (value: string | number) => `$${Number(value).toFixed(2)}`,
          },
          max: 1.0,
          min: 0,
        },
      },
    }

    // What $100 from different years is worth today
    const examples = [
      { year: 1970, amount: 100, todayValue: 100 * pp.dollar_value_today / 1.0 },
      { year: 1980, amount: 100, todayValue: 100 * pp.dollar_value_today / 0.44 },
      { year: 1990, amount: 100, todayValue: 100 * pp.dollar_value_today / 0.27 },
      { year: 2000, amount: 100, todayValue: 100 * pp.dollar_value_today / 0.21 },
    ]

    return (
      <div className="space-y-6">
        {/* Key Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <p className="text-slate-400 text-sm">$1 (1970) Now Worth</p>
            <p className="text-3xl font-mono font-bold text-red-400 mt-1">
              ${pp.dollar_value_today.toFixed(2)}
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Purchasing Power Lost</p>
            <p className="text-3xl font-mono font-bold text-red-400 mt-1">
              {pp.purchasing_power_lost_pct.toFixed(0)}%
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Cumulative Inflation</p>
            <p className="text-3xl font-mono font-bold text-orange-400 mt-1">
              {pp.cumulative_inflation_pct.toFixed(0)}%
            </p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Average Annual</p>
            <p className="text-3xl font-mono font-bold text-amber-400 mt-1">
              {pp.average_annual_inflation_pct.toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Debasement Chart */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <h3 className="text-slate-200 font-medium mb-4">Dollar Purchasing Power Over Time</h3>
          <div className="h-[300px]">
            <Bar data={chartData} options={options} />
          </div>
        </div>

        {/* Comparison Examples */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <h3 className="text-slate-200 font-medium mb-4">What $100 From The Past Is Worth Today</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { year: 1970, multiplier: 7.69, todayEquiv: 769 },
              { year: 1980, multiplier: 3.38, todayEquiv: 338 },
              { year: 2000, multiplier: 1.79, todayEquiv: 179 },
              { year: 2010, multiplier: 1.43, todayEquiv: 143 },
            ].map(({ year, multiplier, todayEquiv }) => (
              <div key={year} className="text-center p-3 bg-slate-700/50 rounded-lg">
                <p className="text-slate-400 text-sm">${100} in {year}</p>
                <p className="text-xl font-mono font-bold text-amber-400 mt-1">
                  ${todayEquiv}
                </p>
                <p className="text-xs text-slate-500">in today's dollars</p>
              </div>
            ))}
          </div>
        </div>

        {/* Gold as Hedge */}
        <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4">
          <h3 className="text-amber-200 font-medium mb-2">Gold as an Inflation Hedge</h3>
          <p className="text-amber-100/80 text-sm">
            While the dollar lost {pp.purchasing_power_lost_pct.toFixed(0)}% of its purchasing power since 1970,
            gold rose from $35/oz to over $2,700/oz - a <span className="font-bold text-amber-300">7,600%+</span> increase.
            This demonstrates gold's role as a store of value against currency debasement.
          </p>
        </div>
      </div>
    )
  }

  // Main render
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Inflation-Adjusted Charts</h2>
          <p className="text-slate-400 mt-1">Gold & silver prices in real terms, M2 comparison, and purchasing power analysis</p>
        </div>

        {/* View Selector */}
        <div className="flex gap-2 flex-wrap">
          {[
            { id: 'overview', label: 'Overview', icon: TrendingUp },
            { id: 'real-vs-nominal', label: 'Real vs Nominal', icon: Scale },
            { id: 'm2-comparison', label: 'M2 Comparison', icon: Banknote },
            { id: 'purchasing-power', label: 'Purchasing Power', icon: DollarSign },
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
          {view === 'real-vs-nominal' && renderRealVsNominal()}
          {view === 'm2-comparison' && renderM2Comparison()}
          {view === 'purchasing-power' && renderPurchasingPower()}
        </>
      )}
    </div>
  )
}
