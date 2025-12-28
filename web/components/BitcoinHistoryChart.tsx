'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { TrendingUp, TrendingDown, Clock, BarChart3 } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine
} from 'recharts'
import { getBTCHistory } from '@/lib/api'
import type { BTCHistoryResponse, BTCHistoryDataPoint } from '@/lib/types'

// =============================================================================
// Types
// =============================================================================

interface BitcoinHistoryChartProps {
  className?: string
}

type TimeRange = 24 | 72 | 168 | 720 // hours: 1d, 3d, 7d, 30d
type ViewMode = 'premium' | 'price'

// =============================================================================
// Constants
// =============================================================================

const TIME_RANGES: { value: TimeRange; label: string }[] = [
  { value: 24, label: '24h' },
  { value: 72, label: '3d' },
  { value: 168, label: '7d' },
  { value: 720, label: '30d' },
]

const CHART_COLORS = {
  gobtc: '#f97316', // orange
  wbtc: '#8b5cf6', // purple
  spot: '#64748b', // slate
  reference: '#334155', // dark slate
}

// =============================================================================
// Helper Functions
// =============================================================================

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function formatAxisDate(timestamp: string, range: TimeRange): string {
  const date = new Date(timestamp)
  if (range <= 24) {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// =============================================================================
// Stat Card Component
// =============================================================================

function StatMini({
  label,
  value,
  suffix = '%',
  positive
}: {
  label: string
  value: number | null
  suffix?: string
  positive?: boolean
}) {
  if (value === null) return null

  return (
    <div className="text-center">
      <div className="text-xs text-slate-500 uppercase">{label}</div>
      <div className={`text-sm font-semibold ${positive ? 'text-green-400' : 'text-slate-300'}`}>
        {value > 0 ? '+' : ''}{value.toFixed(2)}{suffix}
      </div>
    </div>
  )
}

// =============================================================================
// Custom Tooltip
// =============================================================================

function CustomTooltip({ active, payload, label, viewMode }: any) {
  if (!active || !payload || !payload.length) return null

  const data = payload[0].payload as BTCHistoryDataPoint

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
      <div className="text-xs text-slate-400 mb-2">
        {formatDate(data.timestamp)} {formatTime(data.timestamp)}
      </div>

      {viewMode === 'price' ? (
        <div className="space-y-1">
          <div className="flex items-center justify-between gap-4">
            <span className="text-slate-400 text-sm">Spot:</span>
            <span className="text-slate-200 font-mono">${data.spot_btc.toLocaleString()}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-orange-400 text-sm">goBTC:</span>
            <span className="text-orange-300 font-mono">${data.gobtc_price.toLocaleString()}</span>
          </div>
          {data.wbtc_price && (
            <div className="flex items-center justify-between gap-4">
              <span className="text-purple-400 text-sm">WBTC:</span>
              <span className="text-purple-300 font-mono">${data.wbtc_price.toLocaleString()}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-1">
          <div className="flex items-center justify-between gap-4">
            <span className="text-orange-400 text-sm">goBTC:</span>
            <span className={`font-mono ${data.gobtc_premium_pct < 0 ? 'text-green-400' : 'text-red-400'}`}>
              {data.gobtc_premium_pct > 0 ? '+' : ''}{data.gobtc_premium_pct.toFixed(2)}%
            </span>
          </div>
          {data.wbtc_premium_pct !== null && (
            <div className="flex items-center justify-between gap-4">
              <span className="text-purple-400 text-sm">WBTC:</span>
              <span className={`font-mono ${data.wbtc_premium_pct < 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.wbtc_premium_pct > 0 ? '+' : ''}{data.wbtc_premium_pct.toFixed(2)}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Main Component
// =============================================================================

export function BitcoinHistoryChart({ className = '' }: BitcoinHistoryChartProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>(24)
  const [viewMode, setViewMode] = useState<ViewMode>('premium')
  const [data, setData] = useState<BTCHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch data when time range changes
  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const result = await getBTCHistory(timeRange)
        setData(result)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [timeRange])

  // Loading state
  if (loading) {
    return (
      <Card className={`border-slate-700 bg-slate-900/50 ${className}`}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className={`border-slate-700 bg-slate-900/50 ${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Bitcoin Price History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-400">
            <p>Unable to load historical data</p>
            <p className="text-sm text-slate-500 mt-1">{error}</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => setTimeRange(timeRange)}
            >
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // No data state
  if (!data || data.data_points.length === 0) {
    return (
      <Card className={`border-slate-700 bg-slate-900/50 ${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Bitcoin Price History
          </CardTitle>
          <CardDescription>
            Premium/discount tracking over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-slate-400">
            <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No historical data available yet</p>
            <p className="text-sm text-slate-500 mt-1">
              Data will appear as prices are tracked over time
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const stats = data.stats

  return (
    <Card className={`border-slate-700 bg-slate-900/50 ${className}`}>
      <CardHeader className="pb-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Bitcoin Price History
            </CardTitle>
            <CardDescription>
              {data.data_points.length} data points over {timeRange}h
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex rounded-lg border border-slate-700 overflow-hidden">
              <button
                onClick={() => setViewMode('premium')}
                className={`px-3 py-1 text-sm ${
                  viewMode === 'premium'
                    ? 'bg-orange-500 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                Premium %
              </button>
              <button
                onClick={() => setViewMode('price')}
                className={`px-3 py-1 text-sm ${
                  viewMode === 'price'
                    ? 'bg-orange-500 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                Price $
              </button>
            </div>

            {/* Time Range Selector */}
            <div className="flex rounded-lg border border-slate-700 overflow-hidden">
              {TIME_RANGES.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setTimeRange(value)}
                  className={`px-3 py-1 text-sm ${
                    timeRange === value
                      ? 'bg-slate-700 text-white'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 p-3 bg-slate-800/30 rounded-lg">
          <div className="col-span-2 md:col-span-1">
            <div className="text-xs text-slate-500 uppercase mb-1">Token</div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-orange-500" />
              <span className="text-sm text-slate-300">goBTC</span>
            </div>
          </div>
          <StatMini label="Avg" value={stats.gobtc.avg_premium_pct} />
          <StatMini label="Min" value={stats.gobtc.min_premium_pct} positive={stats.gobtc.min_premium_pct < 0} />
          <StatMini label="Max" value={stats.gobtc.max_premium_pct} />

          {stats.wbtc.avg_premium_pct !== null && (
            <>
              <div className="col-span-2 md:col-span-1 md:border-l md:border-slate-700 md:pl-4">
                <div className="text-xs text-slate-500 uppercase mb-1">Token</div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-purple-500" />
                  <span className="text-sm text-slate-300">WBTC</span>
                </div>
              </div>
              <StatMini label="Avg" value={stats.wbtc.avg_premium_pct} />
            </>
          )}
        </div>

        {/* Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.data_points} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(v) => formatAxisDate(v, timeRange)}
                stroke="#64748b"
                fontSize={11}
                tickMargin={8}
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickFormatter={(v) =>
                  viewMode === 'premium' ? `${v}%` : `$${(v / 1000).toFixed(0)}k`
                }
                domain={viewMode === 'premium' ? ['auto', 'auto'] : ['auto', 'auto']}
              />
              <Tooltip content={<CustomTooltip viewMode={viewMode} />} />
              <Legend />

              {viewMode === 'premium' && (
                <ReferenceLine y={0} stroke={CHART_COLORS.reference} strokeDasharray="5 5" />
              )}

              {viewMode === 'premium' ? (
                <>
                  <Line
                    type="monotone"
                    dataKey="gobtc_premium_pct"
                    name="goBTC Premium"
                    stroke={CHART_COLORS.gobtc}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="wbtc_premium_pct"
                    name="WBTC Premium"
                    stroke={CHART_COLORS.wbtc}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </>
              ) : (
                <>
                  <Line
                    type="monotone"
                    dataKey="spot_btc"
                    name="Coinbase Spot"
                    stroke={CHART_COLORS.spot}
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="gobtc_price"
                    name="goBTC"
                    stroke={CHART_COLORS.gobtc}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="wbtc_price"
                    name="WBTC"
                    stroke={CHART_COLORS.wbtc}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </>
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Interpretation Guide */}
        <div className="flex flex-wrap gap-4 justify-center text-xs text-slate-500 pt-2 border-t border-slate-800">
          {viewMode === 'premium' ? (
            <>
              <span className="flex items-center gap-1">
                <TrendingDown className="h-3 w-3 text-green-500" />
                Below 0% = Discount (buy opportunity)
              </span>
              <span className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3 text-red-500" />
                Above 0% = Premium (sell opportunity)
              </span>
            </>
          ) : (
            <>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-slate-500" />
                Dashed = Coinbase reference
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-orange-500" />
                goBTC (native)
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-purple-500" />
                WBTC (bridged)
              </span>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default BitcoinHistoryChart
