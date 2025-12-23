'use client'

import Image from 'next/image'
import { Pickaxe, Package, Sparkles, Lock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PICKAXE_NFTS, BUNDLE_DEAL, getPickaxeColorClasses } from '@/lib/nft-config'

export default function ShopPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-12 py-8">
      {/* Hero Section */}
      <section className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3">
          <Pickaxe className="w-10 h-10 text-orange-500" />
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
            Mining{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-orange-500 to-slate-300">
              Pickaxe Shop
            </span>
          </h1>
        </div>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          Acquire a pickaxe NFT to auto-mine hard money. Deposit ALGO, automatically swap to your target asset.
        </p>
      </section>

      {/* Bundle Deal Banner */}
      <section>
        <Card className="bg-gradient-to-r from-orange-500/20 via-yellow-500/20 to-slate-400/20 border-orange-500/50">
          <CardContent className="py-6 px-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-orange-500/20 rounded-full">
                  <Package className="w-8 h-8 text-orange-500" />
                </div>
                <div>
                  <h3 className="text-xl font-bold flex items-center gap-2">
                    {BUNDLE_DEAL.name}
                    <span className="text-sm bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">
                      Save {BUNDLE_DEAL.savingsPercent}%
                    </span>
                  </h3>
                  <p className="text-slate-400">{BUNDLE_DEAL.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm text-slate-500 line-through">{BUNDLE_DEAL.originalPrice} ALGO</div>
                  <div className="text-2xl font-bold text-orange-500">{BUNDLE_DEAL.bundlePrice} ALGO</div>
                </div>
                <Button size="lg" disabled className="gap-2">
                  <Lock className="w-4 h-4" />
                  Coming Soon
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Pickaxe NFT Grid */}
      <section className="space-y-6">
        <h2 className="text-2xl font-bold text-center">Individual Pickaxes</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PICKAXE_NFTS.map((nft) => {
            const colors = getPickaxeColorClasses(nft.color)
            return (
              <Card
                key={nft.id}
                className={`${colors.bg} ${colors.border} border-2 transition-all hover:scale-[1.02] hover:shadow-lg ${colors.glow}`}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className={`text-lg ${colors.text}`}>{nft.name}</CardTitle>
                    <span className={`text-xs px-2 py-1 rounded-full ${colors.bg} ${colors.text} border ${colors.border}`}>
                      {nft.rarity.charAt(0).toUpperCase() + nft.rarity.slice(1)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* NFT Image Placeholder */}
                  <div className={`aspect-square rounded-lg ${colors.bg} border ${colors.border} flex items-center justify-center overflow-hidden`}>
                    <div className="relative w-full h-full">
                      <Image
                        src={nft.image}
                        alt={nft.name}
                        fill
                        className="object-contain p-4"
                        onError={(e) => {
                          // Hide image on error, show placeholder
                          const target = e.target as HTMLImageElement
                          target.style.display = 'none'
                        }}
                      />
                      {/* Fallback placeholder */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Pickaxe className={`w-24 h-24 ${colors.text} opacity-50`} />
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  <CardDescription className="text-sm min-h-[3rem]">
                    {nft.description}
                  </CardDescription>

                  {/* Target Asset */}
                  <div className={`flex items-center gap-2 text-sm ${colors.text}`}>
                    <Sparkles className="w-4 h-4" />
                    <span>Mines: <strong>{nft.targetAsset.ticker}</strong></span>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                      <div className="text-slate-400">Price</div>
                      <div className={`font-bold ${colors.text}`}>{nft.price} ALGO</div>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                      <div className="text-slate-400">Supply</div>
                      <div className="font-bold text-white">{nft.supply.toLocaleString()}</div>
                    </div>
                  </div>

                  {/* Buy Button */}
                  <Button
                    className="w-full gap-2"
                    variant={nft.available ? 'default' : 'secondary'}
                    disabled={!nft.available}
                  >
                    {nft.available ? (
                      <>Buy Now</>
                    ) : (
                      <>
                        <Lock className="w-4 h-4" />
                        Coming Soon
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      {/* How Auto-Mining Works */}
      <section className="space-y-6">
        <h2 className="text-2xl font-bold text-center">How Auto-Mining Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 text-center space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-orange-500/10 flex items-center justify-center text-2xl">
                1
              </div>
              <h3 className="font-semibold">Buy Pickaxe</h3>
              <p className="text-slate-400 text-sm">
                Purchase a pickaxe NFT for your target hard money asset
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 text-center space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-orange-500/10 flex items-center justify-center text-2xl">
                2
              </div>
              <h3 className="font-semibold">Deposit ALGO</h3>
              <p className="text-slate-400 text-sm">
                Fund your mining balance with ALGO deposits
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 text-center space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-orange-500/10 flex items-center justify-center text-2xl">
                3
              </div>
              <h3 className="font-semibold">Auto-Swap</h3>
              <p className="text-slate-400 text-sm">
                When balance hits threshold, we auto-swap to your target asset
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="pt-6 text-center space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-orange-500/10 flex items-center justify-center text-2xl">
                4
              </div>
              <h3 className="font-semibold">Stack Hard Money</h3>
              <p className="text-slate-400 text-sm">
                Watch your hard money stack grow automatically
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* FAQ / Info Section */}
      <section>
        <Card className="bg-slate-900/80 border-slate-800">
          <CardContent className="py-6 px-6 space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Pickaxe className="w-5 h-5 text-orange-500" />
              About Mining NFTs
            </h3>
            <div className="grid md:grid-cols-2 gap-6 text-sm text-slate-400">
              <div className="space-y-3">
                <p>
                  <strong className="text-slate-200">What is a mining pickaxe?</strong><br />
                  Each pickaxe NFT grants you access to auto-mining for a specific hard money asset.
                  Deposit ALGO, and when your balance reaches the threshold, it automatically swaps to your target asset.
                </p>
                <p>
                  <strong className="text-slate-200">Why auto-mine?</strong><br />
                  Dollar-cost averaging into hard money is the sovereign way. Auto-mining removes the friction
                  and helps you stack consistently without manual intervention.
                </p>
              </div>
              <div className="space-y-3">
                <p>
                  <strong className="text-slate-200">How does the swap work?</strong><br />
                  When your deposited ALGO balance reaches the configured threshold (default 50 ALGO),
                  our system automatically executes a swap on Tinyman DEX to your target asset.
                </p>
                <p>
                  <strong className="text-slate-200">Is my ALGO safe?</strong><br />
                  You maintain custody of your funds. The pickaxe NFT grants permission for our system
                  to execute swaps on your behalf, but you can withdraw anytime.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
