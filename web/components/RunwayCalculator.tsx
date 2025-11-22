'use client'

import { useState, useMemo } from 'react'
import { Calculator, TrendingUp, Target } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { formatUSD, formatNumber } from '@/lib/utils'
import { calculateSovereigntyMetrics } from '@/lib/api'

interface RunwayCalculatorProps {
  portfolioUSD: number
  algoPrice: number
  initialExpenses?: number
  onUpdate?: (expenses: number) => void
}

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
    if (expenseValue > 0) {
      setCalculatedExpenses(expenseValue)
      onUpdate?.(expenseValue)
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
                min="0"
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

interface NextMilestoneProps {
  portfolioUSD: number
  monthlyExpenses: number
  algoPrice: number
}

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
