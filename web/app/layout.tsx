import type { Metadata, Viewport } from 'next'
import Link from 'next/link'
import Image from 'next/image'
import './globals.css'
import { WalletProviderWrapper } from '@/components/WalletProviderWrapper'
import { HeaderWalletStatus } from '@/components/HeaderWalletStatus'

export const viewport: Viewport = {
  themeColor: '#f97316',
}

export const metadata: Metadata = {
  title: 'Algorand Sovereignty Analyzer',
  description: 'Measure your financial sovereignty. Analyze any Algorand wallet and calculate your freedom.',
  keywords: ['Algorand', 'crypto', 'sovereignty', 'Bitcoin', 'wallet analyzer', 'financial freedom'],
  authors: [{ name: 'Sovereignty Labs' }],
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-96x96.png', sizes: '96x96', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
  },
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'Algo Sovereignty',
  },
  openGraph: {
    title: 'Algorand Sovereignty Analyzer',
    description: 'Measure your financial sovereignty based on your Algorand holdings.',
    type: 'website',
    siteName: 'Algorand Sovereignty Analyzer',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-50 antialiased">
        <WalletProviderWrapper>
          <div className="relative min-h-screen">
            {/* Background gradient */}
            <div className="fixed inset-0 -z-10">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-96 bg-orange-500/5 blur-3xl rounded-full" />
              <div className="absolute bottom-0 right-0 w-96 h-96 bg-orange-500/5 blur-3xl rounded-full" />
            </div>

            {/* Header */}
            <header className="border-b border-slate-800/50 backdrop-blur-sm sticky top-0 z-50">
              <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                  <Image
                    src="/android-chrome-192x192.png"
                    alt="Algo Sovereignty Logo"
                    width={32}
                    height={32}
                    className="rounded-lg"
                  />
                  <span className="font-semibold text-lg hidden sm:inline">Sovereignty Analyzer</span>
                </Link>
                <nav className="flex items-center gap-4">
                  <Link href="/philosophy" className="text-sm text-slate-400 hover:text-orange-500 transition-colors">
                    Philosophy
                  </Link>
                  <Link href="/training" className="text-sm text-slate-400 hover:text-blue-500 transition-colors">
                    Training
                  </Link>
                  <Link href="/news" className="text-sm text-slate-400 hover:text-yellow-500 transition-colors">
                    News
                  </Link>
                  <HeaderWalletStatus />
                  <a
                    href="https://github.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    GitHub
                  </a>
                </nav>
              </div>
            </header>

            {/* Main content */}
            <main className="container mx-auto px-4 py-8">
              {children}
            </main>

            {/* Footer */}
            <footer className="border-t border-slate-800/50 mt-auto">
              <div className="container mx-auto px-4 py-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
                  <p>Built for financial sovereignty</p>
                  <p>Powered by Algorand</p>
                </div>
              </div>
            </footer>
          </div>
        </WalletProviderWrapper >
      </body >
    </html >
  )
}
