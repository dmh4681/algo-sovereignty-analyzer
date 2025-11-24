'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { ArrowLeft, CheckCircle2, Circle, Clock, RefreshCw, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { SearchBar } from '@/components/SearchBar'
import { NodeStatusCard } from '@/components/NodeStatusCard'

// ... (existing imports)



import { SovereigntyScore } from '@/components/SovereigntyScore'
import { AssetBreakdown, AssetBreakdownSummary } from '@/components/AssetBreakdown'
import { RunwayCalculator, NextMilestone } from '@/components/RunwayCalculator'
import { LoadingSpinner, LoadingState } from '@/components/LoadingState'
import { HistoryChart } from '@/components/HistoryChart'
import { BadgeSection } from '@/components/BadgeSection'
import { analyzeWallet, ApiError } from '@/lib/api'
import { AnalysisResponse } from '@/lib/types'
import { truncateAddress } from '@/lib/utils'

function AnalyzeContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expenses, setExpenses] = useState<number | null>(null)

  const address = searchParams.get('address') || ''
  const expensesParam = searchParams.get('expenses')

  useEffect(() => {
    if (expensesParam) {
      setExpenses(parseFloat(expensesParam))
    }
  }, [expensesParam])

  useEffect(() => {
    async function doFetch() {
      if (address && address.length === 58) {
        setLoading(true)
        setError(null)
        try {
          const data = await analyzeWallet({
            address,
            monthly_fixed_expenses: expenses || undefined,
          })
          setAnalysis(data)
        } catch (err) {
          if (err instanceof ApiError) {
            setError(err.message)
          } else {
            setError('Failed to analyze wallet. Please try again.')
          }
        } finally {
          setLoading(false)
        }
      }
    }
    doFetch()
  }, [address, expenses])

  const fetchAnalysis = async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await analyzeWallet({
        address,
        monthly_fixed_expenses: expenses || undefined,
      })
      setAnalysis(data)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to analyze wallet. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleExpenseUpdate = async (newExpenses: number) => {
    setExpenses(newExpenses)
    // Update URL
    const params = new URLSearchParams(searchParams.toString())
    params.set('expenses', newExpenses.toString())
    router.replace(`/analyze?${params.toString()}`, { scroll: false })

    // Re-fetch with new expenses
    setLoading(true)
    try {
      const data = await analyzeWallet({
        address,
        monthly_fixed_expenses: newExpenses,
      })
      setAnalysis(data)
    } catch (err) {
      console.error('Failed to update analysis:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleNewAnalysis = (newAddress: string) => {
    router.push(`/analyze?address=${encodeURIComponent(newAddress)}${expenses ? `&expenses=${expenses}` : ''}`)
  }

  if (!address) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-8">
        <h1 className="text-3xl font-bold">Analyze a Wallet</h1>
        <p className="text-slate-400">Enter an Algorand address to get started</p>
        <SearchBar onAnalyze={handleNewAnalysis} />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-xl font-semibold">
              Analyzing: <span className="font-mono text-orange-500">{truncateAddress(address)}</span>
            </h1>
            {analysis && (
              <div className="flex items-center gap-4 text-sm text-slate-400 mt-1">
                <span className="flex items-center gap-1">
                  {analysis.is_participating ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span className="text-green-500">PARTICIPATING</span>
                    </>
                  ) : (
                    <>
                      <Circle className="h-4 w-4 text-slate-500" />
                      <span>OFFLINE</span>
                    </>
                  )}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {new Date().toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchAnalysis}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Analysis Failed</AlertTitle>
          <AlertDescription>
            {error === 'Wallet not found or empty'
              ? 'This wallet was not found or has no assets. Please check the address and try again.'
              : error}
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {loading && !analysis && <LoadingSpinner text="Fetching wallet data from Algorand..." />}

      {/* Analysis Results */}
      {analysis && !loading && (
        <div className="space-y-8">
          {/* Sovereignty Score (if expenses provided) */}
          {analysis.sovereignty_data && (
            <SovereigntyScore data={analysis.sovereignty_data} />
          )}



          {/* Quick Summary */}
          {!analysis.sovereignty_data && (
            <Card className="bg-gradient-to-br from-slate-800 to-slate-900">
              <CardContent className="py-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold mb-2">Portfolio Overview</h2>
                    <AssetBreakdownSummary categories={analysis.categories} />
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-400">Hard Money ALGO</div>
                    <div className="text-3xl font-bold text-orange-500 tabular-nums">
                      {(() => {
                        // Calculate ALGO equivalent of hard money assets
                        const hardMoneyValue = analysis.categories.hard_money.reduce((sum, a) => sum + a.usd_value, 0)
                        // Get ALGO price from ALGO holdings or use fallback
                        const algoAsset = analysis.categories.algo.find(a => a.ticker === 'ALGO')
                        const algoPrice = algoAsset && algoAsset.amount > 0 && algoAsset.usd_value > 0
                          ? algoAsset.usd_value / algoAsset.amount
                          : 0.15 // fallback price
                        const hardMoneyAlgo = algoPrice > 0 ? hardMoneyValue / algoPrice : 0
                        return hardMoneyAlgo.toLocaleString(undefined, { maximumFractionDigits: 0 })
                      })()} ALGO
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Asset Breakdown */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Asset Breakdown</h2>
            <AssetBreakdown categories={analysis.categories} />
          </section>

          {/* Node Status */}
          <section>
            <NodeStatusCard
              isParticipating={analysis.is_participating}
              participationInfo={analysis.participation_info}
            />
          </section>

          {/* History Chart */}
          <section>
            <HistoryChart address={address} monthlyExpenses={expenses || undefined} />
          </section>

          {/* Badge Section */}
          {analysis.sovereignty_data && (
            <section>
              {(() => {
                const hardMoneyValue = analysis.categories.hard_money.reduce((sum, a) => sum + a.usd_value, 0)
                const algoValue = analysis.categories.algo.reduce((sum, a) => sum + a.usd_value, 0)
                const dollarsValue = analysis.categories.dollars.reduce((sum, a) => sum + a.usd_value, 0)
                const shitcoinValue = analysis.categories.shitcoin.reduce((sum, a) => sum + a.usd_value, 0)
                const totalValue = hardMoneyValue + algoValue + dollarsValue + shitcoinValue
                const hardMoneyPercentage = totalValue > 0 ? (hardMoneyValue / totalValue) * 100 : 0

                return (
                  <BadgeSection
                    sovereigntyRatio={analysis.sovereignty_data!.sovereignty_ratio}
                    hardMoneyPercentage={hardMoneyPercentage}
                  />
                )
              })()}
            </section>
          )}

          {/* Calculator Section */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <RunwayCalculator
              portfolioUSD={analysis.sovereignty_data?.portfolio_usd ||
                (analysis.categories.hard_money.reduce((sum, a) => sum + a.usd_value, 0) +
                  analysis.categories.algo.reduce((sum, a) => sum + a.usd_value, 0) +
                  analysis.categories.dollars.reduce((sum, a) => sum + a.usd_value, 0) +
                  analysis.categories.shitcoin.reduce((sum, a) => sum + a.usd_value, 0))}
              algoPrice={analysis.sovereignty_data?.algo_price || 0.174}
              initialExpenses={expenses || undefined}
              onUpdate={handleExpenseUpdate}
            />

            {analysis.sovereignty_data && expenses && (
              <NextMilestone
                portfolioUSD={analysis.sovereignty_data.portfolio_usd}
                monthlyExpenses={expenses}
                algoPrice={analysis.sovereignty_data.algo_price}
              />
            )}

            {!analysis.sovereignty_data && (
              <Card className="border-orange-500/30 bg-orange-500/5">
                <CardHeader>
                  <CardTitle className="text-orange-500">Enter Your Expenses</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-400 text-sm">
                    Enter your monthly fixed expenses to calculate your sovereignty ratio and see how long your portfolio can sustain your lifestyle.
                  </p>
                </CardContent>
              </Card>
            )}
          </section>

          {/* Analyze Another Wallet */}
          <section className="pt-8 border-t border-slate-800">
            <h2 className="text-lg font-semibold mb-4 text-center">Analyze Another Wallet</h2>
            <div className="max-w-xl mx-auto">
              <SearchBar onAnalyze={handleNewAnalysis} showExamples={false} />
            </div>
          </section>
        </div>
      )}

      {/* Empty Loading State */}
      {loading && analysis && (
        <div className="absolute inset-0 bg-slate-950/50 flex items-center justify-center">
          <LoadingSpinner text="Updating analysis..." />
        </div>
      )}
    </div>
  )
}

export default function AnalyzePage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <AnalyzeContent />
    </Suspense>
  )
}
