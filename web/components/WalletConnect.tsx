'use client'

import dynamic from 'next/dynamic'
import { Button } from '@/components/ui/button'
import { Link as LinkIcon } from 'lucide-react'

// Dynamically import the actual component with SSR disabled
const WalletConnectContent = dynamic(
  () => import('./WalletConnectContent'),
  {
    ssr: false,
    loading: () => (
      <Button
        size="lg"
        className="w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold"
        disabled
      >
        <LinkIcon className="w-4 h-4 mr-2" />
        Connect Wallet
      </Button>
    ),
  }
)

interface WalletConnectProps {
  onConnect?: (address: string) => void
  redirectOnConnect?: boolean
}

export function WalletConnect({ onConnect, redirectOnConnect = true }: WalletConnectProps) {
  return <WalletConnectContent onConnect={onConnect} redirectOnConnect={redirectOnConnect} />
}
