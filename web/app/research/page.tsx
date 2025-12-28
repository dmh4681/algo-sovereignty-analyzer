'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, ExternalLink, TrendingUp, TrendingDown, Shield, AlertTriangle, CheckCircle2, Clock, Users, Coins, Server, Zap, Building2, Lock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  ALGORAND_2025_RESEARCH,
  getSovereigntyRelevantProjects,
  getPositiveSovereigntyEvents,
  getProjectsByCategory,
  getTotalRwaTvl,
  type TimelineEvent,
  type EcosystemProject
} from '@/lib/algorand-2025-research'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'

// =============================================================================
// Types
// =============================================================================

type TabId = 'summary' | 'decentralization' | 'king-safety' | 'timeline' | 'ecosystem' | 'rwa' | 'outlook'

interface Tab {
  id: TabId
  label: string
  icon: React.ReactNode
}

// =============================================================================
// Constants
// =============================================================================

const TABS: Tab[] = [
  { id: 'summary', label: 'Summary', icon: <Zap className="h-4 w-4" /> },
  { id: 'decentralization', label: 'Decentralization', icon: <Users className="h-4 w-4" /> },
  { id: 'king-safety', label: 'King Safety', icon: <AlertTriangle className="h-4 w-4" /> },
  { id: 'timeline', label: 'Timeline', icon: <Clock className="h-4 w-4" /> },
  { id: 'ecosystem', label: 'Ecosystem', icon: <Building2 className="h-4 w-4" /> },
  { id: 'rwa', label: 'RWA', icon: <Coins className="h-4 w-4" /> },
  { id: 'outlook', label: '2026', icon: <TrendingUp className="h-4 w-4" /> },
]

const CHART_COLORS = {
  orange: '#f97316',
  teal: '#14b8a6',
  slate: '#64748b',
  green: '#22c55e',
  red: '#ef4444',
  purple: '#a855f7',
  blue: '#3b82f6',
  yellow: '#eab308'
}

// =============================================================================
// Helper Components
// =============================================================================

