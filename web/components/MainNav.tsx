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
  {
    label: 'Research',
    href: '/research',
    description: 'Algorand infrastructure research report',
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

const preciousMetalsItems = [
  {
    label: 'Arbitrage',
    href: '/arbitrage',
    description: 'Meld Gold/Silver vs spot price analysis',
  },
  {
    label: 'Gold Miners',
    href: '/gold-tracker',
    description: 'Track major gold mining companies',
  },
  {
    label: 'Silver Miners',
    href: '/silver-tracker',
    description: 'Track major silver mining companies',
  },
  {
    label: 'Inflation Charts',
    href: '/inflation-charts',
    description: 'Gold in real terms, M2 comparison, purchasing power',
  },
  {
    label: 'Central Banks',
    href: '/central-bank-gold',
    description: 'Global CB gold holdings & de-dollarization',
  },
  {
    label: 'Earnings Calendar',
    href: '/earnings-calendar',
    description: 'Track miner quarterly reports and price reactions',
  },
  {
    label: 'Physical Premiums',
    href: '/premium-tracker',
    description: 'Compare dealer premiums on coins, bars & rounds',
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
        label="Precious Metals"
        items={preciousMetalsItems}
        hoverColor="text-amber-500"
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
