'use client'

import { useEffect, useState, Suspense, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { ArrowLeft, CheckCircle2, Circle, Clock, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SearchBar } from '@/components/SearchBar'
import { NodeStatusCard } from '@/components/NodeStatusCard'

import { SovereigntyScore } from '@/components/SovereigntyScore'
import { AssetBreakdown, AssetBreakdownSummary } from '@/components/AssetBreakdown'
import { AssetList, AssetListSummary } from '@/components/AssetList'
import { RunwayCalculator, NextMilestone } from '@/components/RunwayCalculator'
import {
  LoadingSpinner,
  LoadingState,
  SovereigntyScoreSkeleton,
  CategorySummarySkeleton,
  SectionLoading
} from '@/components/LoadingState'
import { ErrorAlert } from '@/components/ErrorAlert'
import { HistoryChart } from '@/components/HistoryChart'
import { BadgeSection } from '@/components/BadgeSection'
import { CoachingPanel } from '@/components/CoachingPanel'
import GoldSilverRatio from '@/components/GoldSilverRatio'
import { MeldArbitrageSpotter } from '@/components/MeldArbitrageSpotter'
import Link from 'next/link'
import { analyzeWallet, getQuickSovereignty, ApiError } from '@/lib/api'
import { AnalysisResponse, QuickSovereigntyResponse, CategoryType, CATEGORY_CONFIGS } from '@/lib/types'
import { truncateAddress } from '@/lib/utils'

// Cache for storing analysis results per address
const analysisCache = new Map<string, { data: AnalysisResponse; timestamp: number }>()
const CACHE_TTL_MS = 15 * 60 * 1000 // 15 minutes

function getCachedAnalysis(address: string): AnalysisResponse | null {
  const cached = analysisCache.get(address)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
    return cached.data
  }
  return null
}

function setCachedAnalysis(address: string, data: AnalysisResponse) {
  analysisCache.set(address, { data, timestamp: Date.now() })
}

