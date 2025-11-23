'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Search, BarChart3, Zap, Wallet } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { WalletConnect } from '@/components/WalletConnect'
import { isValidAlgorandAddress } from '@/lib/utils'

export default function HomePage() {
  const [address, setAddress] = useState('')
  const [isValid, setIsValid] = useState(false)
  const router = useRouter()

  const handleAddressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const addr = e.target.value.toUpperCase()
    setAddress(addr)
    setIsValid(isValidAlgorandAddress(addr))
  }

  const handleManualAnalyze = () => {
    if (isValid) {
      router.push(`/analyze?address=${address}`)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && isValid) {
      handleManualAnalyze()
    }
  }

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
          Connect your wallet or enter any Algorand address. Classify your assets. Calculate your freedom.
        </p>

        {/* Main Input Card */}
        <div className="max-w-xl mx-auto pt-4">
          <Card className="bg-slate-900/80 border-slate-800">
            <CardContent className="pt-6 space-y-6">
              {/* Wallet Connect - PRIMARY METHOD */}
              <div>
                <WalletConnect autoRedirect={true} />
              </div>

              {/* Divider */}
              <div className="flex items-center gap-4">
                <div className="flex-1 border-t border-slate-700" />
                <span className="text-slate-500 text-sm">OR ENTER MANUALLY</span>
                <div className="flex-1 border-t border-slate-700" />
              </div>

              {/* Manual Entry - FALLBACK METHOD */}
              <div>
                <label className="block text-sm font-medium mb-2 text-slate-400 text-left">
                  Algorand Address (58 characters)
                </label>
                <div className="flex gap-2">
                  <Input
                    value={address}
                    onChange={handleAddressChange}
                    onKeyDown={handleKeyDown}
                    placeholder="I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4"
                    className="flex-1 bg-slate-800 border-slate-700 font-mono text-sm"
                  />
                  <Button
                    onClick={handleManualAnalyze}
                    disabled={!isValid}
                    variant="outline"
                    className="border-orange-500 text-orange-500 hover:bg-orange-500 hover:text-white disabled:opacity-50"
                  >
                    <Search className="w-4 h-4" />
                  </Button>
                </div>
                {address.length > 0 && !isValid && (
                  <p className="text-xs text-red-400 mt-2 text-left">
                    Invalid address format (must be 58 characters, A-Z and 2-7 only)
                  </p>
                )}
              </div>

              {/* Example Link */}
              <div className="text-center">
                <button
                  onClick={() => {
                    const exampleAddress = 'I26BHULCOKKBNFF3KEXVH3KWMBK3VWJFKQXYOKFLW4UAET4U4MESL3BIP4'
                    setAddress(exampleAddress)
                    setIsValid(true)
                  }}
                  className="text-sm text-orange-500 hover:text-orange-400 underline"
                >
                  Try example address
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section className="space-y-8">
        <h2 className="text-2xl font-bold text-center">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-12 h-12 mx-auto rounded-full bg-orange-500/10 flex items-center justify-center">
                <Wallet className="h-6 w-6 text-orange-500" />
              </div>
              <h3 className="font-semibold text-lg">1. Connect Wallet</h3>
              <p className="text-slate-400 text-sm">
                Use Pera, Defly, Exodus, or enter any address manually
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

      {/* Hard Money Philosophy - Mining Theme */}
      <section>
        <Card className="bg-gradient-to-br from-orange-500/10 via-yellow-500/5 to-slate-400/10 border-orange-500/30">
          <CardContent className="py-6 px-6">
            <div className="flex items-start gap-4">
              <div className="flex flex-col gap-1 text-2xl">
                <span className="text-orange-500">₿</span>
                <span className="text-yellow-400">🥇</span>
                <span className="text-slate-300">🥈</span>
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">
                  <span className="text-orange-500">Hard</span>{' '}
                  <span className="text-yellow-400">Money</span>{' '}
                  <span className="text-slate-300">Philosophy</span>
                </h3>
                <p className="text-slate-400 text-sm mb-3">
                  Only <span className="text-orange-500 font-medium">Bitcoin</span>,{' '}
                  <span className="text-yellow-400 font-medium">gold</span>, and{' '}
                  <span className="text-slate-300 font-medium">silver</span> are classified as hard money.
                  Stablecoins are dollars (fiat-pegged). Everything else is a shitcoin.
                </p>
                <p className="text-orange-400 text-sm font-medium">
                  ⛏️ Sovereignty is measured by your total portfolio value (Hard Money + Algorand + Dollars + Shitcoins).
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
          <Card className="bg-gradient-to-br from-orange-500/10 via-yellow-500/5 to-slate-400/10 border-orange-500/30">
            <CardContent className="pt-6 space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex gap-1 text-xl">
                  <span className="text-orange-500">₿</span>
                  <span className="text-yellow-400">🥇</span>
                  <span className="text-slate-300">🥈</span>
                </div>
                <h3 className="font-semibold text-lg">
                  <span className="text-orange-500">Hard</span>{' '}
                  <span className="text-yellow-400">Money</span>
                </h3>
              </div>
              <p className="text-slate-400 text-sm">
                <span className="text-orange-500">Bitcoin</span>,{' '}
                <span className="text-yellow-400">gold</span>, and{' '}
                <span className="text-slate-300">silver</span> only. Your true sovereignty assets—scarce, durable, and beyond control.
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
        <div className="max-w-md mx-auto">
          <WalletConnect />
        </div>
      </section>
    </div>
  )
}
