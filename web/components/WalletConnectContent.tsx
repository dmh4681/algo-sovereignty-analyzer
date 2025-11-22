'use client'

import { useWallet, type Wallet } from '@txnlab/use-wallet-react'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Loader2, Link as LinkIcon } from 'lucide-react'

// Wallet metadata with icons and descriptions
const WALLET_INFO: Record<string, { name: string; icon: string; description: string; color: string }> = {
  'pera': {
    name: 'Pera Wallet',
    icon: '/wallets/pera.svg',
    description: 'Most popular Algorand wallet',
    color: 'bg-yellow-500',
  },
  'defly': {
    name: 'Defly Wallet',
    icon: '/wallets/defly.svg',
    description: 'Advanced DeFi features',
    color: 'bg-violet-500',
  },
  'exodus': {
    name: 'Exodus Wallet',
    icon: '/wallets/exodus.svg',
    description: 'Multi-chain support',
    color: 'bg-purple-500',
  },
  'kibisis': {
    name: 'Kibisis Wallet',
    icon: '/wallets/kibisis.svg',
    description: 'Browser extension wallet',
    color: 'bg-blue-500',
  },
  'lute': {
    name: 'Lute Wallet',
    icon: '/wallets/lute.svg',
    description: 'Web-based wallet',
    color: 'bg-green-500',
  },
}

interface WalletConnectContentProps {
  onConnect?: (address: string) => void
  redirectOnConnect?: boolean
}

export default function WalletConnectContent({ onConnect, redirectOnConnect = true }: WalletConnectContentProps) {
  const { wallets, activeAccount, activeWallet } = useWallet()
  const [showModal, setShowModal] = useState(false)
  const [connecting, setConnecting] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const handleConnect = async (wallet: Wallet) => {
    setConnecting(wallet.id)
    setError(null)

    try {
      const accounts = await wallet.connect()
      setShowModal(false)

      if (accounts && accounts.length > 0) {
        const address = accounts[0].address
        onConnect?.(address)

        if (redirectOnConnect) {
          router.push(`/analyze?address=${address}`)
        }
      }
    } catch (err) {
      console.error('Connection failed:', err)
      setError(err instanceof Error ? err.message : 'Failed to connect wallet. Please try again.')
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnect = async () => {
    if (activeWallet) {
      await activeWallet.disconnect()
    }
  }

  if (activeAccount) {
    return (
      <div className="flex items-center gap-3">
        <div className="text-sm">
          <span className="text-slate-400">Connected:</span>{' '}
          <span className="text-orange-500 font-mono">
            {activeAccount.address.slice(0, 6)}...{activeAccount.address.slice(-4)}
          </span>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleDisconnect}
          className="border-slate-700"
        >
          Disconnect
        </Button>
      </div>
    )
  }

  return (
    <>
      <Button
        onClick={() => setShowModal(true)}
        size="lg"
        className="w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold"
      >
        <LinkIcon className="w-4 h-4 mr-2" />
        Connect Wallet
      </Button>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-2xl">Connect Your Wallet</DialogTitle>
            <DialogDescription className="text-slate-400">
              Choose your preferred Algorand wallet to analyze your sovereignty
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 mt-4">
            {wallets.map((wallet) => {
              const info = WALLET_INFO[wallet.id] || {
                name: wallet.metadata.name,
                icon: wallet.metadata.icon,
                description: 'Algorand wallet',
                color: 'bg-slate-500',
              }
              const isConnecting = connecting === wallet.id

              return (
                <Button
                  key={wallet.id}
                  onClick={() => handleConnect(wallet)}
                  disabled={connecting !== null}
                  className="w-full h-16 bg-slate-800 hover:bg-slate-700 border border-slate-700 justify-start text-left"
                  variant="outline"
                >
                  <div className="flex items-center gap-4 w-full">
                    <div className={`w-10 h-10 ${info.color} rounded-lg flex items-center justify-center overflow-hidden`}>
                      {wallet.metadata.icon ? (
                        <img
                          src={wallet.metadata.icon}
                          alt={info.name}
                          className="w-8 h-8"
                        />
                      ) : (
                        <span className="text-2xl text-white font-bold">
                          {info.name.charAt(0)}
                        </span>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold">{info.name}</div>
                      <div className="text-xs text-slate-400">{info.description}</div>
                    </div>
                    {isConnecting && (
                      <Loader2 className="w-5 h-5 animate-spin text-orange-500" />
                    )}
                  </div>
                </Button>
              )
            })}
          </div>

          {connecting && (
            <div className="text-center text-sm text-slate-400 mt-4">
              Opening wallet... Please approve the connection in your wallet app.
            </div>
          )}

          {error && (
            <div className="text-center text-sm text-red-400 mt-4 p-3 bg-red-500/10 rounded-lg border border-red-500/20">
              {error}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
