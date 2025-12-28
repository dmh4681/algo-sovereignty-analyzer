'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, TrendingUp, TrendingDown, Minus, AlertTriangle, Zap, Info } from 'lucide-react'
import type { ArbitrageBitcoinData, BitcoinTokenData } from '@/lib/types'

// =============================================================================
// Types
// =============================================================================

interface BitcoinArbitrageCardProps {
  data: ArbitrageBitcoinData
  className?: string
}

type SignalType = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'

// =============================================================================
// Helper Components
// =============================================================================

function SignalBadge({ signal, strength }: { signal: SignalType; strength: number }) {
  const config: Record<SignalType, { bg: string; text: string; icon: React.ReactNode }> = {
    STRONG_BUY: { bg: 'bg-green-500/20', text: 'text-green-400', icon: <TrendingUp className="h-3 w-3" /> },
    BUY: { bg: 'bg-green-500/10', text: 'text-green-400', icon: <TrendingUp className="h-3 w-3" /> },
    HOLD: { bg: 'bg-slate-500/20', text: 'text-slate-400', icon: <Minus className="h-3 w-3" /> },
    SELL: { bg: 'bg-red-500/10', text: 'text-red-400', icon: <TrendingDown className="h-3 w-3" /> },
    STRONG_SELL: { bg: 'bg-red-500/20', text: 'text-red-400', icon: <TrendingDown className="h-3 w-3" /> },
  }

  const c = config[signal]
  return (
    <Badge className={`${c.bg} ${c.text} border-0 gap-1`}>
      {c.icon}
      {signal.replace('_', ' ')}
      {strength > 0 && <span className="opacity-70">({strength.toFixed(0)}%)</span>}
    </Badge>
  )
}

function PremiumDisplay({ premiumPct, premiumUsd }: { premiumPct: number; premiumUsd: number }) {
  const isDiscount = premiumPct < 0
  const color = isDiscount ? 'text-green-400' : premiumPct > 0 ? 'text-red-400' : 'text-slate-400'

  return (
    <div className="text-center">
      <div className={`text-lg font-bold ${color}`}>
        {premiumPct > 0 ? '+' : ''}{premiumPct.toFixed(2)}%
      </div>
      <div className="text-xs text-slate-500">
        {premiumUsd > 0 ? '+' : ''}${premiumUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
    </div>
  )
}

function isTokenData(data: BitcoinTokenData | { error: string }): data is BitcoinTokenData {
  return 'price' in data && !('error' in data && !('price' in data))
}

function TokenColumn({
  label,
  token,
  spotPrice
}: {
  label: string
  token: BitcoinTokenData | { error: string }
  spotPrice: number
}) {
  if (!isTokenData(token)) {
    return (
      <div className="flex-1 p-4 bg-slate-800/30 rounded-lg text-center">
        <div className="text-sm font-medium text-slate-400 mb-2">{label}</div>
        <div className="text-red-400 text-sm">Unavailable</div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4 bg-slate-800/30 rounded-lg">
      <div className="text-center mb-3">
        <div className="text-sm font-medium text-slate-400 mb-1">{label}</div>
        <div className="text-2xl font-bold text-slate-100">
          ${token.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
      </div>

      <div className="space-y-3">
        <PremiumDisplay premiumPct={token.premium_pct} premiumUsd={token.premium_usd} />

        <div className="flex justify-center">
          <SignalBadge signal={token.signal} strength={token.signal_strength} />
        </div>

        {token.liquidity_warning && (
          <div className="flex items-center gap-1 text-xs text-amber-400 justify-center">
            <AlertTriangle className="h-3 w-3" />
            Low liquidity
          </div>
        )}

        <a
          href={token.tinyman_url}
          target="_blank"
          rel="noopener noreferrer"
          className="block"
        >
          <Button size="sm" variant="outline" className="w-full border-slate-600 hover:border-orange-500 hover:text-orange-400">
            Trade on Tinyman
            <ExternalLink className="h-3 w-3 ml-1" />
          </Button>
        </a>
      </div>
    </div>
  )
}

// =============================================================================
// Main Component
// =============================================================================

export function BitcoinArbitrageCard({ data, className = '' }: BitcoinArbitrageCardProps) {
  const gobtcData = isTokenData(data.gobtc) ? data.gobtc : null
  const wbtcData = isTokenData(data.wbtc) ? data.wbtc : null

  return (
    <Card className={`border-slate-700 bg-slate-900/50 ${className}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">₿</span>
              Bitcoin Arbitrage Monitor
            </CardTitle>
            <CardDescription>
              Compare Coinbase spot vs Algorand wrapped tokens
            </CardDescription>
          </div>
          {data.best_opportunity && (
            <Badge className="bg-orange-500/20 text-orange-400 border border-orange-500/30">
              <Zap className="h-3 w-3 mr-1" />
              {data.best_opportunity.action === 'EQUAL' ? 'No Edge' : `${data.best_opportunity.action} ${data.best_opportunity.token}`}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Coinbase Spot Reference */}
        <div className="text-center p-3 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Coinbase Spot Price</div>
          <div className="text-3xl font-bold text-slate-100">
            ${data.spot_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-500">Reference price for arbitrage</div>
        </div>

        {/* 3-Way Comparison */}
        <div className="flex gap-4">
          <TokenColumn label="goBTC (Native)" token={data.gobtc} spotPrice={data.spot_price} />
          <TokenColumn label="WBTC (Wormhole)" token={data.wbtc} spotPrice={data.spot_price} />
        </div>

        {/* Cross-DEX Spread */}
        {data.cross_dex_spread && gobtcData && wbtcData && (
          <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4 text-slate-500" />
                <span className="text-sm text-slate-400">Cross-DEX Spread</span>
              </div>
              <div className="text-sm">
                <span className={data.cross_dex_spread.gobtc_vs_wbtc_pct < 0 ? 'text-green-400' : 'text-red-400'}>
                  {data.cross_dex_spread.gobtc_vs_wbtc_pct > 0 ? '+' : ''}
                  {data.cross_dex_spread.gobtc_vs_wbtc_pct.toFixed(2)}%
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {data.cross_dex_spread.description}
            </p>
          </div>
        )}

        {/* Best Opportunity Callout */}
        {data.best_opportunity && data.best_opportunity.action !== 'EQUAL' && (
          <div className="p-4 bg-gradient-to-r from-orange-500/10 to-amber-500/10 rounded-lg border border-orange-500/30">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-orange-500/20 rounded-lg">
                <Zap className="h-5 w-5 text-orange-400" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-orange-400 mb-1">
                  Best Opportunity: {data.best_opportunity.token}
                </div>
                <p className="text-sm text-slate-300">
                  {data.best_opportunity.reason}
                </p>
                {data.best_opportunity.advantage_pct > 0 && (
                  <div className="text-xs text-slate-400 mt-1">
                    Advantage: {data.best_opportunity.advantage_pct.toFixed(2)}% better vs alternative
                  </div>
                )}
                {data.best_opportunity.liquidity_note && (
                  <div className="flex items-center gap-1 text-xs text-amber-400 mt-1">
                    <AlertTriangle className="h-3 w-3" />
                    {data.best_opportunity.liquidity_note}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap gap-4 justify-center text-xs text-slate-500 pt-2 border-t border-slate-800">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            Discount = Buy opportunity
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            Premium = Sell opportunity
          </span>
        </div>
      </CardContent>
    </Card>
  )
}

export default BitcoinArbitrageCard