function SovereigntyCallout({
  type,
  title,
  children
}: {
  type: 'positive' | 'negative' | 'critical'
  title: string
  children: React.ReactNode
}) {
  const styles = {
    positive: 'border-green-500/30 bg-green-500/5',
    negative: 'border-red-500/30 bg-red-500/5',
    critical: 'border-orange-500/30 bg-orange-500/5'
  }

  const icons = {
    positive: <CheckCircle2 className="h-5 w-5 text-green-500" />,
    negative: <TrendingDown className="h-5 w-5 text-red-500" />,
    critical: <AlertTriangle className="h-5 w-5 text-orange-500" />
  }

  const labels = {
    positive: 'POSITIVE FOR SOVEREIGNTY',
    negative: 'NEGATIVE FOR SOVEREIGNTY',
    critical: 'CRITICAL DECISION POINT'
  }

  return (
    <Card className={`${styles[type]} my-4`}>
      <CardContent className="py-4">
        <div className="flex gap-3">
          {icons[type]}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-xs font-bold uppercase tracking-wide ${
                type === 'positive' ? 'text-green-400' :
                type === 'negative' ? 'text-red-400' : 'text-orange-400'
              }`}>
                {labels[type]}
              </span>
            </div>
            <h4 className="font-semibold text-slate-200 mb-1">{title}</h4>
            <div className="text-sm text-slate-400">{children}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function StatCard({
  label,
  value,
  change,
  description,
  impact
}: {
  label: string
  value: string
  change: string
  description: string
  impact?: 'positive' | 'negative' | 'neutral'
}) {
  const impactColor = impact === 'positive' ? 'text-green-400' :
                      impact === 'negative' ? 'text-red-400' : 'text-slate-400'

  return (
    <Card className="border-slate-700">
      <CardContent className="pt-4">
        <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">{label}</div>
        <div className="text-2xl font-bold text-slate-100">{value}</div>
        <div className={`text-sm font-medium ${impactColor}`}>{change}</div>
        <div className="text-xs text-slate-500 mt-1">{description}</div>
      </CardContent>
    </Card>
  )
}

function TimelineItem({ event }: { event: TimelineEvent }) {
  const categoryColors = {
    protocol: 'bg-blue-500',
    governance: 'bg-purple-500',
    ecosystem: 'bg-teal-500',
    security: 'bg-green-500'
  }

  const impactBadge = {
    positive: <Badge className="bg-green-500/20 text-green-400 text-xs">+Sovereignty</Badge>,
    negative: <Badge className="bg-red-500/20 text-red-400 text-xs">-Sovereignty</Badge>,
    neutral: null
  }

  return (
    <div className="flex gap-4 pb-6 relative">
      <div className="flex flex-col items-center">
        <div className={`w-3 h-3 rounded-full ${categoryColors[event.category]}`} />
        <div className="w-0.5 h-full bg-slate-700 absolute top-3" />
      </div>
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs text-slate-500 font-mono">{event.date}</span>
          <Badge variant="outline" className="text-xs border-slate-600">
            {event.category}
          </Badge>
          {event.sovereigntyImpact && impactBadge[event.sovereigntyImpact]}
        </div>
        <h4 className="font-semibold text-slate-200">{event.title}</h4>
        <p className="text-sm text-slate-400">{event.description}</p>
      </div>
    </div>
  )
}

function ProjectCard({ project }: { project: EcosystemProject }) {
  const categoryColors: Record<EcosystemProject['category'], string> = {
    Wallets: 'border-blue-500/30',
    DeFi: 'border-cyan-500/30',
    Staking: 'border-green-500/30',
    RWA: 'border-amber-500/30',
    NFTs: 'border-rose-500/30',
    Gaming: 'border-purple-500/30',
    Identity: 'border-pink-500/30',
    Infrastructure: 'border-slate-500/30'
  }

  return (
    <Card className={`border-slate-700 ${categoryColors[project.category]} hover:bg-slate-800/50 transition-colors`}>
      <CardContent className="pt-4">
        <div className="flex items-start justify-between mb-2">
          <h4 className="font-semibold text-slate-200">{project.name}</h4>
          {project.sovereigntyRelevant && (
            <Shield className="h-4 w-4 text-orange-500" />
          )}
        </div>
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="outline" className="text-xs border-slate-600">{project.category}</Badge>
          <span className="text-xs text-slate-500">{project.status}</span>
        </div>
        <p className="text-sm text-slate-400 mb-3">{project.description}</p>
        {project.url && (
          <a
            href={project.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-orange-500 hover:text-orange-400 flex items-center gap-1"
          >
            Visit <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </CardContent>
    </Card>
  )
}

// =============================================================================
// Section Components
// =============================================================================

function SummarySection() {
  return (
    <div className="space-y-6">
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
          <CardDescription>Key findings from Algorand's 2025 development</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-slate-300 leading-relaxed">
            {ALGORAND_2025_RESEARCH.executiveSummary}
          </p>
        </CardContent>
      </Card>

      <SovereigntyCallout type="positive" title="Foundation Stake Reduction">
        The Algorand Foundation reduced its stake from 63% to 20% of online consensus.
        This is the most significant decentralization milestone in Algorand's history,
        giving the community 80% control over block production.
      </SovereigntyCallout>

      <SovereigntyCallout type="positive" title="P2P Network Finalized">
        Nodes can now discover peers autonomously without relying on Foundation-run relay nodes.
        This removes a critical centralization vector and makes the network truly permissionless.
      </SovereigntyCallout>

      <SovereigntyCallout type="critical" title="Project King Safety">
        The debate over uncapping the 10 billion ALGO supply to fund long-term validator
        rewards is the defining tension between sound money principles and network sustainability.
        A 90% supermajority vote is required - this decision will determine if ALGO can claim hard money status.
      </SovereigntyCallout>

      <SovereigntyCallout type="positive" title="Post-Quantum Security">
        Algorand became the first major L1 to implement NIST-approved post-quantum cryptography
        (Falcon-1024 signatures). This provides long-term security against quantum computing threats.
      </SovereigntyCallout>
    </div>
  )
}

function DecentralizationSection() {
  const { decentralization } = ALGORAND_2025_RESEARCH

  const stakeData = [
    { name: 'Community', value: decentralization.communityStakePercent, color: CHART_COLORS.orange },
    { name: 'Foundation', value: decentralization.foundationStakePercent, color: CHART_COLORS.slate }
  ]

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-2 gap-6">
        {/* Stake Distribution Chart */}
        <Card className="border-slate-700">
          <CardHeader>
            <CardTitle>Stake Distribution</CardTitle>
            <CardDescription>Foundation vs Community consensus stake</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stakeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}%`}
                    labelLine={false}
                  >
                    {stakeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                    itemStyle={{ color: '#f1f5f9' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-6 mt-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-orange-500" />
                <span className="text-sm text-slate-400">Community (80%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-slate-500" />
                <span className="text-sm text-slate-400">Foundation (20%)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Node Growth */}
        <Card className="border-slate-700">
          <CardHeader>
            <CardTitle>Node Growth</CardTitle>
            <CardDescription>Validator node count over 2025</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                <div>
                  <div className="text-3xl font-bold text-orange-500">~{decentralization.nodeCount.toLocaleString()}</div>
                  <div className="text-sm text-slate-400">Active Validators</div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold text-green-400">+{decentralization.nodeGrowthPercent}%</div>
                  <div className="text-sm text-slate-400">YoY Growth</div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Late 2024</span>
                  <span className="text-slate-300">~900 nodes</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-slate-500 h-2 rounded-full" style={{ width: '45%' }} />
                </div>

                <div className="flex items-center justify-between text-sm mt-4">
                  <span className="text-slate-400">December 2025</span>
                  <span className="text-orange-400 font-semibold">~2,000 nodes</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-orange-500 h-2 rounded-full" style={{ width: '100%' }} />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Decentralization Highlights */}
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle>2025 Decentralization Milestones</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {decentralization.highlights.map((highlight, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-slate-300">{highlight}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <SovereigntyCallout type="positive" title="P2P Network Status">
        {decentralization.p2pNetworkLive ? (
          <>P2P gossip network is <strong className="text-green-400">LIVE</strong>.
          Current relay dependency: {decentralization.relayNodesDependency}</>
        ) : (
          <>P2P network still in development. Relay dependency: {decentralization.relayNodesDependency}</>
        )}
      </SovereigntyCallout>
    </div>
  )
}

function KingSafetySection() {
  const { projectKingSafety } = ALGORAND_2025_RESEARCH

  return (
    <div className="space-y-6">
      <Card className="border-orange-500/30 bg-orange-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-orange-400">
            <AlertTriangle className="h-5 w-5" />
            Project King Safety: The 10B Supply Cap Debate
          </CardTitle>
          <CardDescription>
            The most consequential governance decision in Algorand's history
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="p-4 bg-slate-800/50 rounded-lg">
            <div className="text-sm text-slate-400 uppercase tracking-wide mb-1">The Issue</div>
            <p className="text-slate-200">{projectKingSafety.issue}</p>
          </div>

          <div className="p-4 bg-slate-800/50 rounded-lg">
            <div className="text-sm text-slate-400 uppercase tracking-wide mb-1">The Proposal</div>
            <p className="text-slate-200">{projectKingSafety.proposal}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {/* For Arguments */}
            <div className="p-4 bg-green-500/5 border border-green-500/20 rounded-lg">
              <h4 className="font-semibold text-green-400 mb-3 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Arguments For
              </h4>
              <ul className="space-y-2">
                {projectKingSafety.forArguments.map((arg, i) => (
                  <li key={i} className="text-sm text-slate-300 flex gap-2">
                    <span className="text-green-500">+</span>
                    {arg}
                  </li>
                ))}
              </ul>
            </div>

            {/* Against Arguments */}
            <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg">
              <h4 className="font-semibold text-red-400 mb-3 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Arguments Against
              </h4>
              <ul className="space-y-2">
                {projectKingSafety.againstArguments.map((arg, i) => (
                  <li key={i} className="text-sm text-slate-300 flex gap-2">
                    <span className="text-red-500">-</span>
                    {arg}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="p-4 bg-slate-800/50 rounded-lg">
            <div className="text-sm text-slate-400 uppercase tracking-wide mb-1">Vote Requirement</div>
            <p className="text-xl font-bold text-orange-400">{projectKingSafety.voteRequirement}</p>
          </div>

          <div className="p-4 bg-slate-800/50 rounded-lg">
            <div className="text-sm text-slate-400 uppercase tracking-wide mb-1">Alternative Proposals</div>
            <div className="flex flex-wrap gap-2 mt-2">
              {projectKingSafety.alternatives.map((alt, i) => (
                <Badge key={i} variant="outline" className="border-slate-600">{alt}</Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <SovereigntyCallout type="critical" title="Hard Money Analysis">
        {projectKingSafety.sovereigntyAnalysis}
      </SovereigntyCallout>
    </div>
  )
}

function TimelineSection() {
  const { timeline } = ALGORAND_2025_RESEARCH
  const positiveEvents = getPositiveSovereigntyEvents()

  return (
    <div className="space-y-6">
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle>2025 Protocol Timeline</CardTitle>
          <CardDescription>
            Major upgrades and milestones
            <span className="ml-2 text-green-400">
              ({positiveEvents.length} positive for sovereignty)
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mt-4">
            {timeline.map((event, i) => (
              <TimelineItem key={i} event={event} />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Category Legend */}
      <div className="flex flex-wrap gap-4 justify-center">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-sm text-slate-400">Protocol</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-purple-500" />
          <span className="text-slate-400 text-sm">Governance</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-teal-500" />
          <span className="text-sm text-slate-400">Ecosystem</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-sm text-slate-400">Security</span>
        </div>
      </div>
    </div>
  )
}

function EcosystemSection() {
  const [filter, setFilter] = useState<EcosystemProject['category'] | 'all' | 'sovereignty'>('all')
  const { ecosystemProjects } = ALGORAND_2025_RESEARCH
  const sovereigntyProjects = getSovereigntyRelevantProjects()

  const filteredProjects = filter === 'all'
    ? ecosystemProjects
    : filter === 'sovereignty'
    ? sovereigntyProjects
    : getProjectsByCategory(filter)

  const categories: (EcosystemProject['category'] | 'all' | 'sovereignty')[] = [
    'all', 'sovereignty', 'Wallets', 'DeFi', 'Staking', 'RWA', 'NFTs', 'Gaming', 'Identity', 'Infrastructure'
  ]

  return (
    <div className="space-y-6">
      {/* Filter Buttons */}
      <div className="flex flex-wrap gap-2">
        {categories.map(cat => (
          <Button
            key={cat}
            variant={filter === cat ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(cat)}
            className={filter === cat ? 'bg-orange-500 hover:bg-orange-600' : 'border-slate-600'}
          >
            {cat === 'sovereignty' && <Shield className="h-3 w-3 mr-1" />}
            {cat === 'all' ? 'All Projects' : cat === 'sovereignty' ? 'Sovereignty' : cat}
          </Button>
        ))}
      </div>

      {/* Projects Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredProjects.map((project, i) => (
          <ProjectCard key={i} project={project} />
        ))}
      </div>

      {filter === 'sovereignty' && (
        <SovereigntyCallout type="positive" title="Sovereignty-Relevant Projects">
          These projects directly support financial sovereignty: real-world assets (RWA),
          non-custodial staking, and decentralized finance with hard money principles.
        </SovereigntyCallout>
      )}
    </div>
  )
}

function RwaSection() {
  const { rwaBreakdown, institutionalAdoption } = ALGORAND_2025_RESEARCH
  const totalTvl = getTotalRwaTvl()

  const chartData = rwaBreakdown.labels.map((label, i) => ({
    name: label,
    value: rwaBreakdown.values[i]
  }))

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-2 gap-6">
        {/* RWA TVL Chart */}
        <Card className="border-slate-700">
          <CardHeader>
            <CardTitle>RWA Total Value Locked</CardTitle>
            <CardDescription>
              ${totalTvl}M across tokenized real-world assets
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" stroke="#64748b" tickFormatter={(v) => `$${v}M`} />
                  <YAxis type="category" dataKey="name" stroke="#64748b" width={100} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                    itemStyle={{ color: '#f1f5f9' }}
                    formatter={(value: number) => [`$${value}M`, 'TVL']}
                  />
                  <Bar dataKey="value" fill={CHART_COLORS.orange} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Institutional Adoption */}
        <Card className="border-slate-700">
          <CardHeader>
            <CardTitle>Institutional Adoption</CardTitle>
            <CardDescription>Major partnerships and integrations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {institutionalAdoption.map((inst, i) => (
                <div key={i} className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-200">{inst.name}</span>
                    <Badge variant="outline" className="text-xs border-slate-600">{inst.region}</Badge>
                  </div>
                  <div className="text-sm text-slate-400">{inst.description}</div>
                  {inst.users !== 'N/A' && (
                    <div className="text-xs text-orange-400 mt-1">{inst.users} users</div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <SovereigntyCallout type="positive" title="RWA for Sovereignty">
        Tokenized real-world assets (real estate, precious metals, commodities) provide
        alternatives to fiat exposure. Algorand's RWA ecosystem enables sovereign individuals
        to hold productive, tangible assets on-chain.
      </SovereigntyCallout>
    </div>
  )
}

function OutlookSection() {
  const { outlook2026 } = ALGORAND_2025_RESEARCH

  return (
    <div className="space-y-6">
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle>2026 Key Questions</CardTitle>
          <CardDescription>Critical decisions and trends to watch</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-4">
            {outlook2026.map((question, i) => (
              <li key={i} className="flex gap-3 p-4 bg-slate-800/50 rounded-lg">
                <span className="text-2xl font-bold text-orange-500">{i + 1}</span>
                <span className="text-slate-300">{question}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <SovereigntyCallout type="critical" title="The Path Forward">
        Algorand's 2025 developments have dramatically improved decentralization, but
        the supply cap debate will define its hard money narrative. The community's
        decision will determine whether ALGO positions itself as sound money or
        prioritizes network security through inflation.
      </SovereigntyCallout>
    </div>
  )
}

// =============================================================================
// Main Component
// =============================================================================

export default function ResearchPage() {
  const [activeTab, setActiveTab] = useState<TabId>('summary')
  const { keyStats, sources, lastUpdated, source } = ALGORAND_2025_RESEARCH

  // Map stats to impact
  const statImpacts: Record<string, 'positive' | 'negative' | 'neutral'> = {
    'Validator Nodes': 'positive',
    'Foundation Stake': 'positive',
    'Community Stake': 'positive',
    'Block Time': 'neutral',
    'Combined TVL': 'positive',
    'Reti Pool Stake': 'positive'
  }

  const renderSection = () => {
    switch (activeTab) {
      case 'summary': return <SummarySection />
      case 'decentralization': return <DecentralizationSection />
      case 'king-safety': return <KingSafetySection />
      case 'timeline': return <TimelineSection />
      case 'ecosystem': return <EcosystemSection />
      case 'rwa': return <RwaSection />
      case 'outlook': return <OutlookSection />
      default: return <SummarySection />
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
        </Button>
      </div>

      {/* Hero Section */}
      <div className="text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold">
          Algorand 2025: State of the Chain
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto">
          Comprehensive research on decentralization, technology, and ecosystem development
        </p>
        <div className="flex items-center justify-center gap-4 text-sm text-slate-500">
          <span>Last updated: {lastUpdated}</span>
          <span>|</span>
          <span>Source: {source}</span>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Key Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {keyStats.map((stat, i) => (
            <StatCard
              key={i}
              label={stat.label}
              value={stat.value}
              change={stat.change}
              description={stat.description}
              impact={statImpacts[stat.label]}
            />
          ))}
        </div>
      </section>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 border-b border-slate-700 pb-4">
        {TABS.map(tab => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? 'bg-orange-500 hover:bg-orange-600' : ''}
          >
            {tab.icon}
            <span className="ml-2">{tab.label}</span>
          </Button>
        ))}
      </div>

      {/* Active Section Content */}
      <section>
        {renderSection()}
      </section>

      {/* Sources */}
      <Card className="border-slate-700">
        <CardHeader>
          <CardTitle className="text-lg">Sources</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-2">
            {sources.map(src => (
              <a
                key={src.id}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-slate-400 hover:text-orange-400 flex items-center gap-1"
              >
                [{src.id}] {src.title} <ExternalLink className="h-3 w-3" />
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="py-4">
          <div className="flex gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-slate-400">
              <strong className="text-amber-400">Disclaimer:</strong> This research is provided
              for educational purposes only and does not constitute financial advice.
              The sovereignty analysis reflects the author's interpretation of how network
              changes affect decentralization and hard money properties. Always conduct your
              own research before making investment decisions.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Footer CTA */}
      <div className="text-center py-8">
        <p className="text-slate-400 mb-4">
          Ready to analyze your own Algorand wallet for sovereignty?
        </p>
        <Button asChild className="bg-orange-500 hover:bg-orange-600">
          <Link href="/analyze">
            Analyze Your Wallet
          </Link>
        </Button>
      </div>
    </div>
  )
}
