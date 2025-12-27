'use client'

import { useState, useEffect } from 'react'
import { useWallet } from '@txnlab/use-wallet-react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { getWalletParticipation } from '@/lib/api'
import { WalletParticipationResponse } from '@/lib/types'
import {
  Wallet,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ExternalLink,
  Loader2,
  PartyPopper,
  Clock,
  TrendingUp
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

// Wallet metadata with colors
const WALLET_COLORS: Record<string, string> = {
  'pera': 'bg-yellow-500',
  'defly': 'bg-violet-500',
  'exodus': 'bg-purple-500',
  'kibisis': 'bg-blue-500',
  'lute': 'bg-green-500',
}

// Format rounds to approximate time
function formatRoundsToTime(rounds: number): string {
  // Algorand: ~3.3 seconds per block
  const seconds = rounds * 3.3
  const days = Math.floor(seconds / 86400)
  if (days > 365) {
    const years = (days / 365).toFixed(1)
    return `~${years} years`
  }
  if (days > 30) {
    const months = Math.floor(days / 30)
    return `~${months} month${months > 1 ? 's' : ''}`
  }
  if (days > 0) {
    return `~${days} day${days > 1 ? 's' : ''}`
  }
  const hours = Math.floor(seconds / 3600)
  return `~${hours} hour${hours > 1 ? 's' : ''}`
}

export default function YourContributionSection() {
  const { wallets, activeAccount, activeWallet, isReady } = useWallet()
  const [participation, setParticipation] = useState<WalletParticipationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [connecting, setConnecting] = useState<string | null>(null)

  // Fetch participation status when wallet is connected
  useEffect(() => {
    if (activeAccount?.address) {
      fetchParticipation(activeAccount.address)
    } else {
      setParticipation(null)
    }
  }, [activeAccount?.address])

  const fetchParticipation = async (address: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getWalletParticipation(address)
      setParticipation(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch participation status')
    } finally {
      setLoading(false)
    }
  }

  const handleConnect = async (walletId: string) => {
    const wallet = wallets.find(w => w.id === walletId)
    if (!wallet) return

    setConnecting(walletId)
    try {
      await wallet.connect()
      setShowConnectModal(false)
    } catch (err) {
      console.error('Connection failed:', err)
    } finally {
      setConnecting(null)
    }
  }

  // Not ready yet
  if (!isReady) {
    return <Skeleton className="h-64" />
  }

  // No wallet connected
  if (!activeAccount) {
    return (
      <>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700">
          <CardContent className="py-8">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-slate-700/50 flex items-center justify-center">
                <Wallet className="w-8 h-8 text-slate-400" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-200">Your Contribution</h3>
                <p className="text-slate-400 mt-1">
                  Connect your wallet to see your contribution to network decentralization
                </p>
              </div>
              <Button
                onClick={() => setShowConnectModal(true)}
                className="bg-orange-600 hover:bg-orange-500"
              >
                <Wallet className="w-4 h-4 mr-2" />
                Connect Wallet
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Connect Wallet Modal */}
        <Dialog open={showConnectModal} onOpenChange={setShowConnectModal}>
          <DialogContent className="bg-slate-900 border-slate-700 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-xl">Connect Wallet</DialogTitle>
              <DialogDescription className="text-slate-400">
                Connect your wallet to check your participation status
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-2 mt-4">
              {wallets.map((wallet) => {
                const color = WALLET_COLORS[wallet.id] || 'bg-slate-500'
                const isConnecting = connecting === wallet.id

                return (
                  <Button
                    key={wallet.id}
                    onClick={() => handleConnect(wallet.id)}
                    disabled={connecting !== null}
                    className="w-full h-14 bg-slate-800 hover:bg-slate-700 border border-slate-700 justify-start"
                    variant="outline"
                  >
                    <div className="flex items-center gap-3 w-full">
                      <div className={`w-8 h-8 ${color} rounded-lg flex items-center justify-center overflow-hidden`}>
                        {wallet.metadata.icon ? (
                          <img
                            src={wallet.metadata.icon}
                            alt={wallet.metadata.name}
                            className="w-6 h-6"
                          />
                        ) : (
                          <span className="text-lg text-white font-bold">
                            {wallet.metadata.name.charAt(0)}
                          </span>
                        )}
                      </div>
                      <span className="font-medium">{wallet.metadata.name}</span>
                      {isConnecting && (
                        <Loader2 className="w-4 h-4 animate-spin text-orange-500 ml-auto" />
                      )}
                    </div>
                  </Button>
                )
              })}
            </div>
          </DialogContent>
        </Dialog>
      </>
    )
  }

  // Loading participation data
  if (loading) {
    return (
      <Card className="bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border-purple-500/30">
        <CardContent className="py-8">
          <div className="flex items-center justify-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
            <span className="text-slate-400">Checking participation status...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/30">
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center space-y-4">
            <AlertTriangle className="w-12 h-12 text-red-400" />
            <div>
              <h3 className="text-lg font-semibold text-slate-200">Failed to Load</h3>
              <p className="text-slate-400 mt-1">{error}</p>
            </div>
            <Button
              onClick={() => fetchParticipation(activeAccount.address)}
              variant="outline"
              className="border-red-500/50"
            >
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Wallet connected but no data
  if (!participation) {
    return null
  }

  // Wallet is participating
  if (participation.is_participating) {
    return (
      <Card className="bg-gradient-to-br from-green-500/10 via-emerald-500/10 to-cyan-500/10 border-green-500/40">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <CardTitle className="text-green-400">You&apos;re Contributing!</CardTitle>
                <CardDescription className="flex items-center gap-2">
                  <span className="font-mono text-xs">
                    {activeAccount.address.slice(0, 8)}...{activeAccount.address.slice(-6)}
                  </span>
                  <a
                    href={`https://explorer.perawallet.app/address/${activeAccount.address}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-500 hover:text-green-400"
                  >
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2 text-green-400">
              <PartyPopper className="w-5 h-5" />
              <span className="text-sm font-medium">Online</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Stake Amount */}
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-4 h-4 text-green-400" />
                <span className="text-sm text-slate-400">Your Stake</span>
              </div>
              <div className="text-2xl font-bold text-slate-200">
                {participation.balance_algo.toLocaleString(undefined, { maximumFractionDigits: 0 })} ALGO
              </div>
              <div className="text-xs text-green-400 mt-1">
                {participation.stake_percentage.toFixed(6)}% of online stake
              </div>
            </div>

            {/* Contribution Tier */}
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="text-sm text-slate-400 mb-1">Contribution Tier</div>
              <div className="text-xl font-bold text-purple-400">
                {participation.contribution_tier}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {participation.balance_algo >= 30000 ? 'Incentive Eligible' : 'Need 30k+ for rewards'}
              </div>
            </div>

            {/* Key Status */}
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span className="text-sm text-slate-400">Key Status</span>
              </div>
              {participation.participation_key ? (
                <>
                  <div className={`text-lg font-bold ${participation.participation_key.is_expired ? 'text-red-400' : 'text-cyan-400'}`}>
                    {participation.participation_key.is_expired ? 'EXPIRED' : 'Valid'}
                  </div>
                  {participation.participation_key.rounds_remaining && !participation.participation_key.is_expired && (
                    <div className="text-xs text-slate-500 mt-1">
                      {formatRoundsToTime(participation.participation_key.rounds_remaining)} remaining
                    </div>
                  )}
                  {participation.participation_key.is_expired && (
                    <div className="text-xs text-red-400 mt-1">
                      Re-register your participation key
                    </div>
                  )}
                </>
              ) : (
                <div className="text-lg font-bold text-slate-400">Unknown</div>
              )}
            </div>
          </div>

          {/* Celebration message */}
          <div className="mt-4 bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
            <p className="text-green-400">
              You&apos;re helping secure the Algorand network! Every node makes the network stronger.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Wallet is NOT participating
  return (
    <Card className="bg-gradient-to-br from-slate-800/50 to-slate-700/30 border-slate-600">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-slate-600/50 flex items-center justify-center">
              <XCircle className="w-6 h-6 text-slate-400" />
            </div>
            <div>
              <CardTitle className="text-slate-300">Not Participating</CardTitle>
              <CardDescription className="flex items-center gap-2">
                <span className="font-mono text-xs">
                  {activeAccount.address.slice(0, 8)}...{activeAccount.address.slice(-6)}
                </span>
                <a
                  href={`https://explorer.perawallet.app/address/${activeAccount.address}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-500 hover:text-slate-400"
                >
                  <ExternalLink className="w-3 h-3" />
                </a>
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2 text-slate-500">
            <span className="text-sm font-medium">Offline</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Balance */}
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-sm text-slate-400 mb-1">Your Balance</div>
            <div className="text-2xl font-bold text-slate-200">
              {participation.balance_algo.toLocaleString(undefined, { maximumFractionDigits: 0 })} ALGO
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {participation.contribution_tier}
            </div>
          </div>

          {/* Status */}
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-sm text-slate-400 mb-1">Status</div>
            <div className="text-lg font-bold text-orange-400">
              {participation.balance_algo >= 30000 ? 'Eligible but Offline' : 'Observer'}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {participation.balance_algo >= 30000
                ? 'You could earn rewards by running a node'
                : 'Running a node still helps decentralization'}
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-4 bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h4 className="font-semibold text-orange-400">Start Contributing</h4>
              <p className="text-sm text-slate-400 mt-1">
                Run a participation node to help secure Algorand
                {participation.balance_algo >= 30000 && ' and earn staking rewards'}
              </p>
            </div>
            <a
              href="https://developer.algorand.org/docs/run-a-node/participate/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-500 rounded-lg text-white text-sm font-medium transition-colors whitespace-nowrap"
            >
              Learn How
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
