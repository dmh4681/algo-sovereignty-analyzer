// TODO: Re-enable when auto-mining feature is ready
// This component is part of the NFT auto-mining system that is currently disabled.

'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Pickaxe, Wallet, ArrowRightLeft, Power, PowerOff, ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PICKAXE_NFTS, getPickaxeColorClasses, type PickaxeNFT } from '@/lib/nft-config'

interface OwnedPickaxe {
  nft: PickaxeNFT
  isActive: boolean
  depositBalance: number
  threshold: number
  totalMined: number
  swapHistory: SwapRecord[]
}

interface SwapRecord {
  id: string
  date: string
  algoAmount: number
  targetAmount: number
  targetTicker: string
  txId: string
}

// Placeholder data for UI demonstration
const PLACEHOLDER_OWNED_PICKAXES: OwnedPickaxe[] = [
  {
    nft: PICKAXE_NFTS[0], // Gold Pickaxe
    isActive: true,
    depositBalance: 35.5,
    threshold: 50,
    totalMined: 0.0234,
    swapHistory: [
      {
        id: '1',
        date: '2024-01-15',
        algoAmount: 50,
        targetAmount: 0.0117,
        targetTicker: 'GOLD$',
        txId: 'ABC123...'
      },
      {
        id: '2',
        date: '2024-01-08',
        algoAmount: 50,
        targetAmount: 0.0117,
        targetTicker: 'GOLD$',
        txId: 'DEF456...'
      }
    ]
  }
]

// Empty state for users with no pickaxes
const EMPTY_PICKAXES: OwnedPickaxe[] = []

interface AutoMinerDashboardProps {
  showPlaceholder?: boolean
}

