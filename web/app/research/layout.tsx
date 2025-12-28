import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Algorand 2025 Research Report | Sovereignty Analyzer',
  description: 'Comprehensive analysis of Algorand blockchain developments in 2025: decentralization progress, P2P networking, post-quantum security, and the Project King Safety supply cap debate.',
  keywords: ['Algorand', 'ALGO', '2025', 'decentralization', 'blockchain research', 'cryptocurrency', 'Project King Safety', 'post-quantum', 'P2P network'],
  authors: [{ name: 'Sovereignty Labs' }],
  openGraph: {
    title: 'Algorand 2025: State of the Chain Report',
    description: 'Foundation stake dropped from 63% to 20%. P2P networking live. Post-quantum security operational. Deep dive into 2025 developments.',
    type: 'article',
    publishedTime: '2025-12-27',
    authors: ['Sovereignty Labs'],
    tags: ['Algorand', 'blockchain', 'decentralization', 'research'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Algorand 2025: State of the Chain Report',
    description: 'Comprehensive analysis: 80% community stake, P2P networking, post-quantum security, and the supply cap debate.',
  },
}

export default function ResearchLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
