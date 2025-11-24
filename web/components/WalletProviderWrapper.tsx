'use client'

import { WalletProvider, WalletManager, WalletId, NetworkId } from '@txnlab/use-wallet-react'
import { useMemo, useEffect, useState, type ReactNode } from 'react'

interface WalletProviderWrapperProps {
  children: ReactNode
}

export function WalletProviderWrapper({ children }: WalletProviderWrapperProps) {
  const [mounted, setMounted] = useState(false)

  const walletManager = useMemo(() => {
    return new WalletManager({
      wallets: [
        WalletId.PERA,
        WalletId.DEFLY,
        WalletId.EXODUS,
        WalletId.LUTE,
        WalletId.KIBISIS,
      ],
      defaultNetwork: NetworkId.MAINNET,
    })
  }, [])

  useEffect(() => {
    setMounted(true)
  }, [])



  return (
    <WalletProvider manager={walletManager}>
      {children}
    </WalletProvider>
  )
}
