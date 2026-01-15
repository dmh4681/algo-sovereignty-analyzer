'use client'

import { Pickaxe as PickaxeIcon, Mountain, Gem, Coins } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { WalletConnect } from '@/components/WalletConnect'
import { DwarfMiner, TreasureChest, GoldBars, CoinStack, Pickaxe } from '@/components/illustrations'

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto space-y-16 py-8">
      {/* Hero Section - Mining Theme */}
      <section className="text-center space-y-6 relative">
        {/* Decorative pickaxes */}
        <div className="absolute -left-4 top-0 opacity-20 hidden lg:block">
          <Pickaxe size={80} variant="gold" animated />
        </div>
        <div className="absolute -right-4 top-0 opacity-20 hidden lg:block transform scale-x-[-1]">
          <Pickaxe size={80} variant="silver" animated />
        </div>

        <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
          Mine Your{' '}
          <span className="gold-shimmer">
            Financial Sovereignty
          </span>
        </h1>
        <p className="text-xl text-amber-200/70 max-w-2xl mx-auto">
          Connect your Algorand wallet. Unearth your hard money. Calculate your freedom.
        </p>

        {/* Dwarf Miner Mascot */}
        <div className="flex justify-center py-4">
          <DwarfMiner size={140} animated />
        </div>

        {/* Main Input Card */}
        <div className="max-w-xl mx-auto pt-4">
          <Card className="bg-stone-900/80 border-amber-700/30 gold-glow">
            <CardContent className="pt-6 pb-6">
              {/* Wallet Connect - ONLY METHOD */}
              <WalletConnect autoRedirect={true} />
            </CardContent>
          </Card>
        </div>
      </section>

      {/* How It Works - Mining Steps */}
      <section className="space-y-8">
        <h2 className="text-2xl font-bold text-center text-amber-100">How to Mine Your Freedom</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-stone-900/50 border-amber-900/30 hover:border-amber-600/50 transition-colors">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-amber-500/10 flex items-center justify-center">
                <PickaxeIcon className="h-8 w-8 text-amber-400" />
              </div>
              <h3 className="font-semibold text-lg text-amber-100">1. Enter the Mine</h3>
              <p className="text-amber-200/60 text-sm">
                Connect with Pera, Defly, Exodus, or any Algorand address
              </p>
            </CardContent>
          </Card>

          <Card className="bg-stone-900/50 border-amber-900/30 hover:border-yellow-500/50 transition-colors">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-yellow-500/10 flex items-center justify-center">
                <Gem className="h-8 w-8 text-yellow-400" />
              </div>
              <h3 className="font-semibold text-lg text-amber-100">2. Discover Treasure</h3>
              <p className="text-amber-200/60 text-sm">
                View your assets sorted by hard money classification
              </p>
            </CardContent>
          </Card>

          <Card className="bg-stone-900/50 border-amber-900/30 hover:border-emerald-500/50 transition-colors">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-emerald-500/10 flex items-center justify-center">
                <Coins className="h-8 w-8 text-emerald-400" />
              </div>
              <h3 className="font-semibold text-lg text-amber-100">3. Count Your Hoard</h3>
              <p className="text-amber-200/60 text-sm">
                Calculate how long your treasure grants you freedom
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Philosophy Callout - Treasure Vault */}
      <section>
        <Card className="bg-stone-900 border-amber-600/30 overflow-hidden relative">
          <CardContent className="py-8 px-6 md:px-10">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div className="space-y-4">
                <h3 className="text-2xl font-bold text-amber-100">What is Sovereignty?</h3>
                <div className="bg-stone-800 rounded-lg p-4 font-mono text-lg text-center border border-amber-700/30">
                  <span className="text-yellow-400">Sovereignty</span> = Treasure Hoard / Annual Expenses
                </div>
                <p className="text-amber-200/70">
                  It measures how long you can say &quot;no&quot; to income. True freedom isn&apos;t about how much you earn—it&apos;s about how long you can live on your terms.
                </p>
                {/* Treasure chest illustration */}
                <div className="flex justify-center pt-2">
                  <TreasureChest size={120} open={true} animated />
                </div>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-center">
                    <div className="text-emerald-400 font-bold">20+ years</div>
                    <div className="text-xs text-amber-200/50">Dragon&apos;s Hoard 🐉</div>
                  </div>
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-center">
                    <div className="text-green-400 font-bold">6-20 years</div>
                    <div className="text-xs text-amber-200/50">King&apos;s Treasury 👑</div>
                  </div>
                  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-center">
                    <div className="text-yellow-400 font-bold">3-6 years</div>
                    <div className="text-xs text-amber-200/50">Merchant&apos;s Chest 🪙</div>
                  </div>
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-center">
                    <div className="text-red-400 font-bold">1-3 years</div>
                    <div className="text-xs text-amber-200/50">Miner&apos;s Pouch ⛏️</div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Hard Money Philosophy - Mining Theme with Gold Bars */}
      <section>
        <Card className="bg-gradient-to-br from-amber-600/15 via-yellow-500/10 to-gray-400/10 border-yellow-500/40">
          <CardContent className="py-6 px-6">
            <div className="flex items-start gap-6">
              {/* Gold bars illustration */}
              <div className="hidden sm:block flex-shrink-0">
                <GoldBars size={100} variant="stack" animated />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-xl mb-3">
                  <span className="text-amber-400">Hard</span>{' '}
                  <span className="text-yellow-400">Money</span>{' '}
                  <span className="text-gray-300">Philosophy</span>
                </h3>
                <p className="text-amber-200/70 text-sm mb-4">
                  Only <span className="text-amber-400 font-medium">Bitcoin</span>,{' '}
                  <span className="text-yellow-400 font-medium">gold</span>, and{' '}
                  <span className="text-gray-300 font-medium">silver</span> are classified as hard money.
                  Stablecoins are dollars (fiat-pegged). Everything else is a shitcoin.
                </p>
                <div className="flex items-center gap-3 bg-stone-800/50 rounded-lg p-3 border border-amber-700/30">
                  <span className="text-2xl">⛏️</span>
                  <p className="text-amber-300 text-sm font-medium">
                    Sovereignty is measured by your total portfolio (Hard Money + Algorand + Dollars + Shitcoins).
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Asset Categories - Mining Loot Types */}
      <section className="space-y-8">
        <h2 className="text-2xl font-bold text-center text-amber-100">Your Mining Loot</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-gradient-to-br from-amber-600/15 via-yellow-500/10 to-gray-400/10 border-yellow-500/40 relative overflow-hidden">
            <div className="absolute -right-4 -bottom-4 opacity-20">
              <CoinStack size={80} metal="gold" animated={false} />
            </div>
            <CardContent className="pt-6 space-y-3 relative">
              <div className="flex items-center gap-3">
                <div className="flex gap-1 text-xl">
                  <span className="text-amber-400">₿</span>
                  <span className="text-yellow-400">🪙</span>
                  <span className="text-gray-300">🥈</span>
                </div>
                <h3 className="font-semibold text-lg">
                  <span className="text-amber-400">Precious</span>{' '}
                  <span className="text-yellow-400">Metals</span>
                </h3>
              </div>
              <p className="text-amber-200/60 text-sm">
                <span className="text-amber-400">Bitcoin</span>,{' '}
                <span className="text-yellow-400">gold</span>, and{' '}
                <span className="text-gray-300">silver</span>. Your true sovereignty—scarce, durable, beyond any king&apos;s control.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-green-500/5 border-green-500/30">
            <CardContent className="pt-6 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">💵</span>
                <h3 className="font-semibold text-lg text-green-400">Paper Money</h3>
              </div>
              <p className="text-amber-200/60 text-sm">
                Stablecoins (USDC, USDt, DAI). Fiat-pegged currency with counterparty risk. Useful but not hard money.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-red-500/5 border-red-500/30">
            <CardContent className="pt-6 space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🪨</span>
                <h3 className="font-semibold text-lg text-red-400">Raw Ore</h3>
              </div>
              <p className="text-amber-200/60 text-sm">
                ALGO and everything else. LP tokens, governance tokens, NFTs, memecoins. Speculative, not refined treasure.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA - Enter the Mine */}
      <section className="text-center space-y-6 pb-8">
        <div className="flex justify-center">
          <Mountain className="h-12 w-12 text-amber-600/50" />
        </div>
        <h2 className="text-2xl font-bold text-amber-100">Ready to Enter the Mine?</h2>
        <p className="text-amber-200/60">Connect your wallet and discover your true wealth</p>
        <div className="max-w-md mx-auto">
          <WalletConnect />
        </div>
      </section>
    </div>
  )
}
