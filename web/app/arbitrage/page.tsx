'use client'

import Link from 'next/link'
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, Info, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { MeldArbitrageSpotter } from '@/components/MeldArbitrageSpotter'

export default function ArbitragePage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          asChild
        >
          <Link href="/">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
        </Button>
      </div>

      {/* Hero Section */}
      <div className="text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold">
          Arbitrage Spotter
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto">
          Compare on-chain asset prices to spot markets.
          Find opportunities when Meld tokens or goBTC trade above or below fair value.
        </p>
      </div>

      {/* Main Widget */}
      <section>
        <MeldArbitrageSpotter autoRefresh={true} refreshInterval={30000} />
      </section>

      {/* How It Works */}
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5 text-cyan-500" />
            How It Works
          </CardTitle>
          <CardDescription>
            Understanding the arbitrage calculation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-200">Data Sources</h3>
              <ol className="space-y-3 text-sm text-slate-400">
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-500/20 text-orange-500 flex items-center justify-center text-xs font-bold">1</span>
                  <span>We fetch spot gold/silver prices from Yahoo Finance (GC=F, SI=F futures)</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-500/20 text-orange-500 flex items-center justify-center text-xs font-bold">2</span>
                  <span>We fetch Meld GOLD$/SILVER$ token prices from Vestige DEX aggregator</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-500/20 text-orange-500 flex items-center justify-center text-xs font-bold">3</span>
                  <span>We convert spot price (per troy oz) to per-gram to match Meld's denomination</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-500/20 text-orange-500 flex items-center justify-center text-xs font-bold">4</span>
                  <span>We calculate the premium/discount: (Meld - Spot) / Spot × 100%</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-500/20 text-orange-500 flex items-center justify-center text-xs font-bold">5</span>
                  <span>For Bitcoin, we compare goBTC (Vestige) to Coinbase BTC spot price</span>
                </li>
              </ol>
            </div>
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-200">Signal Thresholds</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between p-2 rounded bg-green-500/10 border border-green-500/30">
                  <span className="text-green-400 font-medium">STRONG BUY</span>
                  <span className="text-slate-400">&gt;10% discount (Meld underpriced)</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-green-400/10 border border-green-400/30">
                  <span className="text-green-300 font-medium">BUY</span>
                  <span className="text-slate-400">5-10% discount</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-slate-500/10 border border-slate-500/30">
                  <span className="text-slate-300 font-medium">HOLD</span>
                  <span className="text-slate-400">±5% (fair value)</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-orange-500/10 border border-orange-500/30">
                  <span className="text-orange-400 font-medium">SELL</span>
                  <span className="text-slate-400">5-10% premium</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-red-500/10 border border-red-500/30">
                  <span className="text-red-400 font-medium">STRONG SELL</span>
                  <span className="text-slate-400">&gt;10% premium (Meld overpriced)</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* How to Trade */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Buy Strategy */}
        <Card className="border-green-500/30 bg-green-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-400">
              <TrendingUp className="h-5 w-5" />
              If STRONG_BUY (Meld Underpriced)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ol className="space-y-3 text-sm text-slate-300">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-xs font-bold">1</span>
                <span>Buy GOLD$ or SILVER$ tokens on Tinyman, Pact, or Vestige</span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-xs font-bold">2</span>
                <span>Hold the tokens as a precious metals proxy at a discount</span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-xs font-bold">3</span>
                <span>Optionally redeem for physical metal via meld.gold (minimum amounts apply)</span>
              </li>
            </ol>
            <div className="pt-2 text-xs text-slate-500">
              Best for: Long-term precious metals accumulators looking to DCA at a discount
            </div>
          </CardContent>
        </Card>

        {/* Sell Strategy */}
        <Card className="border-red-500/30 bg-red-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-400">
              <TrendingDown className="h-5 w-5" />
              If STRONG_SELL (Meld Overpriced)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ol className="space-y-3 text-sm text-slate-300">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center text-xs font-bold">1</span>
                <span>Sell your GOLD$ or SILVER$ tokens on Tinyman, Pact, or Vestige</span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center text-xs font-bold">2</span>
                <span>Realize the premium above spot price</span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center text-xs font-bold">3</span>
                <span>Optionally buy physical metal from a dealer or ETF at spot to maintain exposure</span>
              </li>
            </ol>
            <div className="pt-2 text-xs text-slate-500">
              Best for: Taking profits when on-chain premiums exceed physical dealer spreads
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bitcoin Signal */}
      <Card className="border-orange-500/30 bg-orange-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-orange-400">
            <span className="text-2xl">₿</span>
            Bitcoin / goBTC Arbitrage
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-green-400 mb-3">If goBTC is Underpriced (Discount)</h4>
              <ol className="space-y-2 text-sm text-slate-300">
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-xs font-bold">1</span>
                  <span>Buy goBTC on Tinyman or Vestige at a discount to spot BTC</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-xs font-bold">2</span>
                  <span>Hold as BTC exposure on Algorand, or bridge back to native BTC</span>
                </li>
              </ol>
            </div>
            <div>
              <h4 className="font-medium text-red-400 mb-3">If goBTC is Overpriced (Premium)</h4>
              <ol className="space-y-2 text-sm text-slate-300">
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center text-xs font-bold">1</span>
                  <span>Sell goBTC on Algorand DEXs above spot price</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center text-xs font-bold">2</span>
                  <span>Rebuy native BTC on an exchange at spot to maintain exposure</span>
                </li>
              </ol>
            </div>
          </div>
          <div className="pt-2 text-xs text-slate-500">
            Note: goBTC is a wrapped Bitcoin token on Algorand. Verify bridge liquidity and fees before large trades.
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle>Quick Links</CardTitle>
          <CardDescription>Trade and research resources</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <a
              href="https://vestige.fi/asset/246516580"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors group"
            >
              <span className="text-2xl">🥇</span>
              <span className="text-sm font-medium text-slate-300 group-hover:text-orange-400">Trade GOLD$</span>
              <ExternalLink className="h-3 w-3 text-slate-500" />
            </a>
            <a
              href="https://vestige.fi/asset/246519683"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors group"
            >
              <span className="text-2xl">🥈</span>
              <span className="text-sm font-medium text-slate-300 group-hover:text-orange-400">Trade SILVER$</span>
              <ExternalLink className="h-3 w-3 text-slate-500" />
            </a>
            <a
              href="https://vestige.fi/asset/386192725"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors group"
            >
              <span className="text-2xl">₿</span>
              <span className="text-sm font-medium text-slate-300 group-hover:text-orange-400">Trade goBTC</span>
              <ExternalLink className="h-3 w-3 text-slate-500" />
            </a>
            <a
              href="https://meld.gold"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors group"
            >
              <span className="text-2xl">🏦</span>
              <span className="text-sm font-medium text-slate-300 group-hover:text-orange-400">Meld Gold</span>
              <ExternalLink className="h-3 w-3 text-slate-500" />
            </a>
            <a
              href="https://finance.yahoo.com/quote/GC=F"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors group"
            >
              <span className="text-2xl">📈</span>
              <span className="text-sm font-medium text-slate-300 group-hover:text-orange-400">Spot Prices</span>
              <ExternalLink className="h-3 w-3 text-slate-500" />
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Historical Tracking Placeholder */}
      <Card className="border-slate-700 border-dashed opacity-60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-slate-500">
            📊 Historical Premium Tracking
            <span className="text-xs bg-slate-700 px-2 py-1 rounded">Coming Soon</span>
          </CardTitle>
          <CardDescription>
            Track premium/discount trends over time to identify patterns and optimal entry points.
            Includes BTC dominance tracking to correlate with goBTC premiums.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center text-slate-600 text-sm">
            Premium history chart will appear here
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="py-4">
          <div className="flex gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-slate-400">
              <strong className="text-amber-400">Disclaimer:</strong> This tool is for informational purposes only and does not constitute financial advice.
              Arbitrage opportunities may disappear quickly due to market movements. DEX slippage, swap fees, and transaction costs
              may eliminate small premiums. Meld tokens carry counterparty risk with the issuer. Always do your own research (DYOR)
              and understand the risks before trading.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
