'use client'

import Link from 'next/link'
import { NavDropdown } from './NavDropdown'
import { HeaderWalletStatus } from './HeaderWalletStatus'

const networkItems = [
  {
    label: 'Network Health',
    href: '/network',
    description: 'Stake distribution & decentralization metrics',
  },
  {
    label: 'Run a Node',
    href: '/network/run-a-node',
    description: 'Guide to running your own participation node',
  },
]

const aboutItems = [
  {
    label: 'About',
    href: '/about',
    description: 'Our mission and methodology',
  },
  {
    label: 'Whitepaper',
    href: '/whitepaper',
    description: 'The philosophy of financial sovereignty',
  },
  {
    label: 'Philosophy',
    href: '/philosophy',
    description: 'Why sound money matters',
  },
]

export function MainNav() {
  return (
    <nav className="flex items-center gap-4">
      <NavDropdown
        label="Network"
        items={networkItems}
        hoverColor="text-cyan-500"
      />
      <NavDropdown
        label="About"
        items={aboutItems}
        hoverColor="text-orange-500"
      />
      <Link
        href="/training"
        className="text-sm text-slate-400 hover:text-blue-500 transition-colors"
      >
        Training
      </Link>
      <Link
        href="/news"
        className="text-sm text-slate-400 hover:text-yellow-500 transition-colors"
      >
        News
      </Link>
      <Link
        href="/research"
        className="text-sm text-slate-400 hover:text-purple-500 transition-colors"
      >
        Research
      </Link>
      <Link
        href="/arbitrage"
        className="text-sm text-slate-400 hover:text-green-500 transition-colors"
      >
        Arbitrage
      </Link>
      <Link
        href="/gold-tracker"
        className="text-sm text-slate-400 hover:text-amber-500 transition-colors"
      >
        Gold Miners
      </Link>
      <Link
        href="/silver-tracker"
        className="text-sm text-slate-400 hover:text-slate-300 transition-colors"
      >
        Silver Miners
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
  )
}
