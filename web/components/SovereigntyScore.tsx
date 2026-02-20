'use client'

import { Card } from '@/components/ui/card'
import { formatUSD, formatNumber } from '@/lib/utils'
import { SovereigntyData } from '@/lib/types'
import { TreasureChest } from '@/components/illustrations'

/**
 * Props for the {@link SovereigntyScore} component.
 *
 * @property data - The sovereignty calculation results including ratio, status,
 *   portfolio value, and annual expenses. Sourced from the `/analyze` API response
 *   or calculated client-side via `calculateSovereigntyMetrics()`.
 */
interface SovereigntyScoreProps {
  data: SovereigntyData
}

/**
 * Maps a sovereignty status string to a mining-themed display name and emoji.
 *
 * The mining theme is used throughout the UI to gamify the sovereignty journey:
 * - Generationally Sovereign -> "Dragon's Hoard"
 * - Antifragile -> "King's Treasury"
 * - Robust -> "Merchant's Chest"
 * - Fragile -> "Miner's Pouch"
 * - Vulnerable -> "Empty Mine"
 *
 * @param status - The sovereignty status string (e.g., "Robust", "Antifragile")
 * @returns An object with `title` (mining theme name) and `emoji` for display
 */
const getMiningStatus = (status: string): { title: string; emoji: string } => {
  if (status.includes('Generationally')) {
    return { title: "Dragon's Hoard", emoji: '🐉' }
  }
  if (status.includes('Antifragile')) {
    return { title: "King's Treasury", emoji: '👑' }
  }
  if (status.includes('Robust')) {
    return { title: "Merchant's Chest", emoji: '🪙' }
  }
  if (status.includes('Fragile')) {
    return { title: "Miner's Pouch", emoji: '⛏️' }
  }
  return { title: 'Empty Mine', emoji: '🪨' }
}

/**
 * Displays the sovereignty score as a large, visually prominent card with a
 * tier-based gradient background. This is the primary "hero" element on the
 * analysis dashboard.
 *
 * The component renders:
 * - The sovereignty ratio as years of financial runway (e.g., "3.5 years")
 * - A mining-themed status name (e.g., "Merchant's Chest") with emoji
 * - The formal status label (e.g., "Robust")
 * - Portfolio total value and annual expenses in a 2-column grid
 * - A decorative TreasureChest illustration (opens when ratio > 3)
 *
 * Background gradients change based on sovereignty tier:
 * - Generationally Sovereign: emerald gradient
 * - Antifragile: green gradient
 * - Robust: yellow/amber gradient
 * - Fragile: red gradient
 * - Vulnerable: stone/gray gradient
 *
 * Accessibility: Uses `role="meter"` with `aria-valuenow`, `aria-valuemin`,
 * and `aria-valuemax` for screen reader support.
 *
 * @param props - Component props
 * @param props.data - SovereigntyData with ratio, status, portfolio value, and expenses
 *
 * @example
 * ```tsx
 * <SovereigntyScore data={{
 *   sovereignty_ratio: 3.5,
 *   sovereignty_status: "Robust",
 *   portfolio_usd: 210000,
 *   annual_fixed_expenses: 60000,
 *   monthly_fixed_expenses: 5000,
 *   algo_price: 0.42,
 *   years_of_runway: 3.5
 * }} />
 * ```
 */
export function SovereigntyScore({ data }: SovereigntyScoreProps) {
  const { sovereignty_ratio, sovereignty_status, portfolio_usd, annual_fixed_expenses } = data
  const miningStatus = getMiningStatus(sovereignty_status)

  // Determine the background gradient based on status
  const getGradient = () => {
    if (sovereignty_status.includes('Generationally')) {
      return 'from-emerald-600 to-emerald-900'
    }
    if (sovereignty_status.includes('Antifragile')) {
      return 'from-green-600 to-green-900'
    }
    if (sovereignty_status.includes('Robust')) {
      return 'from-yellow-600 to-amber-900'
    }
    if (sovereignty_status.includes('Fragile')) {
      return 'from-red-600 to-red-900'
    }
    return 'from-stone-600 to-stone-900'
  }

  return (
    <Card className={`bg-gradient-to-br ${getGradient()} border-0 overflow-hidden relative`}>
      {/* Decorative treasure chest */}
      <div className="absolute -right-8 -bottom-8 opacity-20" aria-hidden="true">
        <TreasureChest size={150} open={sovereignty_ratio > 3} animated={false} />
      </div>
      <div className="p-8 text-center relative z-10">
        <div className="text-sm uppercase tracking-wider text-white/80 mb-2 flex items-center justify-center gap-2">
          <span aria-hidden="true">⛏️</span>
          <span>Sovereignty Score</span>
          <span aria-hidden="true">⛏️</span>
        </div>
        <div
          role="meter"
          aria-valuenow={sovereignty_ratio}
          aria-valuemin={0}
          aria-valuemax={20}
          aria-label={`Sovereignty Score: ${formatNumber(sovereignty_ratio, 1)} years of financial independence`}
          className="text-6xl md:text-7xl font-bold text-white mb-2 tabular-nums"
        >
          {formatNumber(sovereignty_ratio, 1)}
          <span className="text-3xl md:text-4xl ml-2">years</span>
        </div>
        <div className="text-2xl md:text-3xl text-white/90 mb-2 flex items-center justify-center gap-2">
          <span className="text-3xl">{miningStatus.emoji}</span>
          <span>{miningStatus.title}</span>
        </div>
        <div className="text-sm text-white/60 mb-4">
          ({sovereignty_status})
        </div>
        <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-white/20">
          <div>
            <div className="text-white/70 text-sm">Treasure Hoard</div>
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

/**
 * Props for the {@link SovereigntyScoreMini} compact display component.
 *
 * @property ratio - The sovereignty ratio (years of runway)
 * @property status - The sovereignty status string (e.g., "Robust")
 * @property portfolioUSD - Total portfolio value in USD
 */
interface SovereigntyScoreMiniProps {
  ratio: number
  status: string
  portfolioUSD: number
}

/**
 * A compact, inline version of the sovereignty score for use in headers,
 * summaries, or sidebar contexts. Displays the ratio, mining theme name,
 * and portfolio value in a single row.
 *
 * Color-coded text matches the sovereignty tier (emerald for top tier,
 * stone for vulnerable).
 *
 * @param props - Component props
 * @param props.ratio - Sovereignty ratio as a number (years)
 * @param props.status - Sovereignty status label
 * @param props.portfolioUSD - Total portfolio value in USD
 */
export function SovereigntyScoreMini({ ratio, status, portfolioUSD }: SovereigntyScoreMiniProps) {
  const miningStatus = getMiningStatus(status)

  const getColor = () => {
    if (status.includes('Generationally')) return 'text-emerald-400'
    if (status.includes('Antifragile')) return 'text-green-400'
    if (status.includes('Robust')) return 'text-yellow-400'
    if (status.includes('Fragile')) return 'text-red-400'
    return 'text-stone-400'
  }

  return (
    <div className="flex items-center gap-4 p-4 bg-stone-800/50 rounded-lg border border-amber-900/30">
      <div className="text-2xl">{miningStatus.emoji}</div>
      <div className={`text-3xl font-bold tabular-nums ${getColor()}`}>
        {formatNumber(ratio, 1)}y
      </div>
      <div className="text-sm">
        <div className={getColor()}>{miningStatus.title}</div>
        <div className="text-amber-200/50">{formatUSD(portfolioUSD)}</div>
      </div>
    </div>
  )
}
