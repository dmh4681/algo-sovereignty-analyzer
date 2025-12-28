'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, TrendingUp, TrendingDown, Minus, AlertTriangle, ExternalLink } from 'lucide-react'
import { getMeldArbitrage } from '@/lib/api'
import type { MeldArbitrageResponse, ArbitrageMetalData, ArbitrageMetalError, ArbitrageBitcoinData, BitcoinTokenData } from '@/lib/types'
import { BitcoinArbitrageCard } from './BitcoinArbitrageCard'

// ============================================================================
// Helper Functions
// ============================================================================

function isArbitrageData(data: ArbitrageMetalData | ArbitrageMetalError | null): data is ArbitrageMetalData {
  return data !== null && 'signal' in data
}

function isBitcoinData(data: ArbitrageBitcoinData | ArbitrageMetalError | null): data is ArbitrageBitcoinData {
  return data !== null && 'spot_price' in data && 'gobtc' in data
}

function isTokenData(token: BitcoinTokenData | { error: string } | undefined): token is BitcoinTokenData {
  return token !== undefined && 'price' in token && 'signal' in token
}

function getSignalColor(signal: string): string {
  switch (signal) {
    case 'STRONG_BUY':
      return 'bg-green-500 text-white'
    case 'BUY':
      return 'bg-green-400 text-white'
    case 'HOLD':
      return 'bg-slate-500 text-white'
    case 'SELL':
      return 'bg-orange-500 text-white'
    case 'STRONG_SELL':
      return 'bg-red-500 text-white'
    default:
      return 'bg-slate-500 text-white'
  }
}

function getSignalGlow(signal: string): string {
  switch (signal) {
    case 'STRONG_BUY':
      return 'shadow-green-500/50 shadow-lg'
    case 'BUY':
      return 'shadow-green-400/30 shadow-md'
    case 'HOLD':
      return ''
    case 'SELL':
      return 'shadow-orange-500/30 shadow-md'
    case 'STRONG_SELL':
      return 'shadow-red-500/50 shadow-lg'
    default:
      return ''
  }
}

function getSignalIcon(signal: string) {
  switch (signal) {
    case 'STRONG_BUY':
    case 'BUY':
      return <TrendingUp className="h-5 w-5" />
    case 'SELL':
    case 'STRONG_SELL':
      return <TrendingDown className="h-5 w-5" />
    default:
      return <Minus className="h-5 w-5" />
  }
}

function getSignalDescription(signal: string, metal: string): string {
  const meldToken = metal === 'gold' ? 'GOLD$' : 'SILVER$'
  switch (signal) {
    case 'STRONG_BUY':
      return `${meldToken} trading significantly below spot. Strong buy opportunity.`
    case 'BUY':
      return `${meldToken} trading below spot. Consider accumulating.`
    case 'HOLD':
      return `${meldToken} trading near fair value. No clear arbitrage.`
    case 'SELL':
      return `${meldToken} trading above spot. Consider taking profits.`
    case 'STRONG_SELL':
      return `${meldToken} trading significantly above spot. Strong sell signal.`
    default:
      return 'Unable to determine signal.'
  }
}

