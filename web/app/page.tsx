'use client'

import { Search, BarChart3, Zap, Shield } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { SearchBar } from '@/components/SearchBar'

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto space-y-16 py-8">
      {/* Hero Section */}
      <section className="text-center space-y-6">
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
          Measure Your{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-orange-600">
            Financial Sovereignty
          </span>
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          Analyze any Algorand wallet. Classify your assets. Calculate your freedom.
        </p>

        {/* Search Bar */}
        <div className="max-w-2xl mx-auto pt-4">
          <SearchBar size="large" showExamples={true} />
        </div>
      </section>

      {/* How It Works */}
      <section className="space-y-8">
        <h2 className="text-2xl font-bold text-center">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-12 h-12 mx-auto rounded-full bg-orange-500/10 flex items-center justify-center">
                <Search className="h-6 w-6 text-orange-500" />
              </div>
              <h3 className="font-semibold text-lg">1. Enter Address</h3>
              <p className="text-slate-400 text-sm">
                Paste any Algorand wallet address (58 characters)
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-12 h-12 mx-auto rounded-full bg-orange-500/10 flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-orange-500" />
              </div>
              <h3 className="font-semibold text-lg">2. See Breakdown</h3>
              <p className="text-slate-400 text-sm">
                View your assets classified by sovereignty tier
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-12 h-12 mx-auto rounded-full bg-orange-500/10 flex items-center justify-center">
                <Zap className="h-6 w-6 text-orange-500" />
              </div>
              <h3 className="font-semibold text-lg">3. Calculate Runway</h3>
              <p className="text-slate-400 text-sm">
                See how long you can sustain your lifestyle
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Philosophy Callout */}
      <section>
        <Card className="bg-slate-900 border-orange-500/20">
          <CardContent className="py-8 px-6 md:px-10">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div className="space-y-4">
                <h3 className="text-2xl font-bold">What is Sovereignty?</h3>
                <div className="bg-slate-800 rounded-lg p-4 font-mono text-lg text-center">
                  <span className="text-orange-500">Sovereignty</span> = Portfolio Value / Annual Expenses
                </div>
                <p className="text-slate-400">
                  It measures how long you can say &quot;no&quot; to income. True freedom isn&apos;t about how much you earn—it&apos;s about how long you can live on your terms.
                </p>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-center">
                    <div className="text-emerald-500 font-bold">20+ years</div>
                    <div className="text-xs text-slate-400">Generational 🟩</div>
                  </div>
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-center">
                    <div className="text-green-500 font-bold">6-20 years</div>
                    <div className="text-xs text-slate-400">Antifragile 🟢</div>
                  </div>
                  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-center">
                    <div className="text-yellow-500 font-bold">3-6 years</div>
                    <div className="text-xs text-slate-400">Robust 🟡</div>
                  </div>
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-center">
                    <div className="text-red-500 font-bold">1-3 years</div>
                    <div className="text-xs text-slate-400">Fragile 🔴</div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Hard Money Philosophy */}
      <section>
        <Card className="bg-orange-500/5 border-orange-500/20">
          <CardContent className="py-6 px-6">
            <div className="flex items-start gap-4">
              <span className="text-3xl">🟠</span>
              <div>
                <h3 className="font-semibold text-lg text-orange-500 mb-2">Hard Money Philosophy</h3>
                <p className="text-slate-400 text-sm">
                  Only Bitcoin, gold, and silver are classified as hard money.
                  Stablecoins are dollars (fiat-pegged). Everything else—including
                  ALGO—is a shitcoin. Sovereignty is measured by hard money holdings only.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Asset Categories */}
      <section className="space-y-8">
        <h2 className="text-2xl font-bold text-center">Asset Classification</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-emerald-500/5 border-emerald-500/30">
            <CardContent className="pt-6 space-y-3">
              <div className="flex items-center gap-3">
                <Shield className="h-6 w-6 text-emerald-500" />
                <h3 className="font-semibold text-lg text-emerald-500">Hard Money</h3>
              </div>
              <p className="text-slate-400 text-sm">
                Bitcoin, gold, and silver only. These are your true sovereignty assets—scarce, durable, and beyond control.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-blue-500/5 border-blue-500/30">
            <CardContent className="pt-6 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">💵</span>
                <h3 className="font-semibold text-lg text-blue-500">Dollars</h3>
              </div>
              <p className="text-slate-400 text-sm">
                Stablecoins (USDC, USDt, DAI, etc). Fiat-pegged assets with counterparty risk. Not hard money.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-red-500/5 border-red-500/30">
            <CardContent className="pt-6 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">💩</span>
                <h3 className="font-semibold text-lg text-red-500">Shitcoins</h3>
              </div>
              <p className="text-slate-400 text-sm">
                ALGO and everything else. LP tokens, governance tokens, NFTs, memecoins. Fun, but not freedom.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA */}
      <section className="text-center space-y-6 pb-8">
        <h2 className="text-2xl font-bold">Ready to Measure Your Freedom?</h2>
        <div className="max-w-xl mx-auto">
          <SearchBar showExamples={false} />
        </div>
      </section>
    </div>
  )
}
