'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Pickaxe, Package, Sparkles, ExternalLink, ShoppingCart, Loader2, CheckCircle2, XCircle, Wallet } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PICKAXE_NFTS, BUNDLE_DEAL, getPickaxeColorClasses, type PickaxeNFT } from '@/lib/nft-config'
import { usePurchaseNFT } from '@/lib/usePurchaseNFT'
import { useWallet } from '@txnlab/use-wallet-react'

function PurchaseButton({ nft }: { nft: PickaxeNFT }) {
  const { purchaseNFT, status, error, txId, reset, isConnected } = usePurchaseNFT()
  const { wallets } = useWallet()
  const [showModal, setShowModal] = useState(false)

  const handleBuyClick = async () => {
    if (!isConnected) {
      // Try to connect with first available wallet
      const availableWallet = wallets.find(w => w.isAvailable)
      if (availableWallet) {
        try {
          await availableWallet.connect()
        } catch {
          // User cancelled or error
          return
        }
      }
      return
    }

    setShowModal(true)
    await purchaseNFT(nft)
  }

  const handleClose = () => {
    setShowModal(false)
    reset()
  }

  const getStatusMessage = () => {
    switch (status) {
      case 'checking':
        return 'Checking asset opt-in...'
      case 'opting-in':
        return 'Preparing opt-in transaction...'
      case 'signing':
        return 'Please sign the transaction in your wallet...'
      case 'submitting':
        return 'Submitting transaction to network...'
      case 'success':
        return 'Purchase successful!'
      case 'error':
        return error || 'Purchase failed'
      default:
        return ''
    }
  }

  const isProcessing = ['checking', 'opting-in', 'signing', 'submitting'].includes(status)

  return (
    <>
      <Button
        className="w-full gap-2"
        onClick={handleBuyClick}
        disabled={isProcessing}
      >
        {!isConnected ? (
          <>
            <Wallet className="w-4 h-4" />
            Connect Wallet
          </>
        ) : isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <ShoppingCart className="w-4 h-4" />
            Buy Now
          </>
        )}
      </Button>

      {/* Purchase Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-bold">Purchasing {nft.name}</h3>
              {(status === 'success' || status === 'error') && (
                <button
                  onClick={handleClose}
                  className="text-slate-400 hover:text-white"
                >
                  &times;
                </button>
              )}
            </div>

            <div className="flex items-center gap-4 py-4">
              {isProcessing && (
                <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
              )}
              {status === 'success' && (
                <CheckCircle2 className="w-8 h-8 text-green-500" />
              )}
              {status === 'error' && (
                <XCircle className="w-8 h-8 text-red-500" />
              )}
              <div className="flex-1">
                <p className="text-slate-300">{getStatusMessage()}</p>
                {status === 'signing' && (
                  <p className="text-sm text-slate-500 mt-1">
                    This will send {nft.price} ALGO to the contract
                  </p>
                )}
              </div>
            </div>

            {status === 'success' && txId && (
              <div className="bg-slate-800/50 rounded-lg p-4 space-y-2">
                <p className="text-sm text-slate-400">Transaction ID:</p>
                <a
                  href={`https://explorer.perawallet.app/tx/${txId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-orange-500 hover:text-orange-400 break-all flex items-center gap-1"
                >
                  {txId}
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
                <p className="text-sm text-green-400 mt-2">
                  Your {nft.name} NFT has been sent to your wallet!
                </p>
              </div>
            )}

            {status === 'error' && (
              <div className="bg-red-900/20 border border-red-900/50 rounded-lg p-4">
                <p className="text-sm text-red-400">{error}</p>
                <Button
                  variant="outline"
                  className="mt-3"
                  onClick={() => {
                    reset()
                    purchaseNFT(nft)
                  }}
                >
                  Try Again
                </Button>
              </div>
            )}

            {(status === 'success' || status === 'error') && (
              <Button
                className="w-full"
                variant={status === 'success' ? 'default' : 'outline'}
                onClick={handleClose}
              >
                {status === 'success' ? 'Done' : 'Close'}
              </Button>
            )}
          </div>
        </div>
      )}
    </>
  )
}

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
                  <ShoppingCart className="w-4 h-4" />
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

                  {/* Verify on Explorer */}
                  <a
                    href={nft.explorerUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 text-sm text-slate-400 hover:text-orange-500 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Verify on Pera Explorer (ASA {nft.asaId})
                  </a>

                  {/* Buy Button */}
                  <PurchaseButton nft={nft} />
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