function formatPremium(pct: number): string {
  const sign = pct >= 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

// ============================================================================
// Metal Card Component
// ============================================================================

interface MetalCardProps {
  metal: 'gold' | 'silver'
  data: ArbitrageMetalData | ArbitrageMetalError | null
  loading: boolean
}

function MetalCard({ metal, data, loading }: MetalCardProps) {
  const isGold = metal === 'gold'
  const icon = isGold ? '🥇' : '🥈'
  const title = isGold ? 'Gold' : 'Silver'
  const meldToken = isGold ? 'GOLD$' : 'SILVER$'
  const meldAsa = isGold ? '246516580' : '246519683'

  // Loading state
  if (loading) {
    return (
      <Card className="border-slate-700 animate-pulse">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">{icon}</span>
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="h-8 bg-slate-700 rounded w-24" />
            <div className="h-4 bg-slate-700 rounded w-32" />
            <div className="h-4 bg-slate-700 rounded w-28" />
          </div>
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (!data || !isArbitrageData(data)) {
    const errorData = data as ArbitrageMetalError | null
    return (
      <Card className="border-slate-700 border-red-500/30">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">{icon}</span>
            {title}
            <AlertTriangle className="h-4 w-4 text-red-400 ml-auto" />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-red-400">
            {errorData?.error || 'Unable to fetch price data'}
          </div>
          <div className="text-xs text-slate-500 mt-2">
            Spot: {errorData?.spot_available ? '✓' : '✗'} |
            Meld: {errorData?.meld_available ? '✓' : '✗'}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Normal state with data
  const { spot_per_oz, implied_per_gram, meld_price, premium_pct, signal, signal_strength } = data
  const premiumColor = premium_pct > 0 ? 'text-red-400' : premium_pct < 0 ? 'text-green-400' : 'text-slate-400'

  return (
    <Card className={`border-slate-700 transition-all duration-300 ${getSignalGlow(signal)}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">{icon}</span>
            {title}
          </CardTitle>
          <Badge className={`${getSignalColor(signal)} flex items-center gap-1`}>
            {getSignalIcon(signal)}
            {signal.replace('_', ' ')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Price Comparison */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wide">Spot (per oz)</div>
            <div className="text-lg font-bold text-slate-200">
              ${spot_per_oz.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wide">Implied (per g)</div>
            <div className="text-lg font-bold text-slate-200">
              ${implied_per_gram.toFixed(4)}
            </div>
          </div>
        </div>

        {/* Meld Price */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wide">Meld {meldToken}</div>
              <div className="text-xl font-bold text-orange-400">
                ${meld_price.toFixed(4)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-400 uppercase tracking-wide">Premium</div>
              <div className={`text-xl font-bold ${premiumColor}`}>
                {formatPremium(premium_pct)}
              </div>
            </div>
          </div>
        </div>

        {/* Signal Strength Bar */}
        {signal !== 'HOLD' && (
          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Signal Strength</span>
              <span>{signal_strength.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  signal.includes('BUY') ? 'bg-green-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, signal_strength)}%` }}
              />
            </div>
          </div>
        )}

        {/* Signal Description */}
        <div className="text-sm text-slate-400">
          {getSignalDescription(signal, metal)}
        </div>

        {/* Quick Links */}
        <div className="flex gap-2 pt-2">
          <a
            href={`https://app.tinyman.org/#/swap?asset_in=0&asset_out=${meldAsa}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-500 hover:text-orange-400 flex items-center gap-1"
          >
            Trade on Tinyman <ExternalLink className="h-3 w-3" />
          </a>
          <span className="text-slate-600">|</span>
          <a
            href="https://meld.gold"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-500 hover:text-orange-400 flex items-center gap-1"
          >
            Meld Gold <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Bitcoin Card Component (Fallback for loading/error states)
// ============================================================================

interface BitcoinCardProps {
  data: ArbitrageBitcoinData | ArbitrageMetalError | null
  loading: boolean
}

function BitcoinCard({ data, loading }: BitcoinCardProps) {
  const icon = '₿'
  const title = 'Bitcoin Arbitrage'

  // Loading state
  if (loading) {
    return (
      <Card className="border-slate-700 animate-pulse">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl text-orange-500">{icon}</span>
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="h-8 bg-slate-700 rounded w-full" />
            <div className="h-4 bg-slate-700 rounded w-3/4" />
            <div className="h-4 bg-slate-700 rounded w-1/2" />
          </div>
        </CardContent>
      </Card>
    )
  }

  // Error state (only shown when data doesn't match new structure)
  const errorData = data as ArbitrageMetalError | null
  return (
    <Card className="border-slate-700 border-red-500/30">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2">
          <span className="text-2xl text-orange-500">{icon}</span>
          {title}
          <AlertTriangle className="h-4 w-4 text-red-400 ml-auto" />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-red-400">
          {errorData?.error || 'Unable to fetch Bitcoin price data'}
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Main Component
// ============================================================================

interface MeldArbitrageSpotterProps {
  autoRefresh?: boolean
  refreshInterval?: number // in milliseconds
}

export function MeldArbitrageSpotter({
  autoRefresh = false,
  refreshInterval = 60000 // 1 minute default
}: MeldArbitrageSpotterProps) {
  const [data, setData] = useState<MeldArbitrageResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchArbitrageData = async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await getMeldArbitrage()
      setData(result)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Error fetching arbitrage data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchArbitrageData()
  }, [])

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(fetchArbitrageData, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval])

  // Check for any strong signals
  const hasStrongSignal = data && (
    (isArbitrageData(data.gold) && (data.gold.signal === 'STRONG_BUY' || data.gold.signal === 'STRONG_SELL')) ||
    (isArbitrageData(data.silver) && (data.silver.signal === 'STRONG_BUY' || data.silver.signal === 'STRONG_SELL')) ||
    (isBitcoinData(data.bitcoin) && isTokenData(data.bitcoin.gobtc) && (data.bitcoin.gobtc.signal === 'STRONG_BUY' || data.bitcoin.gobtc.signal === 'STRONG_SELL')) ||
    (isBitcoinData(data.bitcoin) && isTokenData(data.bitcoin.wbtc) && (data.bitcoin.wbtc.signal === 'STRONG_BUY' || data.bitcoin.wbtc.signal === 'STRONG_SELL'))
  )

  return (
    <Card className={`border-slate-700 ${hasStrongSignal ? 'border-orange-500/50' : ''}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-xl">
              Meld Arbitrage Spotter
              {hasStrongSignal && (
                <Badge className="bg-orange-500 text-white animate-pulse">
                  OPPORTUNITY
                </Badge>
              )}
            </CardTitle>
            <CardDescription className="mt-1">
              Compare Algorand wrapped assets to spot prices
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchArbitrageData}
            disabled={loading}
            className="border-slate-600 hover:border-orange-500"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        {lastUpdated && (
          <div className="text-xs text-slate-500 mt-2">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
        )}
      </CardHeader>

      <CardContent>
        {error ? (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-center">
            <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-2" />
            <div className="text-red-400 font-medium">Error Loading Data</div>
            <div className="text-sm text-slate-400 mt-1">{error}</div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchArbitrageData}
              className="mt-3"
            >
              Try Again
            </Button>
          </div>
        ) : (
          <>
            {/* Precious Metals Row */}
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <MetalCard
                metal="gold"
                data={data?.gold || null}
                loading={loading && !data}
              />
              <MetalCard
                metal="silver"
                data={data?.silver || null}
                loading={loading && !data}
              />
            </div>

            {/* Bitcoin 3-Way Comparison */}
            {data?.bitcoin && isBitcoinData(data.bitcoin) ? (
              <BitcoinArbitrageCard data={data.bitcoin} />
            ) : (
              <BitcoinCard
                data={data?.bitcoin || null}
                loading={loading && !data}
              />
            )}

            {/* Legend / Help */}
            <div className="mt-6 pt-4 border-t border-slate-700">
              <div className="text-xs text-slate-500 mb-2 font-medium">SIGNAL GUIDE</div>
              <div className="flex flex-wrap gap-2">
                <Badge className="bg-green-500 text-white text-xs">STRONG BUY</Badge>
                <span className="text-xs text-slate-400">&gt;6% discount</span>
                <span className="text-slate-600 mx-1">|</span>
                <Badge className="bg-green-400 text-white text-xs">BUY</Badge>
                <span className="text-xs text-slate-400">0.5-6% discount</span>
                <span className="text-slate-600 mx-1">|</span>
                <Badge className="bg-slate-500 text-white text-xs">HOLD</Badge>
                <span className="text-xs text-slate-400">±0.5%</span>
                <span className="text-slate-600 mx-1">|</span>
                <Badge className="bg-orange-500 text-white text-xs">SELL</Badge>
                <span className="text-xs text-slate-400">0.5-6% premium</span>
                <span className="text-slate-600 mx-1">|</span>
                <Badge className="bg-red-500 text-white text-xs">STRONG SELL</Badge>
                <span className="text-xs text-slate-400">&gt;6% premium</span>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="mt-4 text-xs text-slate-600 text-center">
              Data sources: Yahoo Finance (metals), Coinbase (BTC), Vestige API (on-chain). Not financial advice.
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export default MeldArbitrageSpotter
