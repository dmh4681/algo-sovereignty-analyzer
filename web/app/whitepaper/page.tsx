'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowUp, ArrowLeft, FileDown, List } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface TOCItem {
    id: string
    title: string
    level: number
}

const tocItems: TOCItem[] = [
    { id: 'abstract', title: 'Abstract', level: 1 },
    { id: 'introduction', title: '1. Introduction', level: 1 },
    { id: 'sovereignty-problem', title: '1.1 The Sovereignty Problem', level: 2 },
    { id: 'thesis', title: '1.2 Our Thesis', level: 2 },
    { id: 'hard-money', title: '2. Hard Money: Definition and Criteria', level: 1 },
    { id: 'what-makes-money-hard', title: '2.1 What Makes Money "Hard"?', level: 2 },
    { id: 'hard-money-algorand', title: '2.2 Hard Money on Algorand', level: 2 },
    { id: 'exclusion-criteria', title: '2.3 Exclusion Criteria', level: 2 },
    { id: 'iga-exception', title: '2.4 The iGetAlgo Exception', level: 2 },
    { id: 'sovereignty-ratio', title: '3. The Sovereignty Ratio', level: 1 },
    { id: 'ratio-definition', title: '3.1 Definition', level: 2 },
    { id: 'ratio-interpretation', title: '3.2 Interpretation', level: 2 },
    { id: 'why-fixed-expenses', title: '3.3 Why Fixed Expenses?', level: 2 },
    { id: 'ratio-limitations', title: '3.4 Limitations', level: 2 },
    { id: 'asset-classification', title: '4. Asset Classification Framework', level: 1 },
    { id: 'four-tier-system', title: '4.1 Four-Tier System', level: 2 },
    { id: 'classification-logic', title: '4.2 Classification Logic', level: 2 },
    { id: 'algo-classification', title: '4.3 ALGO\'s Conditional Classification', level: 2 },
    { id: 'decentralization-imperative', title: '5. Algorand\'s Decentralization Imperative', level: 1 },
    { id: 'current-state', title: '5.1 Current State', level: 2 },
    { id: 'path-to-decentralization', title: '5.2 The Path to Decentralization', level: 2 },
    { id: 'how-we-contribute', title: '5.3 How We Contribute', level: 2 },
    { id: 'roadmap', title: '6. Roadmap', level: 1 },
    { id: 'conclusion', title: '7. Conclusion', level: 1 },
    { id: 'appendix-a', title: 'Appendix A: Asset Classification Table', level: 1 },
    { id: 'appendix-b', title: 'Appendix B: Sovereignty Ratio Examples', level: 1 },
]

