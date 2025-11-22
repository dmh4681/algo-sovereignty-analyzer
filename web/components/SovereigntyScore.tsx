'use client'

import { Card } from '@/components/ui/card'
import { formatUSD, formatNumber } from '@/lib/utils'
import { SovereigntyData } from '@/lib/types'

interface SovereigntyScoreProps {
  data: SovereigntyData
}

export function SovereigntyScore({ data }: SovereigntyScoreProps) {
  const { sovereignty_ratio, sovereignty_status, portfolio_usd, annual_fixed_expenses } = data

  // Determine the background gradient based on status
  const getGradient = () => {
    if (sovereignty_status.includes('Generationally')) {
      return 'from-emerald-600 to-emerald-800'
    }
    if (sovereignty_status.includes('Antifragile')) {
      return 'from-green-500 to-green-700'
    }
    if (sovereignty_status.includes('Robust')) {
      return 'from-yellow-500 to-yellow-700'
    }
    if (sovereignty_status.includes('Fragile')) {
      return 'from-red-500 to-red-700'
    }
    return 'from-slate-600 to-slate-800'
  }

  return (
    <Card className={`bg-gradient-to-br ${getGradient()} border-0 overflow-hidden`}>
      <div className="p-8 text-center">
        <div className="text-sm uppercase tracking-wider text-white/80 mb-2">
          Sovereignty Score
        </div>
        <div className="text-6xl md:text-7xl font-bold text-white mb-2 tabular-nums">
          {formatNumber(sovereignty_ratio, 1)}
          <span className="text-3xl md:text-4xl ml-2">years</span>
        </div>
        <div className="text-2xl md:text-3xl text-white/90 mb-4">
          {sovereignty_status}
        </div>
        <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-white/20">
          <div>
            <div className="text-white/70 text-sm">Portfolio Value</div>
            <div className="text-xl font-semibold text-white tabular-nums">
              {formatUSD(portfolio_usd)}
            </div>
          </div>
          <div>
            <div className="text-white/70 text-sm">Annual Expenses</div>
            <div className="text-xl font-semibold text-white tabular-nums">
              {formatUSD(annual_fixed_expenses)}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

interface SovereigntyScoreMiniProps {
  ratio: number
  status: string
  portfolioUSD: number
}

export function SovereigntyScoreMini({ ratio, status, portfolioUSD }: SovereigntyScoreMiniProps) {
  const getColor = () => {
    if (status.includes('Generationally')) return 'text-emerald-500'
    if (status.includes('Antifragile')) return 'text-green-500'
    if (status.includes('Robust')) return 'text-yellow-500'
    if (status.includes('Fragile')) return 'text-red-500'
    return 'text-slate-500'
  }

  return (
    <div className="flex items-center gap-4 p-4 bg-slate-800/50 rounded-lg">
      <div className={`text-3xl font-bold tabular-nums ${getColor()}`}>
        {formatNumber(ratio, 1)}y
      </div>
      <div className="text-sm">
        <div className={getColor()}>{status}</div>
        <div className="text-slate-400">{formatUSD(portfolioUSD)}</div>
      </div>
    </div>
  )
}
