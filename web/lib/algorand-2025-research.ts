export interface ResearchStat {
  label: string
  value: string
  change: string
  description: string
}

export interface TimelineEvent {
  date: string
  title: string
  description: string
  category: 'protocol' | 'governance' | 'ecosystem' | 'security'
  sovereigntyImpact?: 'positive' | 'negative' | 'neutral'
}

export interface EcosystemProject {
  name: string
  category: 'DeFi' | 'RWA' | 'Gaming' | 'Identity' | 'Infrastructure'
  status: string
  description: string
  sovereigntyRelevant: boolean
  url?: string
}

export interface InstitutionalAdoption {
  name: string
  region: string
  users: string
  description: string
}

export interface ResearchSource {
  id: number
  title: string
  url: string
}

export const ALGORAND_2025_RESEARCH = {
  lastUpdated: '2025-12-27',
  source: 'Gemini Deep Research',

  executiveSummary: `2025 marked a definitive inflection point for Algorand. The network achieved massive decentralization (Foundation stake dropped from 63% to 20%), launched P2P networking to remove relay node centralization, and became the first major L1 to operationalize post-quantum security. However, the "Project King Safety" debate around uncapping the 10B supply to fund validator rewards highlights the tension between sound money principles and network security economics.`,

  keyStats: [
    { label: 'Validator Nodes', value: '~2,000', change: '+121%', description: 'From 900 in late 2024' },
    { label: 'Foundation Stake', value: '20%', change: '-43%', description: 'Down from 63%' },
    { label: 'Community Stake', value: '80%', change: '+43%', description: 'Decentralization achieved' },
    { label: 'Block Time', value: '2.8s', change: '-0.5s', description: 'Dynamic Round Times' },
    { label: 'Combined TVL', value: '$685M', change: '+115%', description: 'DeFi + RWA' },
    { label: 'Reti Pool Stake', value: '480M ALGO', change: 'New', description: 'Non-custodial pooling' }
  ] as ResearchStat[],

  decentralization: {
    foundationStakePercent: 20,
    communityStakePercent: 80,
    nodeCount: 2000,
    nodeGrowthPercent: 121,
    p2pNetworkLive: true,
    relayNodesDependency: 'Hybrid (transitioning to full P2P)',
    highlights: [
      'P2P Gossip Network finalized December 2025 - nodes can discover peers without centralized directory',
      'Consensus Incentivization program launched January 2025 - direct rewards for block production',
      '30,000 ALGO minimum stake for rewards drove professionalization of validator set',
      'Reti Pooling and Valar provide non-custodial delegation for smaller holders',
      'Foundation actively divesting to force ecosystem self-sufficiency'
    ]
  },

  projectKingSafety: {
    issue: 'Foundation treasury depleting by ~January 2027',
    proposal: 'Uncap 10B ALGO supply, introduce tail emissions for validator rewards',
    forArguments: [
      'L1 security is a public good that must be paid for',
      'Without tail emission, security relies entirely on fees',
      'Current fee revenue (~0.001 ALGO) insufficient to incentivize 2,000+ validators'
    ],
    againstArguments: [
      '10B hard cap was fundamental promise of protocol',
      'Uncapping would dilute holders',
      'Damages store-of-value narrative'
    ],
    alternatives: ['Fee market increase', 'MEV capture mechanisms'],
    voteRequirement: '90% supermajority of consensus stake',
    sovereigntyAnalysis: 'This debate is the defining tension between "sound money" principles and practical network sustainability. The outcome will determine if ALGO can claim hard money status.'
  },

  timeline: [
    { date: 'Jan 2025', title: 'Consensus Incentivization Launch', description: 'Direct rewards for block production, 30k ALGO minimum', category: 'governance', sovereigntyImpact: 'positive' },
    { date: 'Feb 2025', title: 'AlgoKit 2.5 Release', description: 'Native Python debugging, one-click localnet setup', category: 'protocol', sovereigntyImpact: 'neutral' },
    { date: 'May 2025', title: 'Dynamic Round Times', description: 'Block times adapt to network load, averaging 2.8s', category: 'protocol', sovereigntyImpact: 'neutral' },
    { date: 'Aug 2025', title: 'P2P Gossip Optimization', description: '30% bandwidth reduction for relay nodes', category: 'protocol', sovereigntyImpact: 'positive' },
    { date: 'Oct 2025', title: 'AVM v10 Upgrade', description: 'ZK-proof support via BN254 curves', category: 'protocol', sovereigntyImpact: 'neutral' },
    { date: 'Oct 2025', title: 'xGov Mainnet Launch', description: 'Community-driven grant allocation, removing Foundation gatekeeper', category: 'governance', sovereigntyImpact: 'positive' },
    { date: 'Nov 2025', title: 'FOLKS Token TGE', description: 'Folks Finance governance token, cross-chain via Wormhole', category: 'ecosystem', sovereigntyImpact: 'neutral' },
    { date: 'Dec 2025', title: 'Post-Quantum Accounts', description: 'Falcon-1024 signatures - first major L1 with NIST quantum resistance', category: 'security', sovereigntyImpact: 'positive' },
    { date: 'Dec 2025', title: 'P2P Network Finalized', description: 'Autonomous peer discovery, removes relay node dependency', category: 'protocol', sovereigntyImpact: 'positive' }
  ] as TimelineEvent[],

  ecosystemProjects: [
    { name: 'Folks Finance', category: 'DeFi', status: 'Dominant - 60% DeFi TVL', description: 'Cross-chain lending via xPortal/Wormhole. FOLKS token launched.', sovereigntyRelevant: true, url: 'https://folks.finance' },
    { name: 'Lofty', category: 'RWA', status: 'Profitable', description: '$99M TVL, $4M rental income paid out. Fractionalized real estate.', sovereigntyRelevant: true, url: 'https://lofty.ai' },
    { name: 'Meld Gold', category: 'RWA', status: 'Expanding', description: 'Supply chain integration, vault verification on-chain. Added copper/platinum.', sovereigntyRelevant: true, url: 'https://meld.gold' },
    { name: 'Tinyman', category: 'DeFi', status: 'Stable', description: '$500M cumulative volume. 40% TINY locked in governance.', sovereigntyRelevant: false, url: 'https://tinyman.org' },
    { name: 'Pact', category: 'DeFi', status: 'Growing', description: '$POW token, Consensus Compatible LP pools (earn fees + staking rewards).', sovereigntyRelevant: true, url: 'https://pact.fi' },
    { name: 'Vestige', category: 'Infrastructure', status: 'Essential', description: '$200M lifetime volume. DEX aggregator and analytics.', sovereigntyRelevant: false, url: 'https://vestige.fi' },
    { name: 'goBTC (Algomint)', category: 'DeFi', status: 'Stable', description: '1:1 BTC bridge. Primary use: collateral in lending markets.', sovereigntyRelevant: true, url: 'https://algomint.io' },
    { name: 'NFDomains', category: 'Identity', status: 'V3 Launch', description: 'Yearly renewal model for sustainability. Permissionless minting.', sovereigntyRelevant: false, url: 'https://nf.domains' },
    { name: 'Alpha Arcade', category: 'Gaming', status: 'New', description: 'Prediction market on Algorand. Sports/political betting.', sovereigntyRelevant: false },
    { name: 'Midas (mTBILL)', category: 'RWA', status: 'New', description: 'Tokenized US Treasury Bills. German-regulated.', sovereigntyRelevant: false }
  ] as EcosystemProject[],

  rwaBreakdown: {
    labels: ['Real Estate', 'Precious Metals', 'Agro-Commodities', 'Govt Bonds', 'Equities'],
    values: [120, 85, 200, 150, 45] // Millions USD
  },

  institutionalAdoption: [
    { name: 'Nubank', region: 'Latin America', users: '100M', description: 'ALGO trading for Brazil/Mexico/Colombia' },
    { name: 'HesabPay', region: 'Afghanistan', users: 'Millions', description: 'Largest humanitarian blockchain payments (UN agencies)' },
    { name: 'Mann Deshi', region: 'India', users: '400,000', description: 'Blockchain credit scores for rural women' },
    { name: 'SEWA', region: 'India', users: 'Millions', description: 'Digital identity for informal workers' },
    { name: 'Pera Mastercard', region: '12 Countries', users: 'N/A', description: 'Self-custodied USDCa spending' }
  ] as InstitutionalAdoption[],

  outlook2026: [
    'Will community vote to uncap supply for security budget?',
    'Can RWA momentum generate sufficient transaction fees?',
    'Will AlgoKit Python onboard next wave of developers?'
  ],

  sources: [
    { id: 1, title: '2025 on Algorand: Roadmap progress', url: 'https://algorand.co/blog/2025-on-algorand-roadmap-progress' },
    { id: 2, title: 'Algorand 2025 roadmap: Web3 core values', url: 'https://algorand.co/blog/web3-core-values-from-algorands-2025-roadmap' },
    { id: 7, title: 'Project King Safety Reddit Discussion', url: 'https://www.reddit.com/r/AlgorandOfficial/comments/1pkdpi8/update_on_the_status_of_the_project_king_safety/' },
    { id: 8, title: '2025 Ecosystem Highlights', url: 'https://algorand.co/blog/2025-on-algorand-2025-ecosystem-highlights' },
    { id: 13, title: 'Q3 2025 Transparency Report', url: 'https://algorand.co/hubfs/Algorand%20Transparency%20Report-Q3-2025_V3%20Final.pdf' }
  ] as ResearchSource[]
}

// Helper function to get sovereignty-relevant projects
export function getSovereigntyRelevantProjects() {
  return ALGORAND_2025_RESEARCH.ecosystemProjects.filter(p => p.sovereigntyRelevant)
}

// Helper function to get positive sovereignty impact events
export function getPositiveSovereigntyEvents() {
  return ALGORAND_2025_RESEARCH.timeline.filter(e => e.sovereigntyImpact === 'positive')
}

// Helper function to get events by category
export function getEventsByCategory(category: TimelineEvent['category']) {
  return ALGORAND_2025_RESEARCH.timeline.filter(e => e.category === category)
}

// Helper function to get projects by category
export function getProjectsByCategory(category: EcosystemProject['category']) {
  return ALGORAND_2025_RESEARCH.ecosystemProjects.filter(p => p.category === category)
}

// Calculate total RWA TVL
export function getTotalRwaTvl() {
  return ALGORAND_2025_RESEARCH.rwaBreakdown.values.reduce((sum, val) => sum + val, 0)
}