function AnalyzeContent() {
  const searchParams = useSearchParams()
  const router = useRouter()

  // Full analysis state (includes detailed asset breakdown)
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  // Quick sovereignty data (loaded first for fast display)
  const [quickData, setQuickData] = useState<QuickSovereigntyResponse | null>(null)

  // Loading states for progressive loading
  const [loadingQuick, setLoadingQuick] = useState(false)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expenses, setExpenses] = useState<number | null>(null)

  // Track if we should use progressive loading (for large wallets)
  const [useProgressiveLoading, setUseProgressiveLoading] = useState(false)

  const address = searchParams.get('address') || ''
  const expensesParam = searchParams.get('expenses')

  // Ref to prevent duplicate fetches
  const fetchingRef = useRef(false)

  useEffect(() => {
    if (expensesParam) {
      setExpenses(parseFloat(expensesParam))
    }
  }, [expensesParam])

  // Progressive loading: first fetch quick sovereignty data, then full details
  useEffect(() => {
    async function doFetch() {
      if (!address || address.length !== 58 || fetchingRef.current) return

      // Check cache first
      const cached = getCachedAnalysis(address)
      if (cached) {
        setAnalysis(cached)
        setQuickData(null)
        setUseProgressiveLoading(false)
        return
      }

      fetchingRef.current = true
      setError(null)

      try {
        // Step 1: Fetch quick sovereignty data first (fast)
        setLoadingQuick(true)
        const quick = await getQuickSovereignty(address, expenses || undefined)
        setQuickData(quick)
        setLoadingQuick(false)

        // Determine if we need progressive loading based on asset counts
        const totalAssets = Object.values(quick.asset_counts).reduce((sum, count) => sum + count, 0)
        const hasLargeCategories = Object.values(quick.needs_pagination).some(v => v)

        if (totalAssets > 50 || hasLargeCategories) {
          setUseProgressiveLoading(true)
        }

        // Step 2: Fetch full analysis (may be slower for large wallets)
        setLoadingDetails(true)
        const data = await analyzeWallet({
          address,
          monthly_fixed_expenses: expenses || undefined,
        })
        setAnalysis(data)
        setCachedAnalysis(address, data)
        setQuickData(null) // Clear quick data once we have full data
        setUseProgressiveLoading(false)

      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message)
        } else {
          setError('Failed to analyze wallet. Please try again.')
        }
      } finally {
        setLoadingQuick(false)
        setLoadingDetails(false)
        fetchingRef.current = false
      }
    }
    doFetch()
  }, [address, expenses])

  const fetchAnalysis = async (forceRefresh = false) => {
    if (forceRefresh) {
      // Clear cache for this address
      analysisCache.delete(address)
    }

    setLoadingQuick(true)
    setLoadingDetails(true)
    setError(null)
    setQuickData(null)

    try {
      // Fetch quick data first for immediate display
      const quick = await getQuickSovereignty(address, expenses || undefined)
      setQuickData(quick)
      setLoadingQuick(false)

      // Then fetch full details
      const data = await analyzeWallet({
        address,
        monthly_fixed_expenses: expenses || undefined,
      })
      setAnalysis(data)
      setCachedAnalysis(address, data)
      setQuickData(null)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to analyze wallet. Please try again.')
      }
    } finally {
      setLoadingQuick(false)
      setLoadingDetails(false)
    }
  }

  // Computed loading state
  const loading = loadingQuick || loadingDetails
  const hasQuickData = quickData !== null
  const hasFullData = analysis !== null

  const handleExpenseUpdate = async (newExpenses: number) => {
    setExpenses(newExpenses)
    // Update URL
    const params = new URLSearchParams(searchParams.toString())
    params.set('expenses', newExpenses.toString())
    router.replace(`/analyze?${params.toString()}`, { scroll: false })

    // Clear cache and re-fetch with new expenses
    analysisCache.delete(address)
    setLoadingDetails(true)
    try {
      const data = await analyzeWallet({
        address,
        monthly_fixed_expenses: newExpenses,
      })
      setAnalysis(data)
      setCachedAnalysis(address, data)
    } catch (err) {
      console.error('Failed to update analysis:', err)
    } finally {
      setLoadingDetails(false)
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
            {(hasFullData || hasQuickData) && (
              <div className="flex items-center gap-4 text-sm text-slate-400 mt-1">
                <span className="flex items-center gap-1">
                  {(analysis?.is_participating || quickData?.is_participating) ? (
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
          onClick={() => fetchAnalysis(true)}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error State */}
      {error && (
        <ErrorAlert
          message={error === 'Wallet not found or empty'
            ? 'This wallet was not found or has no assets. Please check the address and try again.'
            : error}
          onRetry={() => fetchAnalysis(true)}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Loading State - Show different states based on progressive loading */}
      {loadingQuick && !hasQuickData && !hasFullData && (
        <LoadingSpinner text="Fetching wallet data from Algorand..." />
      )}

      {/* Quick Data Display - Sovereignty Score First (Progressive Loading Stage 1) */}
      {hasQuickData && !hasFullData && (
        <div className="space-y-8 animate-in fade-in duration-300">
          {/* Quick Sovereignty Score */}
          {quickData.sovereignty_ratio !== null && quickData.sovereignty_status && (
            <SovereigntyScore
              data={{
                monthly_fixed_expenses: expenses || 0,
                annual_fixed_expenses: (expenses || 0) * 12,
                algo_price: quickData.algo_price,
                portfolio_usd: quickData.portfolio_usd,
                sovereignty_ratio: quickData.sovereignty_ratio,
                sovereignty_status: quickData.sovereignty_status,
                years_of_runway: quickData.years_of_runway || quickData.sovereignty_ratio
              }}
            />
          )}

          {/* Quick Portfolio Overview (no expenses) */}
          {quickData.sovereignty_ratio === null && (
            <Card className="bg-gradient-to-br from-slate-800 to-slate-900">
              <CardContent className="py-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold mb-2">Portfolio Overview</h2>
                    <div className="flex flex-wrap gap-4">
                      {CATEGORY_CONFIGS.map((config) => (
                        <div key={config.key} className="flex items-center gap-2">
                          <span>{config.emoji}</span>
                          <span className={`font-medium ${config.colorClass}`}>
                            {quickData.asset_counts[config.key as CategoryType]}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-400">Total Portfolio</div>
                    <div className="text-3xl font-bold text-orange-500 tabular-nums">
                      ${quickData.portfolio_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Category Summaries (Quick View) */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Asset Breakdown</h2>
              <span className="text-sm text-slate-400 flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-orange-500 animate-pulse" />
                Loading details...
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {CATEGORY_CONFIGS.map((config) => (
                <AssetListSummary
                  key={config.key}
                  category={config.key}
                  count={quickData.asset_counts[config.key as CategoryType]}
                  totalUsd={quickData.category_totals[config.key as CategoryType]}
                  isLoading={loadingDetails}
                />
              ))}
            </div>
          </section>

          {/* Node Status (quick data includes participation info) */}
          <section>
            <NodeStatusCard
              isParticipating={quickData.is_participating}
              participationInfo={quickData.participation_info}
            />
          </section>
        </div>
      )}

      {/* Full Analysis Results */}
      {hasFullData && !loadingQuick && (
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

          {/* Gold/Silver Ratio */}
          <section>
            <GoldSilverRatio />
          </section>

          {/* Meld Arbitrage Spotter */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Precious Metals Arbitrage</h2>
              <Link
                href="/arbitrage"
                className="text-sm text-orange-500 hover:text-orange-400 transition-colors flex items-center gap-1"
              >
                View Full Arbitrage Dashboard →
              </Link>
            </div>
            <MeldArbitrageSpotter />
          </section>

          {/* Node Status */}
          <section>
            <NodeStatusCard
              isParticipating={analysis.is_participating}
              participationInfo={analysis.participation_info}
            />
          </section>

          {/* History Chart */}
          {analysis.sovereignty_data && (
            <section>
              <HistoryChart
                address={address}
                currentRatio={analysis.sovereignty_data.sovereignty_ratio}
              />
            </section>
          )}

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

          {/* AI Sovereignty Coach */}
          {analysis.sovereignty_data && (
            <section>
              <CoachingPanel address={address} analysis={analysis} />
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

      {/* Overlay Loading State when refreshing */}
      {loadingDetails && hasFullData && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-center justify-center z-50">
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
