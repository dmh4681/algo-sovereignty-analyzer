import { Metadata } from 'next'
import { MeldArbitrageSpotter } from '@/components/MeldArbitrageSpotter'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ExternalLink, AlertTriangle, TrendingUp, TrendingDown, Scale } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Meld Arbitrage Spotter | Algorand Sovereignty Analyzer',
  description: 'Compare Meld Gold and Silver on-chain prices to spot precious metals prices. Find arbitrage opportunities.',
}

export default function ArbitragePage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Hero */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2 flex items-center justify-center gap-3">
          <Scale className="h-10 w-10 text-orange-500" />
          Meld Arbitrage Spotter
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          Compare on-chain precious metals prices to spot. 
          Find opportunities when Meld tokens trade above or below fair value.
        </p>
      </div>
      
      {/* Main Widget */}
      <MeldArbitrageSpotter autoRefresh={true} refreshInterval={30000} />
      
      {/* How It Works */}
      <Card className="mt-8 border-slate-700">
        <CardHeader>
          <CardTitle className="text-xl">📊 How It Works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-4 gap-4">
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="text-2xl mb-2">1️⃣</div>
              <div className="font-medium text-slate-200">Spot Prices</div>
              <div className="text-sm text-slate-400">
                Fetch gold/silver spot prices from Yahoo Finance (COMEX futures)
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="text-2xl mb-2">2️⃣</div>
              <div className="font-medium text-slate-200">Convert to Grams</div>
              <div className="text-sm text-slate-400">
                Divide spot price by 31.1035 (grams per troy ounce)
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="text-2xl mb-2">3️⃣</div>
              <div className="font-medium text-slate-200">Meld Prices</div>
              <div className="text-sm text-slate-400">
                Fetch GOLD$/SILVER$ prices from Vestige DEX aggregator
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="text-2xl mb-2">4️⃣</div>
              <div className="font-medium text-slate-200">Calculate Premium</div>
              <div className="text-sm text-slate-400">
                Compare Meld price to implied price. Generate signal.
              </div>
            </div>
          </div>
          
          <div className="bg-slate-800/30 rounded-lg p-4 mt-4">
            <div className="font-mono text-sm text-slate-300">
              <div>implied_price = spot_per_oz / 31.1035</div>
              <div>premium_pct = ((meld_price - implied_price) / implied_price) × 100</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Trading Guide */}
      <div className="grid md:grid-cols-2 gap-6 mt-8">
        {/* Buy Signal */}
        <Card className="border-green-500/30 bg-green-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-400">
              <TrendingUp className="h-5 w-5" />
              When to BUY Meld
            </CardTitle>
            <CardDescription>
              Meld trading below spot (negative premium)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-slate-300">
              <strong className="text-green-400">Opportunity:</strong> Meld tokens are cheaper than 
              physical metal. You're getting gold/silver at a discount.
            </div>
            <div className="text-sm text-slate-400">
              <strong>Action:</strong>
              <ol className="list-decimal list-inside mt-2 space-y-1">
                <li>Buy GOLD$ or SILVER$ on Tinyman or Pact</li>
                <li>Hold for appreciation or redemption</li>
                <li>Optionally redeem for physical via meld.gold</li>
              </ol>
            </div>
            <div className="text-xs text-slate-500 mt-3">
              ⚠️ Consider DEX slippage and fees when calculating true discount
            </div>
          </CardContent>
        </Card>
        
        {/* Sell Signal */}
        <Card className="border-red-500/30 bg-red-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-400">
              <TrendingDown className="h-5 w-5" />
              When to SELL Meld
            </CardTitle>
            <CardDescription>
              Meld trading above spot (positive premium)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-slate-300">
              <strong className="text-red-400">Opportunity:</strong> Meld tokens are more expensive 
              than physical metal. Sell at a premium.
            </div>
            <div className="text-sm text-slate-400">
              <strong>Action:</strong>
              <ol className="list-decimal list-inside mt-2 space-y-1">
                <li>Sell GOLD$ or SILVER$ on Tinyman or Pact</li>
                <li>Receive ALGO or USDC at premium price</li>
                <li>Optionally buy physical metal elsewhere</li>
              </ol>
            </div>
            <div className="text-xs text-slate-500 mt-3">
              ⚠️ Premium may reflect convenience/liquidity value, not pure arbitrage
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Quick Links */}
      <Card className="mt-8 border-slate-700">
        <CardHeader>
          <CardTitle className="text-xl">🔗 Quick Links</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a 
              href="https://vestige.fi/asset/246516580"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <span className="text-xl">🥇</span>
              <div>
                <div className="font-medium text-slate-200">Trade GOLD$</div>
                <div className="text-xs text-slate-400">Vestige</div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-500 ml-auto" />
            </a>
            
            <a 
              href="https://vestige.fi/asset/246519683"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <span className="text-xl">🥈</span>
              <div>
                <div className="font-medium text-slate-200">Trade SILVER$</div>
                <div className="text-xs text-slate-400">Vestige</div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-500 ml-auto" />
            </a>
            
            <a 
              href="https://meld.gold"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <span className="text-xl">🏦</span>
              <div>
                <div className="font-medium text-slate-200">Meld Gold</div>
                <div className="text-xs text-slate-400">Issuer</div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-500 ml-auto" />
            </a>
            
            <a 
              href="https://finance.yahoo.com/quote/GC=F"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <span className="text-xl">📈</span>
              <div>
                <div className="font-medium text-slate-200">Gold Spot</div>
                <div className="text-xs text-slate-400">Yahoo Finance</div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-500 ml-auto" />
            </a>
          </div>
        </CardContent>
      </Card>
      
      {/* Disclaimer */}
      <Card className="mt-8 border-yellow-500/30 bg-yellow-500/5">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-medium text-yellow-400 mb-1">Disclaimer</div>
              <div className="text-sm text-slate-400">
                This tool is for informational purposes only. Not financial advice. 
                Arbitrage opportunities may disappear quickly due to market movements. 
                DEX slippage, trading fees, and gas costs may eliminate small premiums. 
                Meld tokens are redeemable for physical metal, but redemption has minimum 
                amounts and fees. Always do your own research before trading.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Future Features Placeholder */}
      <div className="mt-8 text-center text-slate-500 text-sm">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/30 rounded-full">
          <span>🚧</span>
          <span>Coming Soon: Historical premium charts, price alerts, gold/silver ratio tracking</span>
        </div>
      </div>
    </div>
  )
}
