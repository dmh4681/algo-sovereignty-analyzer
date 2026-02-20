'use client'

import dynamic from 'next/dynamic'
import { Button } from '@/components/ui/button'
import { Link as LinkIcon } from 'lucide-react'

/**
 * Dynamically imported wallet connection component with SSR disabled.
 *
 * The wallet connection logic (via @txnlab/use-wallet) depends on browser APIs
 * (window, localStorage, Web Crypto) that are unavailable during server-side
 * rendering. Dynamic import with `ssr: false` ensures the component only loads
 * on the client. A disabled "Connect Wallet" button is shown as a placeholder
 * during the loading phase.
 *
 * The actual wallet logic lives in `WalletConnectContent.tsx`, which integrates
 * with Pera Wallet, Defly, and WalletConnect providers.
 */
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

/**
 * Props for the {@link WalletConnect} component.
 *
 * @property onConnect - Callback invoked with the connected wallet's Algorand
 *   address string when a connection is established.
 * @property redirectOnConnect - If true, navigates to the analysis page
 *   (`/analyze?address=...`) after a successful wallet connection. Defaults to true.
 * @property autoRedirect - If true, automatically triggers the redirect without
 *   requiring additional user interaction after connection. Defaults to false.
 */
interface WalletConnectProps {
  onConnect?: (address: string) => void
  redirectOnConnect?: boolean
  autoRedirect?: boolean
}

/**
 * Wallet connection button that integrates with Algorand wallet providers.
 *
 * This is a thin wrapper around the dynamically-imported `WalletConnectContent`
 * component. It exists to handle the SSR boundary -- the actual wallet provider
 * logic (Pera, Defly, WalletConnect) requires browser APIs and cannot be
 * server-rendered.
 *
 * Usage contexts:
 * - Landing page: with `redirectOnConnect={true}` to navigate to analysis
 * - Embedded in other pages: with `onConnect` callback for custom handling
 *
 * @param props - Component props
 *
 * @example
 * ```tsx
 * // Landing page usage - connects and redirects to /analyze
 * <WalletConnect redirectOnConnect autoRedirect />
 *
 * // Custom handler usage
 * <WalletConnect
 *   onConnect={(addr) => console.log('Connected:', addr)}
 *   redirectOnConnect={false}
 * />
 * ```
 */
export function WalletConnect({ onConnect, redirectOnConnect = true, autoRedirect = false }: WalletConnectProps) {
  return <WalletConnectContent onConnect={onConnect} redirectOnConnect={redirectOnConnect} autoRedirect={autoRedirect} />
}
