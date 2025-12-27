/**
 * History Chart Component - Visualizes sovereignty ratio over time
 * File: web/components/HistoryChart.tsx
 */

'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart
} from 'recharts'

interface HistoryChartProps {
  address: string
  currentRatio: number
}

interface Snapshot {
  id: number
  timestamp: string
  sovereignty_ratio: number
  sovereignty_status: string
  hard_money_usd: number
  total_portfolio_usd: number
  hard_money_pct: number
}

interface ProgressData {
  current_ratio: number
  previous_ratio: number | null
  change_absolute: number | null
  change_pct: number | null
  trend: string
  days_tracked: number
  snapshots_count: number
  projected_next_status: {
    status: string
    ratio_needed: number
    projected_date: string
  } | null
}

interface AllTimeData {
  high: number
  low: number
  average: number
  first_tracked: string
}

interface HistoryResponse {
  address: string
  snapshots: Snapshot[]
  progress: ProgressData
  all_time: AllTimeData | null
}

// Status threshold lines
const STATUS_THRESHOLDS = [
  { value: 1, label: 'Fragile', color: '#ef4444' },
  { value: 3, label: 'Robust', color: '#f59e0b' },
  { value: 6, label: 'Antifragile', color: '#22c55e' },
  { value: 20, label: 'Generational', color: '#10b981' },
]

export function HistoryChart({ address, currentRatio }: HistoryChartProps) {
  const [history, setHistory] = useState<HistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    fetchHistory()
  }, [address])
  
  const fetchHistory = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/v1/history/${address}?days=90`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch history')
      }
      
      const data: HistoryResponse = await response.json()
      setHistory(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }
  
  // Loading state
  if (loading) {
    return (
      <Card className="border-slate-700 bg-slate-900/50">
        <CardContent className="pt-6">
          <div className="h-64 flex items-center justify-center">
            <div className="animate-pulse text-slate-400">Loading history...</div>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  // No history yet - first time user
  if (!history || history.progress.snapshots_count <= 1) {
    return (
      <Card className="border-slate-700 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📈 Track Your Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🚀</div>
            <h3 className="text-lg font-semibold text-slate-200 mb-2">
              This is your first analysis!
            </h3>
            <p className="text-slate-400 max-w-md mx-auto">
              Come back in a few days to see your sovereignty ratio change over time.
              We'll automatically save snapshots when you analyze your wallet.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  // Prepare chart data (reverse to show oldest first)
  const chartData = [...history.snapshots]
    .reverse()
    .map(snapshot => ({
      date: new Date(snapshot.timestamp).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      }),
      ratio: snapshot.sovereignty_ratio,
      hardMoneyUsd: snapshot.hard_money_usd,
      fullDate: new Date(snapshot.timestamp).toLocaleDateString()
    }))
  
  // Calculate max Y value for chart (round up to nearest threshold)
  const maxRatio = Math.max(currentRatio, ...chartData.map(d => d.ratio))
  const yAxisMax = STATUS_THRESHOLDS.find(t => t.value > maxRatio)?.value || Math.ceil(maxRatio * 1.2)
  
  const { progress, all_time } = history
  
  // Trend indicator
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return '📈'
      case 'declining': return '📉'
      case 'stable': return '➡️'
      default: return '🆕'
    }
  }
  
  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return 'text-green-400'
      case 'declining': return 'text-red-400'
      default: return 'text-slate-400'
    }
  }
  
  return (
    <Card className="border-slate-700 bg-slate-900/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              📈 Sovereignty Progress
            </CardTitle>
            <CardDescription>
              {progress.days_tracked} days tracked • {progress.snapshots_count} snapshots
            </CardDescription>
          </div>
          
          {/* Trend Badge */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 ${getTrendColor(progress.trend)}`}>
            <span>{getTrendIcon(progress.trend)}</span>
            <span className="font-semibold capitalize">{progress.trend}</span>
            {progress.change_pct !== null && (
              <span className="text-sm">
                ({progress.change_pct > 0 ? '+' : ''}{progress.change_pct.toFixed(1)}%)
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Progress Summary */}
        {progress.change_absolute !== null && (
          <div className={`mb-4 p-3 rounded-lg ${
            progress.trend === 'improving' 
              ? 'bg-green-500/10 border border-green-500/20' 
              : progress.trend === 'declining'
              ? 'bg-red-500/10 border border-red-500/20'
              : 'bg-slate-800 border border-slate-700'
          }`}>
            <p className="text-sm">
              {progress.trend === 'improving' && (
                <span className="text-green-400">
                  🎉 Your sovereignty ratio improved <strong>{Math.abs(progress.change_pct || 0).toFixed(1)}%</strong> over the last 30 days!
                </span>
              )}
              {progress.trend === 'declining' && (
                <span className="text-red-400">
                  ⚠️ Your ratio declined <strong>{Math.abs(progress.change_pct || 0).toFixed(1)}%</strong>. Consider stacking more hard money.
                </span>
              )}
              {progress.trend === 'stable' && (
                <span className="text-slate-300">
                  Your ratio has remained stable. Keep stacking to reach your next milestone!
                </span>
              )}
            </p>
          </div>
        )}
        
        {/* Chart */}
        <div className="h-64 mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="ratioGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                </linearGradient>
              </defs>
              
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              
              <XAxis 
                dataKey="date" 
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
              />
              
              <YAxis 
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                domain={[0, yAxisMax]}
                tickFormatter={(value) => `${value}y`}
              />
              
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(value: number, name: string) => {
                  if (name === 'ratio') return [`${value.toFixed(2)} years`, 'Ratio']
                  return [value, name]
                }}
              />
              
              {/* Status threshold reference lines */}
              {STATUS_THRESHOLDS.filter(t => t.value <= yAxisMax).map(threshold => (
                <ReferenceLine
                  key={threshold.label}
                  y={threshold.value}
                  stroke={threshold.color}
                  strokeDasharray="5 5"
                  strokeOpacity={0.5}
                  label={{
                    value: threshold.label,
                    position: 'right',
                    fill: threshold.color,
                    fontSize: 10,
                  }}
                />
              ))}
              
              <Area
                type="monotone"
                dataKey="ratio"
                stroke="#f97316"
                fill="url(#ratioGradient)"
                strokeWidth={0}
              />
              
              <Line
                type="monotone"
                dataKey="ratio"
                stroke="#f97316"
                strokeWidth={3}
                dot={{ fill: '#f97316', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: '#fb923c' }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        
        {/* Projection */}
        {progress.projected_next_status && (
          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <p className="text-sm text-blue-300">
              🔮 At this rate, you'll reach <strong>{progress.projected_next_status.status}</strong> status 
              by <strong>{new Date(progress.projected_next_status.projected_date).toLocaleDateString()}</strong>
            </p>
          </div>
        )}
        
        {/* All-Time Stats */}
        {all_time && (
          <div className="mt-4 pt-4 border-t border-slate-700">
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-xs text-slate-500 uppercase">All-Time High</div>
                <div className="text-lg font-bold text-green-400">{all_time.high.toFixed(1)}y</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 uppercase">All-Time Low</div>
                <div className="text-lg font-bold text-red-400">{all_time.low.toFixed(1)}y</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 uppercase">Average</div>
                <div className="text-lg font-bold text-slate-300">{all_time.average.toFixed(1)}y</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 uppercase">Tracking Since</div>
                <div className="text-lg font-bold text-slate-300">
                  {new Date(all_time.first_tracked).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
