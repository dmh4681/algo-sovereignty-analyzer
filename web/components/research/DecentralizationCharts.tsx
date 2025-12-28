'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  ComposedChart
} from 'recharts'

// ============================================================================
// Types
// ============================================================================

interface DecentralizationChartsProps {
  foundationStake: number
  communityStake: number
  nodeData: number[]
  governanceData?: GovernanceDataPoint[]
  className?: string
}

interface GovernanceDataPoint {
  period: string
  committed: number // in millions of ALGO
}

// ============================================================================
// Default Data
// ============================================================================

const DEFAULT_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const DEFAULT_NODE_DATA = [900, 950, 1050, 1200, 1400, 1550, 1650, 1750, 1850, 1900, 1950, 2000]

const DEFAULT_GOVERNANCE_DATA: GovernanceDataPoint[] = [
  { period: 'G1', committed: 1500 },
  { period: 'G2', committed: 2100 },
  { period: 'G3', committed: 2800 },
  { period: 'G4', committed: 3200 },
  { period: 'G5', committed: 2900 },
  { period: 'G6', committed: 3100 },
  { period: 'G7', committed: 3400 },
  { period: 'G8', committed: 3600 },
]

// ============================================================================
// Stake Distribution Donut Chart
// ============================================================================

interface StakeDonutChartProps {
  foundationStake: number
  communityStake: number
  animated?: boolean
}

function StakeDonutChart({ foundationStake, communityStake, animated = true }: StakeDonutChartProps) {
  const [isAnimated, setIsAnimated] = useState(false)

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => setIsAnimated(true), 100)
      return () => clearTimeout(timer)
    }
  }, [animated])

  const data = [
    { name: 'Foundation', value: foundationStake, color: '#64748b' },
    { name: 'Community', value: communityStake, color: '#14b8a6' },
  ]

  const total = foundationStake + communityStake
  const communityPct = ((communityStake / total) * 100).toFixed(0)

  return (
    <Card className="border-slate-700 bg-slate-900/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          Stake Distribution
        </CardTitle>
        <CardDescription>
          Foundation vs Community stake allocation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64 relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                animationBegin={0}
                animationDuration={isAnimated ? 1000 : 0}
                animationEasing="ease-out"
              >
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.color}
                    stroke="transparent"
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => [`${value}%`, '']}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => (
                  <span className="text-slate-300 text-sm">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* Center Label */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center -mt-8">
              <div className="text-3xl font-bold text-teal-400">{communityPct}%</div>
              <div className="text-xs text-slate-400">Community</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Node Growth Line Chart
// ============================================================================

interface NodeGrowthChartProps {
  nodeData: number[]
  months?: string[]
  animated?: boolean
}

function NodeGrowthChart({
  nodeData = DEFAULT_NODE_DATA,
  months = DEFAULT_MONTHS,
  animated = true
}: NodeGrowthChartProps) {
  const [isAnimated, setIsAnimated] = useState(false)

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => setIsAnimated(true), 100)
      return () => clearTimeout(timer)
    }
  }, [animated])

  const chartData = months.map((month, index) => ({
    month,
    nodes: nodeData[index] || 0,
  }))

  const minNodes = Math.min(...nodeData) * 0.9
  const maxNodes = Math.max(...nodeData) * 1.1

  return (
    <Card className="border-slate-700 bg-slate-900/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          Node Growth 2025
        </CardTitle>
        <CardDescription>
          Participation node count over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="nodeGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0.05}/>
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />

              <XAxis
                dataKey="month"
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: '#475569' }}
              />

              <YAxis
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                domain={[minNodes, maxNodes]}
                tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
                axisLine={{ stroke: '#475569' }}
              />

              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(value: number) => [value.toLocaleString(), 'Nodes']}
              />

              <Area
                type="monotone"
                dataKey="nodes"
                stroke="transparent"
                fill="url(#nodeGradient)"
                animationBegin={0}
                animationDuration={isAnimated ? 1500 : 0}
              />

              <Line
                type="monotone"
                dataKey="nodes"
                stroke="#f97316"
                strokeWidth={3}
                dot={{ fill: '#f97316', strokeWidth: 0, r: 4 }}
                activeDot={{ r: 6, fill: '#fb923c', stroke: '#fff', strokeWidth: 2 }}
                animationBegin={0}
                animationDuration={isAnimated ? 1500 : 0}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Growth Stats */}
        <div className="mt-4 pt-3 border-t border-slate-700 grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-slate-500 uppercase">Start</div>
            <div className="text-lg font-bold text-slate-300">{nodeData[0]?.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase">Current</div>
            <div className="text-lg font-bold text-orange-400">{nodeData[nodeData.length - 1]?.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase">Growth</div>
            <div className="text-lg font-bold text-green-400">
              +{(((nodeData[nodeData.length - 1] - nodeData[0]) / nodeData[0]) * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Governance Participation Bar Chart
// ============================================================================

interface GovernanceChartProps {
  data?: GovernanceDataPoint[]
  animated?: boolean
}

function GovernanceChart({
  data = DEFAULT_GOVERNANCE_DATA,
  animated = true
}: GovernanceChartProps) {
  const [isAnimated, setIsAnimated] = useState(false)

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => setIsAnimated(true), 100)
      return () => clearTimeout(timer)
    }
  }, [animated])

  const maxCommitted = Math.max(...data.map(d => d.committed)) * 1.1

  return (
    <Card className="border-slate-700 bg-slate-900/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          Governance Participation
        </CardTitle>
        <CardDescription>
          ALGO committed per governance period (millions)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity={1}/>
                  <stop offset="100%" stopColor="#0891b2" stopOpacity={0.8}/>
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />

              <XAxis
                dataKey="period"
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: '#475569' }}
              />

              <YAxis
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                domain={[0, maxCommitted]}
                tickFormatter={(value) => `${(value / 1000).toFixed(1)}B`}
                axisLine={{ stroke: '#475569' }}
              />

              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(value: number) => [`${value.toLocaleString()}M ALGO`, 'Committed']}
              />

              <Bar
                dataKey="committed"
                fill="url(#barGradient)"
                radius={[4, 4, 0, 0]}
                animationBegin={0}
                animationDuration={isAnimated ? 1200 : 0}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Summary Stats */}
        <div className="mt-4 pt-3 border-t border-slate-700 flex justify-between text-sm">
          <div className="text-slate-400">
            Latest Period: <span className="text-cyan-400 font-semibold">{data[data.length - 1]?.committed.toLocaleString()}M ALGO</span>
          </div>
          <div className="text-slate-400">
            Avg: <span className="text-slate-300 font-semibold">
              {(data.reduce((sum, d) => sum + d.committed, 0) / data.length).toFixed(0)}M ALGO
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Combined Chart Grid Component
// ============================================================================

export function DecentralizationCharts({
  foundationStake,
  communityStake,
  nodeData,
  governanceData,
  className = ''
}: DecentralizationChartsProps) {
  return (
    <div className={`grid md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
      <StakeDonutChart
        foundationStake={foundationStake}
        communityStake={communityStake}
      />
      <NodeGrowthChart nodeData={nodeData} />
      <GovernanceChart data={governanceData} />
    </div>
  )
}

// ============================================================================
// Individual Chart Exports
// ============================================================================

export { StakeDonutChart, NodeGrowthChart, GovernanceChart }
export type { DecentralizationChartsProps, GovernanceDataPoint }
