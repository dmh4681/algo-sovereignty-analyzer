'use client'

import { useState, useMemo } from 'react'
import { Calculator, TrendingUp, Target } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { formatUSD, formatNumber } from '@/lib/utils'
import { calculateSovereigntyMetrics } from '@/lib/api'

/**
 * Props for the {@link RunwayCalculator} component.
 *
 * @property portfolioUSD - Total portfolio value in USD across all asset categories.
 *   Used as the numerator in the sovereignty ratio calculation.
 * @property algoPrice - Current ALGO price in USD. Used to calculate how many
 *   ALGO tokens are needed to reach the next sovereignty milestone.
 * @property initialExpenses - Pre-filled monthly expense value (e.g., from URL params
 *   or previous calculation). Defaults to 0 (empty input).
 * @property onUpdate - Callback invoked with the new monthly expense value when the
 *   user recalculates. Allows the parent to update URL params or other state.
 */
interface RunwayCalculatorProps {
  portfolioUSD: number
  algoPrice: number
  initialExpenses?: number
  onUpdate?: (expenses: number) => void
}

/**
 * Interactive calculator that lets users input their monthly fixed expenses
 * to compute their sovereignty ratio and runway in real-time.
 *
 * The calculation is performed client-side using `calculateSovereigntyMetrics()`
 * from `@/lib/api`, which mirrors the backend's sovereignty formula:
 * `ratio = portfolioUSD / (monthlyExpenses * 12)`.
 *
 * Features:
 * - Minimum expense threshold of $1,000/month (auto-enforced)
 * - Enter key submission support
 * - Displays sovereignty ratio (years), status tier, and annual expenses
 * - Memoized calculation via `useMemo` to avoid unnecessary recomputation
 *
 * @param props - Component props
 *
 * @example
 * ```tsx
 * <RunwayCalculator
 *   portfolioUSD={180000}
 *   algoPrice={0.42}
 *   initialExpenses={5000}
 *   onUpdate={(expenses) => updateURLParams({ expenses })}
 * />
 * ```
 */
export function RunwayCalculator({
  portfolioUSD,
  algoPrice,
  initialExpenses = 0,
  onUpdate
}: RunwayCalculatorProps) {
  const [expenses, setExpenses] = useState(initialExpenses || '')
  const [calculatedExpenses, setCalculatedExpenses] = useState<number | null>(
    initialExpenses && initialExpenses > 0 ? initialExpenses : null
  )

  const metrics = useMemo(() => {
    if (calculatedExpenses && calculatedExpenses > 0) {
      return calculateSovereigntyMetrics(portfolioUSD, calculatedExpenses, algoPrice)
    }
    return null
  }, [calculatedExpenses, portfolioUSD, algoPrice])

  const handleCalculate = () => {
    const expenseValue = typeof expenses === 'string' ? parseFloat(expenses) : expenses
    if (expenseValue >= 1000) {
      setCalculatedExpenses(expenseValue)
      onUpdate?.(expenseValue)
    } else if (expenseValue > 0) {
      // Enforce minimum of $1000
      setCalculatedExpenses(1000)
      setExpenses(1000)
      onUpdate?.(1000)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCalculate()
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5 text-orange-500" />
          Calculate Your Runway
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm text-slate-400 mb-2 block">
            Monthly Fixed Expenses (USD)
          </label>
          <div className="flex gap-3">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">$</span>
              <Input
                type="number"
                placeholder="4000"
                value={expenses}
                onChange={(e) => setExpenses(e.target.value)}
                onKeyDown={handleKeyDown}
                className="pl-7"
                min="1000"
                step="100"
              />
            </div>
            <Button onClick={handleCalculate}>
              Calculate
            </Button>
          </div>
        </div>

        {metrics && (
          <div className="space-y-4 pt-4 border-t border-slate-800">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Sovereignty Ratio</div>
                <div className="text-2xl font-bold text-orange-500 tabular-nums">
                  {formatNumber(metrics.ratio, 1)} years
                </div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Status</div>
                <div className="text-xl font-semibold">
                  {metrics.status}
                </div>
              </div>
            </div>

            <div className="text-sm text-slate-400">
              <TrendingUp className="inline h-4 w-4 mr-1" />
              Annual Expenses: {formatUSD(metrics.annualExpenses)}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Props for the {@link NextMilestone} component.
 *
 * @property portfolioUSD - Current total portfolio value in USD
 * @property monthlyExpenses - User's monthly fixed expenses in USD
 * @property algoPrice - Current ALGO price in USD for ALGO-needed calculations
 */
interface NextMilestoneProps {
  portfolioUSD: number
  monthlyExpenses: number
  algoPrice: number
}

/**
 * Displays progress toward the next sovereignty tier with a visual progress bar.
 *
 * Uses `calculateSovereigntyMetrics()` to determine the next milestone and
 * calculates:
 * - Target tier name and required ratio
 * - USD amount needed to reach the next tier
 * - Equivalent ALGO tokens needed at current price
 * - Visual progress bar showing percentage toward the goal
 *
 * If the user has already reached "Generationally Sovereign" (20+ years),
 * shows a congratulatory message instead of a milestone target.
 *
 * @param props - Component props
 *
 * @example
 * ```tsx
 * <NextMilestone
 *   portfolioUSD={180000}
 *   monthlyExpenses={5000}
 *   algoPrice={0.42}
 * />
 * ```
 */
export function NextMilestone({ portfolioUSD, monthlyExpenses, algoPrice }: NextMilestoneProps) {
  const metrics = calculateSovereigntyMetrics(portfolioUSD, monthlyExpenses, algoPrice)

  if (!metrics.nextMilestone) {
    return (
      <Card className="border-emerald-500/50 bg-emerald-500/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-emerald-500">
            <Target className="h-5 w-5" />
            Maximum Sovereignty
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-300">
            Congratulations! You&apos;ve achieved Generational Sovereignty.
          </p>
          <p className="text-slate-400 text-sm mt-2">
            Your portfolio can sustain 20+ years of expenses. You have true financial freedom.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-orange-500" />
          Next Milestone
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-slate-300">
          To reach <span className="font-semibold">{metrics.nextMilestone.target}</span>{' '}
          ({metrics.nextMilestone.ratio} years):
        </p>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-sm text-slate-400 mb-1">USD Needed</div>
            <div className="text-xl font-bold text-orange-500 tabular-nums">
              {formatUSD(metrics.nextMilestone.needed)}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-sm text-slate-400 mb-1">ALGO Needed</div>
            <div className="text-xl font-bold text-slate-200 tabular-nums">
              {formatNumber(metrics.neededAlgo, 0)}
            </div>
            <div className="text-xs text-slate-500">@ {formatUSD(algoPrice)}</div>
          </div>
        </div>

        <div className="text-sm text-slate-500">
          Progress: {formatNumber((portfolioUSD / (metrics.nextMilestone.ratio * metrics.annualExpenses)) * 100, 0)}%
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-orange-500 transition-all duration-500"
            style={{
              width: `${Math.min((portfolioUSD / (metrics.nextMilestone.ratio * metrics.annualExpenses)) * 100, 100)}%`
            }}
          />
        </div>
      </CardContent>
    </Card>
  )
}
