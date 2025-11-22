'use client'

import dynamic from 'next/dynamic'

// Dynamically import the actual component with SSR disabled
const HeaderWalletStatusContent = dynamic(
  () => import('./HeaderWalletStatusContent'),
  {
    ssr: false,
    loading: () => null,
  }
)

export function HeaderWalletStatus() {
  return <HeaderWalletStatusContent />
}
