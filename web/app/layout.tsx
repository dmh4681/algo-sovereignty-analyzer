import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'Algorand Sovereignty Analyzer',
  description: 'Measure your financial sovereignty. Analyze any Algorand wallet and calculate your freedom.',
  keywords: ['Algorand', 'crypto', 'sovereignty', 'Bitcoin', 'wallet analyzer', 'financial freedom'],
  authors: [{ name: 'Sovereignty Labs' }],
  openGraph: {
    title: 'Algorand Sovereignty Analyzer',
    description: 'Measure your financial sovereignty. Analyze any Algorand wallet.',
    type: 'website',
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
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center text-white font-bold">
                  S
                </div>
                <span className="font-semibold text-lg hidden sm:inline">Sovereignty Analyzer</span>
              </Link>
              <nav className="flex items-center gap-6">
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
      </body>
    </html>
  )
}
