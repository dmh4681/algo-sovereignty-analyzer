'use client'

import { useEffect, useState, useCallback } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Card } from '@/components/ui/card'
import { getHistory } from '@/lib/api'
import { SovereigntySnapshot } from '@/lib/types'
import { formatNumber } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus, History, RefreshCw } from 'lucide-react'

interface HistoryChartProps {
  address: string
  monthlyExpenses?: number
}

type TimeRange = 30 | 90 | 365

interface ChartData {
  date: string
  ratio: number
  timestamp: string
}

export function HistoryChart({ address, monthlyExpenses }: HistoryChartProps) {
  const [snapshots, setSnapshots] = useState<SovereigntySnapshot[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<TimeRange>(90)

  const fetchHistory = useCallback(async () => {
    if (!address) return

    setLoading(true)
    setError(null)

    try {
      const response = await getHistory(address, timeRange)
      setSnapshots(response.snapshots)
    } catch (err) {
      setError('Failed to load history')
      console.error('History fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [address, timeRange])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  // Transform snapshots to chart data
  const chartData: ChartData[] = snapshots.map((snapshot) => {
    const date = new Date(snapshot.timestamp)
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      ratio: snapshot.sovereignty_ratio,
      timestamp: snapshot.timestamp,
    }
  })

  // Calculate stats
  const currentRatio = snapshots.length > 0 ? snapshots[snapshots.length - 1].sovereignty_ratio : 0
  const bestRatio = snapshots.length > 0 ? Math.max(...snapshots.map((s) => s.sovereignty_ratio)) : 0

  // Calculate trend (compare latest to 7 days ago or earliest)
  const getTrend = () => {
    if (snapshots.length < 2) return 'neutral'

    const latest = snapshots[snapshots.length - 1].sovereignty_ratio
    const weekAgo = new Date()
    weekAgo.setDate(weekAgo.getDate() - 7)

    // Find snapshot closest to 7 days ago
    let comparisonSnapshot = snapshots[0]
    for (const snapshot of snapshots) {
      const snapshotDate = new Date(snapshot.timestamp)
      if (snapshotDate <= weekAgo) {
        comparisonSnapshot = snapshot
      } else {
        break
      }
    }

    const diff = latest - comparisonSnapshot.sovereignty_ratio
    if (diff > 0.1) return 'up'
    if (diff < -0.1) return 'down'
    return 'neutral'
  }

  const trend = getTrend()

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendColor =
    trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-slate-400'
  const trendLabel = trend === 'up' ? 'Improving' : trend === 'down' ? 'Declining' : 'Stable'

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ value: number; payload: ChartData }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-lg">
          <p className="text-slate-400 text-xs mb-1">{data.date}</p>
          <p className="text-orange-400 font-bold text-lg">
            {formatNumber(data.ratio, 2)} years
          </p>
        </div>
      )
    }
    return null
  }

  // No data state
  if (!loading && snapshots.length === 0) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <History className="w-5 h-5 text-slate-400" />
            <h3 className="text-lg font-semibold text-slate-200">Sovereignty History</h3>
          </div>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-700/50 flex items-center justify-center mb-4">
              <History className="w-8 h-8 text-slate-500" />
            </div>
            <p className="text-slate-400 mb-2">No history data yet</p>
            <p className="text-sm text-slate-500 max-w-sm">
              {monthlyExpenses
                ? 'Your sovereignty ratio will be tracked automatically each time you analyze your wallet.'
                : 'Enter your monthly expenses above to start tracking your sovereignty over time.'}
            </p>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-slate-400" />
            <h3 className="text-lg font-semibold text-slate-200">Sovereignty History</h3>
          </div>
          <button
            onClick={fetchHistory}
            disabled={loading}
            className="p-2 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
            title="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Current</div>
            <div className="text-2xl font-bold text-orange-400 tabular-nums">
              {formatNumber(currentRatio, 1)}y
            </div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Best Ever</div>
            <div className="text-2xl font-bold text-emerald-400 tabular-nums">
              {formatNumber(bestRatio, 1)}y
            </div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Trend</div>
            <div className={`text-xl font-bold flex items-center gap-1 ${trendColor}`}>
              <TrendIcon className="w-5 h-5" />
              <span>{trendLabel}</span>
            </div>
          </div>
        </div>

        {/* Time Range Toggle */}
        <div className="flex gap-2 mb-4">
          {([30, 90, 365] as TimeRange[]).map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                timeRange === days
                  ? 'bg-orange-500 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {days}d
            </button>
          ))}
        </div>

        {/* Chart */}
        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="animate-pulse text-slate-400">Loading history...</div>
          </div>
        ) : error ? (
          <div className="h-64 flex items-center justify-center">
            <div className="text-red-400">{error}</div>
          </div>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickLine={{ stroke: '#64748b' }}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickLine={{ stroke: '#64748b' }}
                  tickFormatter={(value) => `${value}y`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="ratio"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={{ fill: '#f97316', strokeWidth: 0, r: 4 }}
                  activeDot={{ r: 6, stroke: '#f97316', strokeWidth: 2, fill: '#1e293b' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Chart Legend */}
        <div className="mt-4 text-center text-xs text-slate-500">
          Sovereignty ratio over time based on hard money holdings
        </div>
      </div>
    </Card>
  )
}
