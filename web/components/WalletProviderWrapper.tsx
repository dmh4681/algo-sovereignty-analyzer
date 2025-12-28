'use client'

import { WalletProvider, WalletManager, WalletId, NetworkId } from '@txnlab/use-wallet-react'
import { useMemo, type ReactNode } from 'react'

interface WalletProviderWrapperProps {
  children: ReactNode
}

// Create wallet manager configuration
function createWalletManager() {
  return new WalletManager({
    wallets: [
      {
        id: WalletId.PERA,
        options: {
          // Enable compact UI for mobile screens
          compactMode: true,
          // Show toast for transaction signing guidance
          shouldShowSignTxnToast: true,
        },
      },
      {
        id: WalletId.DEFLY,
        options: {
          shouldShowSignTxnToast: true,
        },
      },
      WalletId.EXODUS,
      WalletId.LUTE,
      WalletId.KIBISIS,
    ],
    defaultNetwork: NetworkId.MAINNET,
  })
}

export function WalletProviderWrapper({ children }: WalletProviderWrapperProps) {
  // Create wallet manager once and memoize it
  const walletManager = useMemo(() => createWalletManager(), [])

  return (
    <WalletProvider manager={walletManager}>
      {children}
    </WalletProvider>
  )
}
