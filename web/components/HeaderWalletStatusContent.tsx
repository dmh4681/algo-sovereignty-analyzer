'use client'

import { useWallet } from '@txnlab/use-wallet-react'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Loader2, Wallet, ChevronDown, ExternalLink, AlertCircle } from 'lucide-react'

// Wallet metadata with colors
const WALLET_COLORS: Record<string, string> = {
  'pera': 'bg-yellow-500',
  'defly': 'bg-violet-500',
  'exodus': 'bg-purple-500',
  'kibisis': 'bg-blue-500',
  'lute': 'bg-green-500',
}

// Detect if user is on mobile
function isMobileDevice(): boolean {
  if (typeof window === 'undefined') return false
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

export default function HeaderWalletStatusContent() {
  const { wallets, activeAccount, activeWallet, isReady } = useWallet()
  const [showModal, setShowModal] = useState(false)
  const [connecting, setConnecting] = useState<string | null>(null)
  const [showAccountMenu, setShowAccountMenu] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [isMobile, setIsMobile] = useState(false)
  const router = useRouter()

  // Detect mobile on mount
  useEffect(() => {
    setIsMobile(isMobileDevice())
  }, [])

  const handleConnect = async (walletId: string) => {
    const wallet = wallets.find(w => w.id === walletId)
    if (!wallet) return

    setConnecting(walletId)
    setConnectionError(null)

    try {
      const accounts = await wallet.connect()
      setShowModal(false)

      if (accounts && accounts.length > 0) {
        router.push(`/analyze?address=${accounts[0].address}`)
      }
    } catch (err) {
      console.error('Connection failed:', err)
      const errorMessage = err instanceof Error ? err.message : 'Connection failed'

      // On mobile, if browser blocks the redirect, show helpful message
      if (isMobile && (walletId === 'pera' || walletId === 'defly')) {
        setConnectionError(
          `If the wallet app didn't open, try opening ${wallet.metadata.name} directly and scanning a QR code, or use the wallet's built-in browser.`
        )
      } else {
        setConnectionError(errorMessage)
      }
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnect = async () => {
    if (activeWallet) {
      await activeWallet.disconnect()
      setShowAccountMenu(false)
    }
  }

  const handleAnalyze = () => {
    if (activeAccount) {
      router.push(`/analyze?address=${activeAccount.address}`)
      setShowAccountMenu(false)
    }
  }

  // Don't render until wallet manager is ready
  if (!isReady) {
    return null
  }

  // Show connected state with account menu
  if (activeAccount && activeWallet) {
    const walletColor = WALLET_COLORS[activeWallet.id] || 'bg-slate-500'

    return (
      <div className="relative">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAccountMenu(!showAccountMenu)}
          className="border-slate-700 bg-slate-800/50 hover:bg-slate-700 gap-2"
        >
          <div className={`w-2 h-2 rounded-full ${walletColor}`} />
          <span className="font-mono text-xs">
            {activeAccount.address.slice(0, 4)}...{activeAccount.address.slice(-4)}
          </span>
          <ChevronDown className="w-3 h-3 text-slate-400" />
        </Button>

        {showAccountMenu && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowAccountMenu(false)}
            />

            {/* Menu */}
            <div className="absolute right-0 top-full mt-2 w-64 bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-50 overflow-hidden">
              <div className="p-3 border-b border-slate-800">
                <div className="text-xs text-slate-400 mb-1">Connected with {activeWallet.metadata.name}</div>
                <div className="font-mono text-sm text-slate-200 break-all">
                  {activeAccount.address}
                </div>
              </div>
              <div className="p-2 space-y-1">
                <button
                  onClick={handleAnalyze}
                  className="w-full text-left px-3 py-2 text-sm rounded hover:bg-slate-800 transition-colors"
                >
                  Analyze this wallet
                </button>
                <button
                  onClick={handleDisconnect}
                  className="w-full text-left px-3 py-2 text-sm rounded hover:bg-slate-800 transition-colors text-red-400"
                >
                  Disconnect
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    )
  }

  // Show connect button
  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowModal(true)}
        className="border-slate-700 bg-slate-800/50 hover:bg-slate-700 gap-2"
      >
        <Wallet className="w-4 h-4" />
        <span className="hidden sm:inline">Connect</span>
      </Button>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl">Connect Wallet</DialogTitle>
            <DialogDescription className="text-slate-400">
              Connect your wallet to analyze your holdings
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

          {connecting && (
            <div className="text-center text-sm text-slate-400 mt-3">
              <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
              {isMobile
                ? 'Opening wallet app... If nothing happens, check if the app is installed.'
                : 'Connecting... Check your wallet app or browser extension.'}
            </div>
          )}

          {connectionError && (
            <div className="mt-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <div className="flex gap-2 text-sm text-amber-400">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{connectionError}</span>
              </div>
            </div>
          )}

          {/* Mobile-specific help */}
          {isMobile && !connecting && (
            <div className="mt-4 pt-4 border-t border-slate-700">
              <div className="text-xs text-slate-500 mb-2">
                Having trouble connecting?
              </div>
              <ul className="text-xs text-slate-400 space-y-1">
                <li>• Make sure you have the wallet app installed</li>
                <li>• Try using the wallet's built-in browser</li>
                <li>• You can also enter your address manually on the home page</li>
              </ul>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