export function AutoMinerDashboard({ showPlaceholder = true }: AutoMinerDashboardProps) {
  const ownedPickaxes = showPlaceholder ? PLACEHOLDER_OWNED_PICKAXES : EMPTY_PICKAXES
  const [expandedPickaxe, setExpandedPickaxe] = useState<string | null>(
    ownedPickaxes.length > 0 ? ownedPickaxes[0].nft.id : null
  )

  if (ownedPickaxes.length === 0) {
    return (
      <Card className="bg-slate-900/50 border-slate-800">
        <CardContent className="py-12 text-center space-y-4">
          <Pickaxe className="w-16 h-16 mx-auto text-slate-600" />
          <h3 className="text-xl font-semibold text-slate-400">No Pickaxes Owned</h3>
          <p className="text-slate-500 max-w-md mx-auto">
            Visit the shop to purchase a mining pickaxe and start auto-mining hard money.
          </p>
          <Button variant="outline" className="gap-2">
            <Pickaxe className="w-4 h-4" />
            Visit Shop
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Pickaxe className="w-6 h-6 text-orange-500" />
          Auto-Miner Dashboard
        </h2>
        <div className="text-sm text-slate-400">
          {ownedPickaxes.filter(p => p.isActive).length} of {ownedPickaxes.length} active
        </div>
      </div>

      {/* Pickaxe Cards */}
      <div className="space-y-4">
        {ownedPickaxes.map((owned) => {
          const colors = getPickaxeColorClasses(owned.nft.color)
          const isExpanded = expandedPickaxe === owned.nft.id
          const progressPercent = (owned.depositBalance / owned.threshold) * 100

          return (
            <Card
              key={owned.nft.id}
              className={`${colors.border} border-2 transition-all ${isExpanded ? colors.glow + ' shadow-lg' : ''}`}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {/* Mini Pickaxe Image */}
                    <div className={`w-12 h-12 rounded-lg ${colors.bg} border ${colors.border} flex items-center justify-center overflow-hidden`}>
                      <Image
                        src={owned.nft.image}
                        alt={owned.nft.name}
                        width={40}
                        height={40}
                        className="object-contain"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement
                          target.style.display = 'none'
                        }}
                      />
                      <Pickaxe className={`w-6 h-6 ${colors.text} opacity-50 absolute`} />
                    </div>
                    <div>
                      <CardTitle className={`text-lg ${colors.text}`}>{owned.nft.name}</CardTitle>
                      <div className="text-sm text-slate-400">
                        Mining: <span className="font-medium text-white">{owned.nft.targetAsset.ticker}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {/* Status Indicator */}
                    <div className={`flex items-center gap-2 text-sm ${owned.isActive ? 'text-green-400' : 'text-slate-500'}`}>
                      {owned.isActive ? (
                        <>
                          <Power className="w-4 h-4" />
                          Active
                        </>
                      ) : (
                        <>
                          <PowerOff className="w-4 h-4" />
                          Inactive
                        </>
                      )}
                    </div>
                    {/* Expand/Collapse */}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setExpandedPickaxe(isExpanded ? null : owned.nft.id)}
                    >
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Deposit Balance</span>
                    <span className={colors.text}>
                      {owned.depositBalance.toFixed(2)} / {owned.threshold} ALGO
                    </span>
                  </div>
                  <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        owned.nft.color === 'yellow' ? 'bg-yellow-500' :
                        owned.nft.color === 'slate' ? 'bg-slate-400' :
                        'bg-orange-500'
                      }`}
                      style={{ width: `${Math.min(progressPercent, 100)}%` }}
                    />
                  </div>
                  <div className="text-xs text-slate-500 text-right">
                    {progressPercent.toFixed(0)}% to next auto-swap
                  </div>
                </div>

                {/* Action Buttons (always visible) */}
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1 gap-2" disabled>
                    <Wallet className="w-4 h-4" />
                    Deposit ALGO
                  </Button>
                  <Button
                    variant={owned.isActive ? 'secondary' : 'default'}
                    className="flex-1 gap-2"
                    disabled
                  >
                    {owned.isActive ? (
                      <>
                        <PowerOff className="w-4 h-4" />
                        Deactivate
                      </>
                    ) : (
                      <>
                        <Power className="w-4 h-4" />
                        Activate
                      </>
                    )}
                  </Button>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="pt-4 border-t border-slate-800 space-y-4">
                    {/* Stats Grid */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                        <div className="text-xs text-slate-400">Total Mined</div>
                        <div className={`font-bold ${colors.text}`}>
                          {owned.totalMined.toFixed(4)} {owned.nft.targetAsset.ticker}
                        </div>
                      </div>
                      <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                        <div className="text-xs text-slate-400">Threshold</div>
                        <div className="font-bold text-white">{owned.threshold} ALGO</div>
                      </div>
                      <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                        <div className="text-xs text-slate-400">Swaps</div>
                        <div className="font-bold text-white">{owned.swapHistory.length}</div>
                      </div>
                    </div>

                    {/* Swap History */}
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium flex items-center gap-2">
                        <ArrowRightLeft className="w-4 h-4 text-slate-400" />
                        Recent Swaps
                      </h4>
                      {owned.swapHistory.length === 0 ? (
                        <p className="text-sm text-slate-500 text-center py-4">
                          No swaps yet. Keep depositing ALGO!
                        </p>
                      ) : (
                        <div className="space-y-2">
                          {owned.swapHistory.slice(0, 3).map((swap) => (
                            <div
                              key={swap.id}
                              className="flex items-center justify-between bg-slate-800/30 rounded-lg px-3 py-2 text-sm"
                            >
                              <div className="text-slate-400">{swap.date}</div>
                              <div className="flex items-center gap-2">
                                <span className="text-slate-300">{swap.algoAmount} ALGO</span>
                                <ArrowRightLeft className="w-3 h-3 text-slate-500" />
                                <span className={colors.text}>
                                  {swap.targetAmount.toFixed(4)} {swap.targetTicker}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Settings */}
                    <div className="flex justify-end">
                      <Button variant="ghost" size="sm" className="text-slate-400" disabled>
                        Configure Settings
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Add More Pickaxes CTA */}
      <Card className="bg-slate-900/30 border-dashed border-slate-700 hover:border-orange-500/50 transition-colors cursor-pointer">
        <CardContent className="py-6 text-center">
          <Button variant="ghost" className="gap-2 text-slate-400 hover:text-orange-500" disabled>
            <Pickaxe className="w-5 h-5" />
            Add Another Pickaxe
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
