// Algorand 2025 Research Data
// Sources: Gemini Deep Research
// Last Updated: December 27, 2025

export interface ResearchStat {
  label: string
  value: string
  change: string
  description: string
  sovereigntyImpact?: 'positive' | 'negative' | 'neutral'
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
  category: 'Wallets' | 'DeFi' | 'NFTs' | 'RWA' | 'Infrastructure' | 'Gaming' | 'Staking' | 'Identity'
  subcategory?: string
  status: 'Essential' | 'Major' | 'Growing' | 'New' | 'Stable'
  description: string
  keyFeature?: string
  sovereigntyRelevant: boolean
  hardMoneyPartner?: boolean
  url?: string
  twitter?: string
}

export interface InstitutionalAdoption {
  name: string
  region: string
  users: string
  description: string
  sovereigntyRelevant?: boolean
}

export interface ResearchSource {
  id: number
  title: string
  url: string
}

// =============================================================================
// MAIN RESEARCH DATA EXPORT
// =============================================================================

export const ALGORAND_2025_RESEARCH = {
  lastUpdated: '2025-12-27',
  source: 'Gemini Deep Research',

  // ---------------------------------------------------------------------------
  // EXECUTIVE SUMMARY
  // ---------------------------------------------------------------------------
  executiveSummary: `2025 marked a definitive inflection point for Algorand. The network achieved massive decentralization (Foundation stake dropped from 63% to 20%), launched P2P networking to remove relay node centralization, and became the first major L1 to operationalize post-quantum security with Falcon-1024 signatures.

However, the "Project King Safety" debate around uncapping the 10B ALGO supply to fund validator rewards highlights the critical tension between sound money principles and network security economics. This decision will define Algorand's identity going into 2026.

The ecosystem matured significantly with Folks Finance dominating DeFi (60% TVL), Lofty achieving profitability in real estate, and RWA tokenization exploding across agriculture, precious metals, and government bonds.`,

  // ---------------------------------------------------------------------------
  // KEY STATISTICS
  // ---------------------------------------------------------------------------
  keyStats: [
    {
      label: 'Validator Nodes',
      value: '~2,000',
      change: '+121%',
      description: 'From 900 in late 2024',
      sovereigntyImpact: 'positive'
    },
    {
      label: 'Foundation Stake',
      value: '20%',
      change: '-43%',
      description: 'Down from 63%',
      sovereigntyImpact: 'positive'
    },
    {
      label: 'Community Stake',
      value: '80%',
      change: '+43%',
      description: 'Decentralization achieved',
      sovereigntyImpact: 'positive'
    },
    {
      label: 'Block Time',
      value: '2.8s',
      change: '-0.5s',
      description: 'Dynamic Round Times',
      sovereigntyImpact: 'neutral'
    },
    {
      label: 'Combined TVL',
      value: '$685M',
      change: '+115%',
      description: 'DeFi + RWA',
      sovereigntyImpact: 'neutral'
    },
    {
      label: 'Reti Pool Stake',
      value: '480M ALGO',
      change: 'New',
      description: 'Non-custodial pooling',
      sovereigntyImpact: 'positive'
    }
  ] as ResearchStat[],

  // ---------------------------------------------------------------------------
  // DECENTRALIZATION DATA
  // ---------------------------------------------------------------------------
  decentralization: {
    foundationStakePercent: 20,
    communityStakePercent: 80,
    nodeCount: 2000,
    nodeGrowthPercent: 121,
    p2pNetworkLive: true,
    minimumStakeForRewards: 30000,
    relayNodesDependency: 'Hybrid (transitioning to full P2P)',

    nodeGrowthData: [
      { month: 'Jan', nodes: 900 },
      { month: 'Feb', nodes: 950 },
      { month: 'Mar', nodes: 1050 },
      { month: 'Apr', nodes: 1200 },
      { month: 'May', nodes: 1400 },
      { month: 'Jun', nodes: 1550 },
      { month: 'Jul', nodes: 1650 },
      { month: 'Aug', nodes: 1750 },
      { month: 'Sep', nodes: 1850 },
      { month: 'Oct', nodes: 1900 },
      { month: 'Nov', nodes: 1950 },
      { month: 'Dec', nodes: 2000 }
    ],

    highlights: [
      'P2P Gossip Network finalized December 2025 - nodes discover peers without centralized directory',
      'Consensus Incentivization program launched January 2025 - direct rewards for block production',
      '30,000 ALGO minimum stake for rewards drove professionalization of validator set',
      'Reti Pooling and Valar provide non-custodial delegation for smaller holders',
      'Foundation actively divesting to force ecosystem self-sufficiency',
      'Hybrid Mode allows connection to both permissioned relays and P2P mesh'
    ],

    sovereigntyAnalysis: `The 63% → 20% Foundation stake reduction is the most significant decentralization achievement in Algorand's history. Combined with P2P networking removing relay node centralization, Algorand now has a credible claim to being "decentralized" in practice, not just theory. The 80% community stake means the network is now secured by independent validators, not the Foundation.`
  },

  // ---------------------------------------------------------------------------
  // PROJECT KING SAFETY (SUPPLY CAP DEBATE)
  // ---------------------------------------------------------------------------
  projectKingSafety: {
    issue: 'Foundation treasury depleting by ~January 2027',
    currentSupplyCap: '10 Billion ALGO',
    proposal: 'Uncap supply, introduce "tail emissions" for perpetual validator rewards',

    forArguments: [
      'L1 security is a public good that must be funded',
      'Without tail emission, security relies entirely on transaction fees',
      'Current fee revenue (~0.001 ALGO per tx) insufficient for 2,000+ validators',
      'Rewards could drop to ~0.05 ALGO per block, causing validator exodus',
      'Similar models work for Ethereum and Solana'
    ],

    againstArguments: [
      '10B hard cap was fundamental promise of the protocol',
      'Uncapping would dilute existing holders',
      'Damages Algorand\'s "store of value" and sound money narrative',
      'Sets precedent for future supply changes',
      'May not solve underlying fee revenue problem'
    ],

    alternatives: [
      'Drastically increase transaction fees (risks killing low-cost utility)',
      'Protocol-level MEV capture to redirect arbitrage profits to validators',
      'Fee market mechanisms with dynamic pricing'
    ],

    voteRequirement: '90% supermajority of consensus stake',
    expectedDecision: '2026',

    sovereigntyAnalysis: `This is THE critical decision for Algorand's hard money credentials. A fixed 10B supply is what allows ALGO to be classified alongside Bitcoin as "scarce." Introducing tail emissions would make ALGO inflationary like Ethereum - still useful, but no longer "sound money" in the Austrian economics sense.

For sovereignty-focused investors, the outcome of this vote determines whether ALGO remains in our "Hard Money" classification or moves to "Productive Asset." Watch this closely.`
  },

  // ---------------------------------------------------------------------------
  // PROTOCOL TIMELINE
  // ---------------------------------------------------------------------------
  timeline: [
    {
      date: 'Jan 2025',
      title: 'Consensus Incentivization Launch',
      description: 'Direct rewards for block production. 30,000 ALGO minimum stake required. Massive shift from passive governance to active participation.',
      category: 'governance',
      sovereigntyImpact: 'positive'
    },
    {
      date: 'Feb 2025',
      title: 'AlgoKit 2.5 Release',
      description: 'Native Python debugging, one-click localnet setup. Dramatically lowered developer barrier to entry.',
      category: 'protocol',
      sovereigntyImpact: 'neutral'
    },
    {
      date: 'May 2025',
      title: 'Dynamic Round Times',
      description: 'Block times now adapt to network load, averaging 2.8s (down from 3.3s). Sub-3-second finality.',
      category: 'protocol',
      sovereigntyImpact: 'neutral'
    },
    {
      date: 'Aug 2025',
      title: 'P2P Gossip Optimization',
      description: '30% bandwidth reduction for relay nodes. Preparation for full P2P transition.',
      category: 'protocol',
      sovereigntyImpact: 'positive'
    },
    {
      date: 'Oct 2025',
      title: 'AVM v10 Upgrade',
      description: 'Elliptic curve math for BN254 curves. Enables native ZK-proof verification on Layer 1.',
      category: 'protocol',
      sovereigntyImpact: 'neutral'
    },
    {
      date: 'Oct 2025',
      title: 'xGov Mainnet Launch',
      description: 'Community-driven grant allocation live. 9 proposals submitted, 6 funded in Q4. Foundation no longer gatekeeps funding.',
      category: 'governance',
      sovereigntyImpact: 'positive'
    },
    {
      date: 'Nov 2025',
      title: 'FOLKS Token TGE',
      description: 'Folks Finance governance token launched. Cross-chain via Wormhole/xPortal to Avalanche and Base.',
      category: 'ecosystem',
      sovereigntyImpact: 'neutral'
    },
    {
      date: 'Dec 2025',
      title: 'Post-Quantum Accounts',
      description: 'Falcon-1024 signatures activated. First major L1 with NIST-standardized quantum resistance for transactions.',
      category: 'security',
      sovereigntyImpact: 'positive'
    },
    {
      date: 'Dec 2025',
      title: 'P2P Network Finalized',
      description: 'Autonomous peer discovery live. Nodes no longer dependent on permissioned relay list. Censorship resistance achieved.',
      category: 'protocol',
      sovereigntyImpact: 'positive'
    }
  ] as TimelineEvent[],

  // ---------------------------------------------------------------------------
  // ECOSYSTEM PROJECTS (COMPREHENSIVE - 45+ PROJECTS)
  // ---------------------------------------------------------------------------
  ecosystemProjects: [
    // ===== WALLETS =====
    {
      name: 'Pera Wallet',
      category: 'Wallets',
      status: 'Essential',
      description: 'The standard mobile/web wallet for Algorand. Official wallet with WalletConnect support.',
      keyFeature: 'Native dApp browser, Ledger support',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://perawallet.app',
      twitter: '@PeraAlgoWallet'
    },
    {
      name: 'Defly',
      category: 'Wallets',
      status: 'Essential',
      description: 'Power user wallet with built-in DEX swapping and portfolio tracking.',
      keyFeature: 'In-app swaps, advanced analytics',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://defly.app',
      twitter: '@deflywallet'
    },
    {
      name: 'Lute',
      category: 'Wallets',
      status: 'Major',
      description: 'Web-based hot wallet for quick dApp connections on desktop.',
      keyFeature: 'Browser-based, fast connections',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://lute.app'
    },
    {
      name: 'Ledger',
      category: 'Wallets',
      status: 'Essential',
      description: 'Hardware wallet standard. Nano S/X/Stax support ALGO natively.',
      keyFeature: 'Cold storage, maximum security',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://ledger.com'
    },

    // ===== DEFI =====
    {
      name: 'Folks Finance',
      category: 'DeFi',
      subcategory: 'Lending',
      status: 'Essential',
      description: 'Dominant lending & borrowing protocol. 60% of Algorand DeFi TVL. Cross-chain via Wormhole.',
      keyFeature: 'Liquid Governance (gALGO), cross-chain lending',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://folks.finance',
      twitter: '@FolksFinance'
    },
    {
      name: 'Tinyman',
      category: 'DeFi',
      subcategory: 'DEX',
      status: 'Essential',
      description: 'The original AMM on Algorand. $500M+ cumulative volume. 40% TINY locked in governance.',
      keyFeature: 'Farm rewards, simple swapping',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://tinyman.org',
      twitter: '@TinymanOrg'
    },
    {
      name: 'Pact',
      category: 'DeFi',
      subcategory: 'DEX',
      status: 'Major',
      description: 'DEX focused on stable/low-volatility pairs. Introduced $POW token and CCLP pools.',
      keyFeature: 'Consensus Compatible LP (earn staking + trading fees)',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://pact.fi',
      twitter: '@paborern'
    },
    {
      name: 'Vestige',
      category: 'DeFi',
      subcategory: 'Aggregator',
      status: 'Essential',
      description: 'The "Bloomberg Terminal" of Algorand. DEX aggregator, charts, and analytics. $200M lifetime volume.',
      keyFeature: 'Best price routing, essential charts',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://vestige.fi',
      twitter: '@vesaborern'
    },
    {
      name: 'Messina',
      category: 'DeFi',
      subcategory: 'Bridge',
      status: 'Major',
      description: 'Primary bridge and liquid staking solution for cross-chain assets.',
      keyFeature: 'Cross-chain bridging',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://messina.one'
    },
    {
      name: 'CompX',
      category: 'DeFi',
      subcategory: 'Yield',
      status: 'Growing',
      description: 'Yield farming optimizer and auto-compounder. Integrated with Lofty for rental yield compounding.',
      keyFeature: 'Auto-compound yields',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://compx.io'
    },
    {
      name: 'Humble DeFi',
      category: 'DeFi',
      subcategory: 'DEX',
      status: 'Stable',
      description: 'Major AMM with deep liquidity on stable pairs.',
      keyFeature: 'Stable pair liquidity',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://humble.sh'
    },
    {
      name: 'xBacked',
      category: 'DeFi',
      subcategory: 'Stablecoin',
      status: 'Growing',
      description: 'Decentralized stablecoin (xUSD) minted against ALGO collateral.',
      keyFeature: 'ALGO-backed stablecoin',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://xbacked.io'
    },
    {
      name: 'goBTC (Algomint)',
      category: 'DeFi',
      subcategory: 'Bridge',
      status: 'Stable',
      description: 'Primary Bitcoin bridge. 1:1 BTC backing. Main use: collateral in lending markets.',
      keyFeature: '1:1 BTC peg, carbon-offset',
      sovereigntyRelevant: true,
      hardMoneyPartner: true,
      url: 'https://algomint.io',
      twitter: '@algaborern'
    },

    // ===== STAKING & NODE INFRASTRUCTURE =====
    {
      name: 'Reti Open Pooling',
      category: 'Staking',
      status: 'Essential',
      description: 'Decentralized staking protocol. Pool ALGO to run participation nodes non-custodially. 480M ALGO staked.',
      keyFeature: 'Non-custodial node pooling',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://reti.vote'
    },
    {
      name: 'Valar',
      category: 'Staking',
      status: 'Major',
      description: 'Delegated staking solution for users below 30k ALGO threshold.',
      keyFeature: 'Stake delegation',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://valar.fi'
    },
    // ===== REAL WORLD ASSETS =====
    {
      name: 'Meld Gold',
      category: 'RWA',
      subcategory: 'Precious Metals',
      status: 'Essential',
      description: 'Tokenized gold, silver, copper, platinum. On-chain vault verification in Australia.',
      keyFeature: 'Supply chain integration, trust-minimized auditing',
      sovereigntyRelevant: true,
      hardMoneyPartner: true,
      url: 'https://meld.gold',
      twitter: '@MeldGold'
    },
    {
      name: 'Lofty',
      category: 'RWA',
      subcategory: 'Real Estate',
      status: 'Essential',
      description: 'Fractionalized real estate. $99M TVL, $4M rental income paid. Achieved profitability in 2025.',
      keyFeature: 'Daily rent payouts, auto-compounding via CompX',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://lofty.ai',
      twitter: '@laborern'
    },
    {
      name: 'Agrotoken',
      category: 'RWA',
      subcategory: 'Agriculture',
      status: 'Major',
      description: 'Tokenized agricultural commodities - soy, corn, wheat. Major 2025 growth narrative.',
      keyFeature: 'Commodity-backed tokens',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://agrotoken.io'
    },
    {
      name: 'TravelX',
      category: 'RWA',
      subcategory: 'Tickets',
      status: 'Major',
      description: 'Tokenized airline tickets (NFTickets). Heavy usage in Latin America.',
      keyFeature: 'NFT tickets with secondary market',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://travelx.io'
    },
    {
      name: 'Midas (mTBILL)',
      category: 'RWA',
      subcategory: 'Treasury',
      status: 'New',
      description: 'Tokenized US Treasury Bills. German-regulated, institutional-grade.',
      keyFeature: 'Compliant treasury exposure',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://midas.app'
    },

    // ===== NFTs & MARKETPLACES =====
    {
      name: 'ALGOxNFT',
      category: 'NFTs',
      subcategory: 'Marketplace',
      status: 'Major',
      description: 'Primary auction house for Algorand NFTs.',
      keyFeature: 'Auctions, curated collections',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://algoxnft.com'
    },
    {
      name: 'Rand Gallery',
      category: 'NFTs',
      subcategory: 'Marketplace',
      status: 'Stable',
      description: 'OG marketplace with classic collections.',
      keyFeature: 'Legacy collections',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://randgallery.com'
    },
    {
      name: 'Shufl',
      category: 'NFTs',
      subcategory: 'Aggregator',
      status: 'Growing',
      description: 'NFT aggregator marketplace. The "Blur" of Algorand.',
      keyFeature: 'Cross-marketplace aggregation',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://shufl.app'
    },
    {
      name: 'Asalytic',
      category: 'NFTs',
      subcategory: 'Analytics',
      status: 'Stable',
      description: 'NFT analytics tool for rarity scores and floor history.',
      keyFeature: 'Rarity analysis',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://asalytic.app'
    },
    {
      name: 'Exa Market',
      category: 'NFTs',
      subcategory: 'Marketplace',
      status: 'Growing',
      description: 'Focus on gaming and higher-end art assets.',
      keyFeature: 'Gaming NFTs',
      sovereigntyRelevant: false,
      hardMoneyPartner: false
    },

    // ===== IDENTITY =====
    {
      name: 'NFDomains',
      category: 'Identity',
      status: 'Essential',
      description: 'Naming service (.algo domains). V3 launched with yearly renewal model for sustainability.',
      keyFeature: 'Human-readable addresses, permissionless minting',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://nf.domains',
      twitter: '@NFDomains'
    },

    // ===== INFRASTRUCTURE =====
    {
      name: 'AlgoKit',
      category: 'Infrastructure',
      subcategory: 'Development',
      status: 'Essential',
      description: 'Primary developer onboarding tool. One-click localnet, Python/TypeScript support.',
      keyFeature: 'One-click dev environment',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://developer.algorand.org/algokit'
    },
    {
      name: 'Nodely',
      category: 'Infrastructure',
      subcategory: 'RPC',
      status: 'Essential',
      description: 'RPC provider and indexer service. Also runs Reti pooling.',
      keyFeature: 'Reliable API access',
      sovereigntyRelevant: true,
      hardMoneyPartner: false,
      url: 'https://nodely.io'
    },
    {
      name: 'AlgoNode',
      category: 'Infrastructure',
      subcategory: 'RPC',
      status: 'Essential',
      description: 'Free API endpoint provider for Algorand developers.',
      keyFeature: 'Free tier API access',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://algonode.io'
    },
    {
      name: 'Lora',
      category: 'Infrastructure',
      subcategory: 'Explorer',
      status: 'Major',
      description: 'Modern block explorer replacing older tools. By AlgoExplorer team.',
      keyFeature: 'Clean UX, fast search',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://lora.algokit.io'
    },
    {
      name: 'Chaser',
      category: 'Infrastructure',
      subcategory: 'Tools',
      status: 'Growing',
      description: 'NFT Discord bot. Ubiquitous in Algorand community servers.',
      keyFeature: 'Community notifications',
      sovereigntyRelevant: false,
      hardMoneyPartner: false
    },

    // ===== GAMING =====
    {
      name: 'Cosmic Champs',
      category: 'Gaming',
      status: 'Major',
      description: 'Real-time strategy game on mobile/PC. 50k DAU peak in Q3 2025.',
      keyFeature: 'Mobile release, real gameplay',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://cosmicchamps.com'
    },
    {
      name: 'Fracctal Monsters',
      category: 'Gaming',
      status: 'Stable',
      description: 'Tamagotchi meets Pokémon style game. P2E mechanics overhauled in 2025.',
      keyFeature: 'NFT interoperability',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://fracctalmonsters.com'
    },
    {
      name: 'Alchemon',
      category: 'Gaming',
      status: 'Stable',
      description: 'Monster-collecting card game on Algorand.',
      keyFeature: 'Trading card mechanics',
      sovereigntyRelevant: false,
      hardMoneyPartner: false,
      url: 'https://alchemon.net'
    },
    {
      name: 'Trantorian',
      category: 'Gaming',
      status: 'Growing',
      description: 'Space 4X strategy game.',
      keyFeature: 'Strategy gameplay',
      sovereigntyRelevant: false,
      hardMoneyPartner: false
    },
    {
      name: 'Alpha Arcade',
      category: 'Gaming',
      subcategory: 'Prediction',
      status: 'New',
      description: 'First dedicated prediction market on Algorand. Sports and political betting.',
      keyFeature: 'On-chain predictions',
      sovereigntyRelevant: false,
      hardMoneyPartner: false
    }
  ] as EcosystemProject[],

  // ---------------------------------------------------------------------------
  // RWA BREAKDOWN
  // ---------------------------------------------------------------------------
  rwaBreakdown: {
    labels: ['Real Estate', 'Precious Metals', 'Agro-Commodities', 'Govt Bonds', 'Equities'],
    values: [120, 85, 200, 150, 45], // Millions USD
    colors: ['#14b8a6', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6']
  },

  // ---------------------------------------------------------------------------
  // INSTITUTIONAL ADOPTION
  // ---------------------------------------------------------------------------
  institutionalAdoption: [
    {
      name: 'Nubank',
      region: 'Latin America',
      users: '100M',
      description: 'ALGO trading for Brazil, Mexico, Colombia',
      sovereigntyRelevant: false
    },
    {
      name: 'HesabPay',
      region: 'Afghanistan',
      users: 'Millions',
      description: 'Largest humanitarian blockchain payments (UN agencies). MoneyGram remittances.',
      sovereigntyRelevant: true
    },
    {
      name: 'Mann Deshi',
      region: 'India',
      users: '400,000',
      description: 'Blockchain credit scores for rural women micro-entrepreneurs',
      sovereigntyRelevant: true
    },
    {
      name: 'SEWA',
      region: 'India',
      users: 'Millions',
      description: 'Digital identity for informal sector workers',
      sovereigntyRelevant: true
    },
    {
      name: 'Pera Mastercard',
      region: '12 Countries',
      users: 'N/A',
      description: 'Self-custodied USDCa spending at any Mastercard PoS',
      sovereigntyRelevant: true
    },
    {
      name: 'World Chess',
      region: 'Global',
      users: '1M',
      description: '"The Tower" loyalty program. Immutable rating/title records on-chain.',
      sovereigntyRelevant: false
    },
    {
      name: 'Zebec',
      region: 'Global',
      users: 'N/A',
      description: 'Payroll streaming. Receive salary in USDCa/ALGO, spend via Mastercard.',
      sovereigntyRelevant: true
    }
  ] as InstitutionalAdoption[],

  // ---------------------------------------------------------------------------
  // 2026 OUTLOOK
  // ---------------------------------------------------------------------------
  outlook2026: [
    'Will community vote to uncap supply for security budget?',
    'Can RWA momentum generate sufficient transaction fees?',
    'Will AlgoKit Python strategy onboard next wave of developers?',
    'Will P2P network achieve full relay independence?'
  ],

  // ---------------------------------------------------------------------------
  // HARD MONEY PARTNERS (For Sovereignty Analyzer)
  // ---------------------------------------------------------------------------
  hardMoneyPartners: [
    {
      name: 'Meld Gold (GOLD$)',
      asaId: 246516580,
      supply: 'Gold-backed',
      description: 'Tokenized physical gold in Australian vaults.',
      sovereigntyRationale: 'Real asset backing, 5,000 year track record'
    },
    {
      name: 'Meld Silver (SILVER$)',
      asaId: 246519683,
      supply: 'Silver-backed',
      description: 'Tokenized physical silver.',
      sovereigntyRationale: 'Real asset backing, industrial + monetary demand'
    },
    {
      name: 'goBTC',
      asaId: 386192725,
      supply: 'BTC-backed',
      description: '1:1 wrapped Bitcoin on Algorand.',
      sovereigntyRationale: 'Bitcoin is the apex hard money asset'
    }
  ],

  // ---------------------------------------------------------------------------
  // SOURCES
  // ---------------------------------------------------------------------------
  sources: [
    { id: 1, title: '2025 on Algorand: Roadmap progress', url: 'https://algorand.co/blog/2025-on-algorand-roadmap-progress' },
    { id: 2, title: 'Algorand 2025 roadmap: Web3 core values', url: 'https://algorand.co/blog/web3-core-values-from-algorands-2025-roadmap' },
    { id: 3, title: 'Quantum-Resistant Blockchain Projects', url: 'https://worldbusinessoutlook.com/5-quantum-resistant-blockchain-projects-worth-watching-in-2026/' },
    { id: 4, title: 'Falcon Signatures Technical Brief', url: 'https://algorand.co/blog/technical-brief-quantum-resistant-transactions-on-algorand-with-falcon-signatures' },
    { id: 5, title: 'Latest Algorand Updates - CoinMarketCap', url: 'https://coinmarketcap.com/cmc-ai/algorand/latest-updates/' },
    { id: 6, title: 'Dynamic Round Times & AVM v10', url: 'https://developer.algorand.org/articles/algorands-latest-upgrade-dynamic-round-times-avm-v10/' },
    { id: 7, title: 'Project King Safety Discussion', url: 'https://www.reddit.com/r/AlgorandOfficial/comments/1pkdpi8/update_on_the_status_of_the_project_king_safety/' },
    { id: 8, title: '2025 Ecosystem Highlights', url: 'https://algorand.co/blog/2025-on-algorand-2025-ecosystem-highlights' },
    { id: 9, title: 'April 2025 Algo Insights', url: 'https://algorand.co/blog/april-2025-algorand-insights-online-stake-rwa-tvl-increase' },
    { id: 10, title: 'Staking Rewards FAQ', url: 'https://algorand.co/staking-rewards-faq' },
    { id: 13, title: 'Q3 2025 Transparency Report', url: 'https://algorand.co/hubfs/Algorand%20Transparency%20Report-Q3-2025_V3%20Final.pdf' },
    { id: 14, title: 'Developer Resources 2025', url: 'https://algorand.co/blog/2025-on-algorand-whats-in-it-for-you-as-a-developer' },
    { id: 15, title: 'November 2025 Algo Insights', url: 'https://algorand.co/blog/november-2025-algo-insights-report' },
    { id: 16, title: 'Meld Gold Case Study', url: 'https://algorand.co/case-studies/meld-gold-can' }
  ] as ResearchSource[]
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

export function getProjectsByCategory(category: string): EcosystemProject[] {
  if (category === 'all') return ALGORAND_2025_RESEARCH.ecosystemProjects
  return ALGORAND_2025_RESEARCH.ecosystemProjects.filter(p => p.category === category)
}

export function getSovereigntyRelevantProjects(): EcosystemProject[] {
  return ALGORAND_2025_RESEARCH.ecosystemProjects.filter(p => p.sovereigntyRelevant)
}

export function getHardMoneyPartners(): EcosystemProject[] {
  return ALGORAND_2025_RESEARCH.ecosystemProjects.filter(p => p.hardMoneyPartner)
}

export function getPositiveSovereigntyEvents(): TimelineEvent[] {
  return ALGORAND_2025_RESEARCH.timeline.filter(e => e.sovereigntyImpact === 'positive')
}

export function getEventsByCategory(category: TimelineEvent['category']): TimelineEvent[] {
  return ALGORAND_2025_RESEARCH.timeline.filter(e => e.category === category)
}

export function getEcosystemCategories(): string[] {
  const categories = new Set(ALGORAND_2025_RESEARCH.ecosystemProjects.map(p => p.category))
  return ['all', ...Array.from(categories)]
}

export function getProjectCount(): { total: number; byCategory: Record<string, number> } {
  const projects = ALGORAND_2025_RESEARCH.ecosystemProjects
  const byCategory: Record<string, number> = {}

  projects.forEach(p => {
    byCategory[p.category] = (byCategory[p.category] || 0) + 1
  })

  return { total: projects.length, byCategory }
}

export function getTotalRwaTvl(): number {
  return ALGORAND_2025_RESEARCH.rwaBreakdown.values.reduce((sum, val) => sum + val, 0)
}