function TableOfContents({ activeSection }: { activeSection: string }) {
    return (
        <nav className="space-y-1">
            {tocItems.map((item) => (
                <a
                    key={item.id}
                    href={`#${item.id}`}
                    className={`block py-1.5 text-sm transition-colors ${item.level === 2 ? 'pl-4' : ''
                        } ${activeSection === item.id
                            ? 'text-orange-400 font-medium'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                >
                    {item.title}
                </a>
            ))}
        </nav>
    )
}

function MobileTableOfContents({ activeSection }: { activeSection: string }) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className="lg:hidden fixed bottom-4 right-4 z-40">
            <Button
                onClick={() => setIsOpen(!isOpen)}
                className="rounded-full w-12 h-12 shadow-lg"
            >
                <List className="w-5 h-5" />
            </Button>
            {isOpen && (
                <div className="absolute bottom-16 right-0 w-72 max-h-96 overflow-y-auto bg-slate-900 border border-slate-700 rounded-xl shadow-xl p-4">
                    <h3 className="font-semibold text-white mb-3">Contents</h3>
                    <TableOfContents activeSection={activeSection} />
                </div>
            )}
        </div>
    )
}

export default function WhitepaperPage() {
    const [activeSection, setActiveSection] = useState('abstract')
    const [showBackToTop, setShowBackToTop] = useState(false)

    useEffect(() => {
        const handleScroll = () => {
            setShowBackToTop(window.scrollY > 400)

            // Find which section is currently in view
            const sections = tocItems.map(item => document.getElementById(item.id))
            const scrollPosition = window.scrollY + 100

            for (let i = sections.length - 1; i >= 0; i--) {
                const section = sections[i]
                if (section && section.offsetTop <= scrollPosition) {
                    setActiveSection(tocItems[i].id)
                    break
                }
            }
        }

        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    const scrollToTop = () => {
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    return (
        <div className="max-w-7xl mx-auto px-4 py-8">
            {/* Back link and title */}
            <div className="mb-8">
                <Link href="/about" className="inline-flex items-center gap-2 text-slate-400 hover:text-orange-400 transition-colors mb-4">
                    <ArrowLeft className="w-4 h-4" />
                    Back to About
                </Link>
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">
                    Algorand Sovereignty Analyzer
                </h1>
                <p className="text-xl text-slate-400">Whitepaper v1.0 - December 2024</p>
            </div>

            <div className="flex gap-8">
                {/* Sidebar TOC - Desktop */}
                <aside className="hidden lg:block w-64 flex-shrink-0">
                    <div className="sticky top-24 bg-slate-900/50 border border-slate-800 rounded-xl p-4 max-h-[calc(100vh-8rem)] overflow-y-auto">
                        <h3 className="font-semibold text-white mb-4">Contents</h3>
                        <TableOfContents activeSection={activeSection} />
                        <div className="mt-6 pt-4 border-t border-slate-800">
                            <Button variant="outline" size="sm" className="w-full gap-2" disabled>
                                <FileDown className="w-4 h-4" />
                                Download PDF
                            </Button>
                            <p className="text-xs text-slate-500 mt-2 text-center">Coming soon</p>
                        </div>
                    </div>
                </aside>

                {/* Main content */}
                <article className="flex-1 min-w-0 prose prose-invert prose-slate max-w-none">
                    {/* Abstract */}
                    <section id="abstract" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">Abstract</h2>
                        <p className="text-slate-300 text-lg leading-relaxed">
                            The Algorand Sovereignty Analyzer is a suite of tools designed to measure, track, and incentivize
                            financial sovereignty on the Algorand blockchain. We define sovereignty not as wealth accumulation,
                            but as the capacity to sustain oneself independent of centralized systems. This paper outlines our
                            methodology for classifying on-chain assets, calculating sovereignty metrics, and our thesis on why
                            Algorand's decentralization is both critically important and currently insufficient.
                        </p>
                        <p className="text-slate-300 text-lg leading-relaxed mt-4">
                            Our core contribution is the <strong className="text-orange-400">Sovereignty Ratio</strong>—a metric
                            that relates hard money holdings to fixed annual expenses, providing users with a concrete measurement
                            of their financial independence runway.
                        </p>
                    </section>

                    {/* 1. Introduction */}
                    <section id="introduction" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">1. Introduction</h2>

                        <div id="sovereignty-problem" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">1.1 The Sovereignty Problem</h3>
                            <p className="text-slate-300 mb-4">Modern financial systems are characterized by:</p>
                            <ul className="text-slate-300 space-y-2 list-disc list-inside mb-4">
                                <li>Inflationary monetary policy that erodes purchasing power</li>
                                <li>Centralized control points vulnerable to political pressure</li>
                                <li>Surveillance infrastructure that eliminates financial privacy</li>
                                <li>Counterparty risk embedded in most "assets"</li>
                            </ul>
                            <p className="text-slate-300">
                                Cryptocurrency emerged as a potential solution to these problems. Bitcoin demonstrated that sound
                                money could exist without central banks. Smart contract platforms like Algorand extended this to
                                programmable finance.
                            </p>
                            <p className="text-slate-300 mt-4">
                                However, many cryptocurrency ecosystems have replicated the centralization problems they were
                                designed to solve. Algorand, despite its technical excellence, suffers from significant stake
                                concentration in the Algorand Foundation.
                            </p>
                        </div>

                        <div id="thesis" className="scroll-mt-24">
                            <h3 className="text-2xl font-semibold text-white mb-4">1.2 Our Thesis</h3>
                            <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-6 mb-4">
                                <p className="text-xl font-bold text-orange-400 text-center">
                                    Algorand's survival depends on decentralization from the Foundation.
                                </p>
                            </div>
                            <p className="text-slate-300 mb-4">This is not a criticism of the Foundation's intentions. It's a recognition that:</p>
                            <ol className="text-slate-300 space-y-2 list-decimal list-inside mb-4">
                                <li>Single points of failure create systemic risk</li>
                                <li>Regulatory pressure can compromise any centralized entity</li>
                                <li>True sovereignty requires distributed control</li>
                                <li>The community must build alternatives, not wait for permission</li>
                            </ol>
                            <p className="text-slate-300 mb-4">The Algorand Sovereignty Analyzer exists to accelerate this decentralization by:</p>
                            <ul className="text-slate-300 space-y-2 list-disc list-inside">
                                <li>Making sovereignty measurable</li>
                                <li>Classifying assets by sovereignty characteristics</li>
                                <li>Educating users on participation node operation</li>
                                <li>Creating incentive alignment for decentralization</li>
                            </ul>
                        </div>
                    </section>

                    {/* 2. Hard Money */}
                    <section id="hard-money" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">2. Hard Money: Definition and Criteria</h2>

                        <div id="what-makes-money-hard" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">2.1 What Makes Money "Hard"?</h3>
                            <p className="text-slate-300 mb-4">Hard money is characterized by:</p>
                            <ol className="text-slate-300 space-y-2 list-decimal list-inside mb-4">
                                <li><strong className="text-white">Scarcity</strong> - Fixed or predictably limited supply</li>
                                <li><strong className="text-white">Durability</strong> - Cannot be easily destroyed or degraded</li>
                                <li><strong className="text-white">Portability</strong> - Can be moved and stored efficiently</li>
                                <li><strong className="text-white">Divisibility</strong> - Can be divided into smaller units</li>
                                <li><strong className="text-white">Fungibility</strong> - Units are interchangeable</li>
                                <li><strong className="text-white">Censorship Resistance</strong> - Cannot be easily seized or frozen</li>
                            </ol>
                            <p className="text-slate-300">
                                Historically, gold and silver have served as hard money. Bitcoin introduced digital scarcity,
                                creating the first natively digital hard money.
                            </p>
                        </div>

                        <div id="hard-money-algorand" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">2.2 Hard Money on Algorand</h3>
                            <p className="text-slate-300 mb-4">We classify the following assets as hard money on Algorand:</p>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-slate-700">
                                            <th className="text-left py-3 px-4 text-slate-300 font-semibold">Asset</th>
                                            <th className="text-left py-3 px-4 text-slate-300 font-semibold">ASA ID</th>
                                            <th className="text-left py-3 px-4 text-slate-300 font-semibold">Supply</th>
                                            <th className="text-left py-3 px-4 text-slate-300 font-semibold">Rationale</th>
                                        </tr>
                                    </thead>
                                    <tbody className="text-slate-400">
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4 font-medium text-white">ALGO</td>
                                            <td className="py-3 px-4">Native</td>
                                            <td className="py-3 px-4">10B fixed</td>
                                            <td className="py-3 px-4">Network native, finite supply, participation rewards</td>
                                        </tr>
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4 font-medium text-orange-400">goBTC</td>
                                            <td className="py-3 px-4">386192725</td>
                                            <td className="py-3 px-4">BTC-backed</td>
                                            <td className="py-3 px-4">Wrapped Bitcoin, inherits BTC's properties</td>
                                        </tr>
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4 font-medium text-yellow-400">GOLD$</td>
                                            <td className="py-3 px-4">246516580</td>
                                            <td className="py-3 px-4">Gold-backed</td>
                                            <td className="py-3 px-4">Tokenized physical gold, redeemable</td>
                                        </tr>
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4 font-medium text-slate-300">SILVER$</td>
                                            <td className="py-3 px-4">246519683</td>
                                            <td className="py-3 px-4">Silver-backed</td>
                                            <td className="py-3 px-4">Tokenized physical silver, redeemable</td>
                                        </tr>
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4 font-medium text-purple-400">iGA</td>
                                            <td className="py-3 px-4">2635992378</td>
                                            <td className="py-3 px-4">333 fixed</td>
                                            <td className="py-3 px-4">Earned through node participation, ultra-scarce</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div id="exclusion-criteria" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">2.3 Exclusion Criteria</h3>
                            <p className="text-slate-300 mb-4">Assets are <strong className="text-red-400">not</strong> classified as hard money if they:</p>
                            <ul className="text-slate-300 space-y-2 list-disc list-inside mb-4">
                                <li>Have unlimited or governance-controlled supply</li>
                                <li>Depend on a single centralized issuer without backing</li>
                                <li>Are primarily speculative/memetic in nature</li>
                                <li>Lack clear scarcity mechanics</li>
                                <li>Have concentrated ownership that enables manipulation</li>
                            </ul>
                            <p className="text-slate-300">
                                This excludes most DeFi governance tokens, memecoins, NFTs, and unbacked stablecoins from
                                hard money classification.
                            </p>
                        </div>

                        <div id="iga-exception" className="scroll-mt-24">
                            <h3 className="text-2xl font-semibold text-white mb-4">2.4 The iGetAlgo Exception</h3>
                            <p className="text-slate-300 mb-4">
                                iGetAlgo (iGA) deserves special mention. With only 333 tokens in existence, it represents the
                                scarcest asset on Algorand. More importantly, iGA is <strong className="text-purple-400">earned</strong> by
                                running participation nodes—directly tying its distribution to network decentralization.
                            </p>
                            <p className="text-slate-300">
                                iGA embodies the incentive structure Algorand needs: contribute to decentralization, earn hard
                                money. We consider iGA a model for sovereignty-aligned tokenomics.
                            </p>
                        </div>
                    </section>

                    {/* 3. Sovereignty Ratio */}
                    <section id="sovereignty-ratio" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">3. The Sovereignty Ratio</h2>

                        <div id="ratio-definition" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">3.1 Definition</h3>
                            <p className="text-slate-300 mb-4">
                                The Sovereignty Ratio measures how long an individual can sustain their lifestyle using only
                                hard money assets:
                            </p>
                            <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 my-6">
                                <code className="text-lg text-slate-200 block text-center">
                                    <span className="text-orange-400">Sovereignty Ratio</span> = Hard Money Portfolio Value (USD) / Annual Fixed Expenses (USD)
                                </code>
                            </div>
                            <p className="text-slate-300 mb-2">
                                <strong className="text-white">Hard Money Portfolio Value</strong> includes only assets meeting
                                our hard money criteria (Section 2.2).
                            </p>
                            <p className="text-slate-300">
                                <strong className="text-white">Annual Fixed Expenses</strong> are non-discretionary costs: housing,
                                utilities, insurance, transportation, food, healthcare, debt service.
                            </p>
                        </div>

                        <div id="ratio-interpretation" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">3.2 Interpretation</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-slate-700">
                                            <th className="text-left py-3 px-4 text-slate-300 font-semibold">Ratio</th>
                                            <th className="text-left py-3 px-4 text-slate-300 font-semibold">Status</th>
                                            <th className="text-left py-3 px-4 text-slate-300 font-semibold">Interpretation</th>
                                        </tr>
                                    </thead>
                                    <tbody className="text-slate-400">
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4">&lt; 1.0</td>
                                            <td className="py-3 px-4 font-semibold text-red-400">Vulnerable</td>
                                            <td className="py-3 px-4">Less than one year of runway. A single crisis could force compromise of values for survival.</td>
                                        </tr>
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4">1.0 - 3.0</td>
                                            <td className="py-3 px-4 font-semibold text-orange-400">Fragile</td>
                                            <td className="py-3 px-4">Some buffer exists, but extended adversity would exhaust reserves. Still dependent on income.</td>
                                        </tr>
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4">3.0 - 6.0</td>
                                            <td className="py-3 px-4 font-semibold text-yellow-400">Robust</td>
                                            <td className="py-3 px-4">Can weather most storms. Job loss, illness, or economic downturn won't force immediate capitulation.</td>
                                        </tr>
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4">6.0 - 20.0</td>
                                            <td className="py-3 px-4 font-semibold text-green-400">Antifragile</td>
                                            <td className="py-3 px-4">Benefits from volatility. Market crashes are buying opportunities, not existential threats.</td>
                                        </tr>
                                        <tr className="border-b border-slate-800">
                                            <td className="py-3 px-4">&gt; 20.0</td>
                                            <td className="py-3 px-4 font-semibold text-emerald-400">Generationally Sovereign</td>
                                            <td className="py-3 px-4">Wealth that outlasts the individual. Can make multi-generational decisions.</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div id="why-fixed-expenses" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">3.3 Why Fixed Expenses?</h3>
                            <p className="text-slate-300 mb-4">We use fixed expenses rather than total expenses because:</p>
                            <ol className="text-slate-300 space-y-2 list-decimal list-inside">
                                <li><strong className="text-white">Fixed expenses are non-negotiable</strong> - You can reduce discretionary spending instantly; fixed costs require lifestyle restructuring</li>
                                <li><strong className="text-white">They represent your baseline</strong> - The minimum cost to maintain your current life</li>
                                <li><strong className="text-white">They're more stable</strong> - Easier to project and plan around</li>
                                <li><strong className="text-white">They reveal true dependency</strong> - High fixed expenses = high system dependency</li>
                            </ol>
                        </div>

                        <div id="ratio-limitations" className="scroll-mt-24">
                            <h3 className="text-2xl font-semibold text-white mb-4">3.4 Limitations</h3>
                            <p className="text-slate-300 mb-4">The Sovereignty Ratio is a simplification. It does not account for:</p>
                            <ul className="text-slate-300 space-y-2 list-disc list-inside mb-4">
                                <li>Inflation erosion of purchasing power</li>
                                <li>Volatility of hard money asset prices</li>
                                <li>Geographic cost-of-living differences</li>
                                <li>Non-financial aspects of sovereignty (health, skills, community)</li>
                            </ul>
                            <p className="text-slate-300">
                                We recommend users treat the ratio as a directional indicator, not a precise prediction.
                            </p>
                        </div>
                    </section>

                    {/* 4. Asset Classification */}
                    <section id="asset-classification" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">4. Asset Classification Framework</h2>

                        <div id="four-tier-system" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">4.1 Four-Tier System</h3>
                            <p className="text-slate-300 mb-4">We classify all Algorand assets into four tiers:</p>
                            <div className="grid sm:grid-cols-2 gap-4 mb-6">
                                <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
                                    <h4 className="font-bold text-orange-400 mb-2">Tier 1: Hard Money</h4>
                                    <ul className="text-slate-300 text-sm space-y-1">
                                        <li>Bitcoin (goBTC), Gold (GOLD$), Silver (SILVER$), iGA</li>
                                        <li>ALGO (when participating in consensus)</li>
                                        <li className="text-orange-400">Counts toward Sovereignty Ratio</li>
                                    </ul>
                                </div>
                                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
                                    <h4 className="font-bold text-green-400 mb-2">Tier 2: Productive Assets</h4>
                                    <ul className="text-slate-300 text-sm space-y-1">
                                        <li>Yield-bearing positions (LP tokens, staking derivatives)</li>
                                        <li>Stablecoins (USDC, USDt)</li>
                                        <li>DeFi governance tokens with utility</li>
                                        <li className="text-slate-500">Does not count toward Sovereignty Ratio</li>
                                    </ul>
                                </div>
                                <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                                    <h4 className="font-bold text-purple-400 mb-2">Tier 3: Collectibles</h4>
                                    <ul className="text-slate-300 text-sm space-y-1">
                                        <li>NFTs, domain names (NFD)</li>
                                        <li>Speculative but potentially valuable</li>
                                        <li className="text-slate-500">Does not count toward Sovereignty Ratio</li>
                                    </ul>
                                </div>
                                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
                                    <h4 className="font-bold text-red-400 mb-2">Tier 4: Speculation</h4>
                                    <ul className="text-slate-300 text-sm space-y-1">
                                        <li>Memecoins, unclassified tokens</li>
                                        <li>No clear value proposition</li>
                                        <li className="text-slate-500">Does not count toward Sovereignty Ratio</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <div id="classification-logic" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">4.2 Classification Logic</h3>
                            <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 font-mono text-sm overflow-x-auto">
                                <pre className="text-slate-300">{`Is supply fixed and verifiable?
├── No → Tier 4 (Speculation)
└── Yes → Is it backed by hard assets or network security?
    ├── No → Tier 3 or 4 (case by case)
    └── Yes → Is it censorship resistant?
        ├── No → Tier 2 (Productive)
        └── Yes → Tier 1 (Hard Money)`}</pre>
                            </div>
                        </div>

                        <div id="algo-classification" className="scroll-mt-24">
                            <h3 className="text-2xl font-semibold text-white mb-4">4.3 ALGO's Conditional Classification</h3>
                            <p className="text-slate-300 mb-4">
                                ALGO is classified as hard money <strong className="text-orange-400">only when the holder is
                                    participating in consensus</strong> (running a participation node or delegating to one).
                                Non-participating ALGO is classified as Tier 2 (Productive Asset).
                            </p>
                            <p className="text-slate-300">
                                This reflects our belief that ALGO's value derives from network security. Holding ALGO without
                                participating is rent-seeking; participating is contribution.
                            </p>
                        </div>
                    </section>

                    {/* 5. Decentralization Imperative */}
                    <section id="decentralization-imperative" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">5. Algorand's Decentralization Imperative</h2>

                        <div id="current-state" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">5.1 Current State</h3>
                            <p className="text-slate-300 mb-4">As of late 2024, Algorand's stake distribution shows concerning centralization:</p>
                            <ul className="text-slate-300 space-y-2 list-disc list-inside mb-4">
                                <li>The Algorand Foundation controls a significant percentage of total stake</li>
                                <li>Relay nodes are predominantly Foundation-operated</li>
                                <li>Development direction is Foundation-led</li>
                            </ul>
                            <p className="text-slate-300 mb-4">This creates risks:</p>
                            <ul className="text-slate-300 space-y-2 list-disc list-inside">
                                <li><strong className="text-red-400">Regulatory capture</strong> - A single entity can be pressured by governments</li>
                                <li><strong className="text-red-400">Key person risk</strong> - Leadership changes could alter network direction</li>
                                <li><strong className="text-red-400">Economic dependency</strong> - Ecosystem projects depend on Foundation grants</li>
                            </ul>
                        </div>

                        <div id="path-to-decentralization" className="scroll-mt-24 mb-8">
                            <h3 className="text-2xl font-semibold text-white mb-4">5.2 The Path to Decentralization</h3>
                            <p className="text-slate-300 mb-4">Algorand can decentralize through:</p>
                            <ol className="text-slate-300 space-y-2 list-decimal list-inside">
                                <li><strong className="text-white">Stake distribution</strong> - Foundation gradually reducing holdings</li>
                                <li><strong className="text-white">Participation node growth</strong> - More independent validators</li>
                                <li><strong className="text-white">Relay node decentralization</strong> - Community-operated relays</li>
                                <li><strong className="text-white">Development diversification</strong> - Multiple independent teams building core infrastructure</li>
                            </ol>
                        </div>

                        <div id="how-we-contribute" className="scroll-mt-24">
                            <h3 className="text-2xl font-semibold text-white mb-4">5.3 How We Contribute</h3>
                            <p className="text-slate-300 mb-4">The Sovereignty Analyzer contributes by:</p>
                            <ul className="text-slate-300 space-y-2 list-disc list-inside">
                                <li><strong className="text-orange-400">Education</strong> - Teaching users how to run participation nodes</li>
                                <li><strong className="text-orange-400">Measurement</strong> - Tracking decentralization metrics publicly</li>
                                <li><strong className="text-orange-400">Incentive alignment</strong> - Promoting iGA and other participation rewards</li>
                                <li><strong className="text-orange-400">Community building</strong> - Connecting sovereignty-minded Algorand users</li>
                            </ul>
                        </div>
                    </section>

                    {/* 6. Roadmap */}
                    <section id="roadmap" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">6. Roadmap</h2>

                        <div className="space-y-6">
                            <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6">
                                <h4 className="font-bold text-green-400 mb-3">Phase 1: Foundation (Current)</h4>
                                <ul className="text-slate-300 space-y-1 list-disc list-inside">
                                    <li>Sovereignty Ratio calculation</li>
                                    <li>Hard money classification</li>
                                    <li>Wallet analysis dashboard</li>
                                    <li>Educational content</li>
                                </ul>
                            </div>

                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
                                <h4 className="font-bold text-blue-400 mb-3">Phase 2: Network Intelligence</h4>
                                <ul className="text-slate-300 space-y-1 list-disc list-inside">
                                    <li>Decentralization metrics dashboard</li>
                                    <li>Participation node guide</li>
                                    <li>Node health monitoring</li>
                                    <li>Historical tracking</li>
                                </ul>
                            </div>

                            <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-6">
                                <h4 className="font-bold text-purple-400 mb-3">Phase 3: Incentive Layer</h4>
                                <ul className="text-slate-300 space-y-1 list-disc list-inside">
                                    <li>Achievement badge NFTs</li>
                                    <li>Auto-mining utilities (ALGO → hard money conversion)</li>
                                    <li>Participation rewards integration</li>
                                </ul>
                            </div>

                            <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-6">
                                <h4 className="font-bold text-orange-400 mb-3">Phase 4: Ecosystem Expansion</h4>
                                <ul className="text-slate-300 space-y-1 list-disc list-inside">
                                    <li>Multi-chain support</li>
                                    <li>Partner integrations</li>
                                    <li>Community governance</li>
                                    <li>API for third-party builders</li>
                                </ul>
                            </div>
                        </div>
                    </section>

                    {/* 7. Conclusion */}
                    <section id="conclusion" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">7. Conclusion</h2>
                        <p className="text-slate-300 text-lg mb-4">
                            Financial sovereignty is not a destination—it's a practice. The Algorand Sovereignty Analyzer
                            provides tools to measure progress, classify assets honestly, and contribute to network decentralization.
                        </p>
                        <p className="text-slate-300 text-lg mb-6">
                            Algorand has the technical foundation to be the most accessible sovereign blockchain. Whether it
                            achieves that potential depends on the community building alternatives to Foundation dependency.
                        </p>
                        <p className="text-xl font-bold text-orange-400 text-center py-6">
                            We're building those alternatives.
                        </p>
                    </section>

                    {/* Appendix A */}
                    <section id="appendix-a" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">Appendix A: Asset Classification Table</h2>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-slate-700">
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Asset</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">ASA ID</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Classification</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Rationale</th>
                                    </tr>
                                </thead>
                                <tbody className="text-slate-400">
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-white">ALGO (participating)</td>
                                        <td className="py-3 px-4">Native</td>
                                        <td className="py-3 px-4 text-orange-400">Hard Money</td>
                                        <td className="py-3 px-4">Network native, consensus participation</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-white">ALGO (non-participating)</td>
                                        <td className="py-3 px-4">Native</td>
                                        <td className="py-3 px-4 text-green-400">Productive</td>
                                        <td className="py-3 px-4">Holding without contributing</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-orange-400">goBTC</td>
                                        <td className="py-3 px-4">386192725</td>
                                        <td className="py-3 px-4 text-orange-400">Hard Money</td>
                                        <td className="py-3 px-4">Wrapped Bitcoin</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-yellow-400">GOLD$</td>
                                        <td className="py-3 px-4">246516580</td>
                                        <td className="py-3 px-4 text-orange-400">Hard Money</td>
                                        <td className="py-3 px-4">Tokenized gold</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-slate-300">SILVER$</td>
                                        <td className="py-3 px-4">246519683</td>
                                        <td className="py-3 px-4 text-orange-400">Hard Money</td>
                                        <td className="py-3 px-4">Tokenized silver</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-purple-400">iGA</td>
                                        <td className="py-3 px-4">2635992378</td>
                                        <td className="py-3 px-4 text-orange-400">Hard Money</td>
                                        <td className="py-3 px-4">333 fixed supply, earned via nodes</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-white">USDC</td>
                                        <td className="py-3 px-4">31566704</td>
                                        <td className="py-3 px-4 text-green-400">Productive</td>
                                        <td className="py-3 px-4">Stablecoin, centralized issuer</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-white">USDt</td>
                                        <td className="py-3 px-4">312769</td>
                                        <td className="py-3 px-4 text-green-400">Productive</td>
                                        <td className="py-3 px-4">Stablecoin, centralized issuer</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-white">xALGO</td>
                                        <td className="py-3 px-4">Various</td>
                                        <td className="py-3 px-4 text-green-400">Productive</td>
                                        <td className="py-3 px-4">Liquid staking derivative</td>
                                    </tr>
                                    <tr className="border-b border-slate-800">
                                        <td className="py-3 px-4 font-medium text-white">TMPOOL2</td>
                                        <td className="py-3 px-4">Various</td>
                                        <td className="py-3 px-4 text-green-400">Productive</td>
                                        <td className="py-3 px-4">LP tokens</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Appendix B */}
                    <section id="appendix-b" className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">Appendix B: Sovereignty Ratio Examples</h2>

                        <div className="space-y-6">
                            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6">
                                <h4 className="font-bold text-red-400 mb-3">Example 1: Early Accumulator</h4>
                                <ul className="text-slate-300 space-y-1 mb-3">
                                    <li><strong>Hard Money:</strong> $25,000 (mostly ALGO + small goBTC position)</li>
                                    <li><strong>Annual Fixed Expenses:</strong> $36,000</li>
                                    <li><strong>Sovereignty Ratio:</strong> 0.69 (Vulnerable)</li>
                                </ul>
                                <p className="text-slate-400 text-sm italic">
                                    Interpretation: ~8 months runway. Focus on increasing hard money or reducing fixed expenses.
                                </p>
                            </div>

                            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-6">
                                <h4 className="font-bold text-yellow-400 mb-3">Example 2: Robust Position</h4>
                                <ul className="text-slate-300 space-y-1 mb-3">
                                    <li><strong>Hard Money:</strong> $180,000 (ALGO + goBTC + GOLD$)</li>
                                    <li><strong>Annual Fixed Expenses:</strong> $48,000</li>
                                    <li><strong>Sovereignty Ratio:</strong> 3.75 (Robust)</li>
                                </ul>
                                <p className="text-slate-400 text-sm italic">
                                    Interpretation: Nearly 4 years runway. Can weather job loss or market downturn.
                                </p>
                            </div>

                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6">
                                <h4 className="font-bold text-emerald-400 mb-3">Example 3: Generationally Sovereign</h4>
                                <ul className="text-slate-300 space-y-1 mb-3">
                                    <li><strong>Hard Money:</strong> $2,400,000 (diversified hard money)</li>
                                    <li><strong>Annual Fixed Expenses:</strong> $72,000</li>
                                    <li><strong>Sovereignty Ratio:</strong> 33.3 (Generationally Sovereign)</li>
                                </ul>
                                <p className="text-slate-400 text-sm italic">
                                    Interpretation: Could sustain family for 30+ years on hard money alone.
                                </p>
                            </div>
                        </div>
                    </section>

                    {/* References */}
                    <section className="scroll-mt-24 mb-16">
                        <h2 className="text-3xl font-bold text-white border-b border-slate-800 pb-4 mb-6">References</h2>
                        <ol className="text-slate-400 space-y-2 list-decimal list-inside">
                            <li>Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System</li>
                            <li>Taleb, N.N. (2012). Antifragile: Things That Gain from Disorder</li>
                            <li>Algorand Foundation. Pure Proof of Stake Documentation</li>
                            <li>Ammous, S. (2018). The Bitcoin Standard</li>
                        </ol>
                    </section>

                    {/* Footer */}
                    <footer className="border-t border-slate-800 pt-8 text-center text-slate-500 text-sm space-y-2">
                        <p>Document Version: 1.0 | Last Updated: December 2024</p>
                        <p>License: CC BY-SA 4.0</p>
                        <div className="pt-4 space-x-4">
                            <a href="https://algosovereignty.com" className="hover:text-orange-400">Website</a>
                        </div>
                    </footer>
                </article>
            </div>

            {/* Mobile TOC */}
            <MobileTableOfContents activeSection={activeSection} />

            {/* Back to Top */}
            {showBackToTop && (
                <button
                    onClick={scrollToTop}
                    className="fixed bottom-4 left-4 z-40 p-3 bg-orange-500 text-white rounded-full shadow-lg hover:bg-orange-600 transition-colors lg:bottom-8 lg:left-8"
                    aria-label="Back to top"
                >
                    <ArrowUp className="w-5 h-5" />
                </button>
            )}
        </div>
    )
}
