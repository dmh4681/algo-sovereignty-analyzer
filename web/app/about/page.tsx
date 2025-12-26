import Link from 'next/link'
import {
    AlertTriangle,
    BarChart3,
    Eye,
    GraduationCap,
    ArrowRight,
    Coins,
    Shield,
    Users,
    Wallet,
    FileText,
    ExternalLink,
    Bitcoin
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { HardMoneyPartners } from '@/components/HardMoneyPartners'

export default function AboutPage() {
    return (
        <div className="max-w-5xl mx-auto space-y-20 py-8">
            {/* Hero Section */}
            <section className="text-center space-y-6">
                <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                    About the{' '}
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-orange-600">
                        Sovereignty Analyzer
                    </span>
                </h1>
                <p className="text-xl text-slate-400 max-w-3xl mx-auto">
                    Infrastructure for the decentralization movement. Measuring sovereignty, tracking hard money,
                    and building the tools Algorand needs to escape Foundation dependency.
                </p>
            </section>

            {/* The Problem Section */}
            <section className="space-y-6">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-red-500/10 rounded-xl border border-red-500/30">
                        <AlertTriangle className="w-6 h-6 text-red-400" />
                    </div>
                    <h2 className="text-3xl font-bold text-white">The Problem We're Solving</h2>
                </div>

                <Card className="bg-gradient-to-br from-red-950/30 to-slate-950 border-red-500/30">
                    <CardContent className="py-8 space-y-6">
                        <p className="text-lg text-slate-300">
                            Algorand has the technical foundation to be one of the most sovereign blockchains in existence:
                            Pure Proof of Stake, carbon negative, instant finality, low fees. But there's a problem nobody wants to talk about.
                        </p>

                        <div className="bg-red-950/50 border border-red-500/30 rounded-xl p-6">
                            <p className="text-xl font-bold text-red-400 text-center">
                                The network is dangerously centralized.
                            </p>
                        </div>

                        <p className="text-slate-400">
                            The Algorand Foundation controls a massive percentage of the stake, the relay nodes, and the
                            development direction. This isn't a conspiracy theory—it's public information. And it means that
                            despite all of Algorand's technical advantages, the network has a single point of failure.
                        </p>

                        <p className="text-slate-400">
                            If the Foundation makes a bad decision, gets regulatory pressure, or simply runs out of runway,
                            the entire ecosystem is at risk. That's not sovereignty. That's dependence with extra steps.
                        </p>
                    </CardContent>
                </Card>
            </section>

            {/* What We're Building */}
            <section className="space-y-8">
                <div className="text-center space-y-4">
                    <h2 className="text-3xl font-bold text-white">What We're Building</h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        The Algorand Sovereignty Analyzer is infrastructure for the decentralization movement.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                    <Card className="bg-slate-900/50 border-slate-800 hover:border-orange-500/30 transition-colors">
                        <CardHeader>
                            <div className="mb-2 w-12 h-12 rounded-xl bg-orange-500/10 border border-orange-500/30 flex items-center justify-center">
                                <BarChart3 className="w-6 h-6 text-orange-400" />
                            </div>
                            <CardTitle className="text-lg text-white">Measure Your Sovereignty</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-slate-400 text-sm">
                                Not just your portfolio value, but how long you can say "no" to systems of control.
                                Calculate your freedom runway in years.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900/50 border-slate-800 hover:border-yellow-500/30 transition-colors">
                        <CardHeader>
                            <div className="mb-2 w-12 h-12 rounded-xl bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center">
                                <Coins className="w-6 h-6 text-yellow-400" />
                            </div>
                            <CardTitle className="text-lg text-white">Track Hard Money</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-slate-400 text-sm">
                                Bitcoin, gold, silver, and other limited-supply assets that preserve wealth across
                                generations. See what's real vs. speculation.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900/50 border-slate-800 hover:border-cyan-500/30 transition-colors">
                        <CardHeader>
                            <div className="mb-2 w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                                <Eye className="w-6 h-6 text-cyan-400" />
                            </div>
                            <CardTitle className="text-lg text-white">Visualize Decentralization</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-slate-400 text-sm">
                                See where the network stands and where it needs to go. Track relay node distribution,
                                provider concentration, and infrastructure sovereignty.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900/50 border-slate-800 hover:border-green-500/30 transition-colors">
                        <CardHeader>
                            <div className="mb-2 w-12 h-12 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center justify-center">
                                <GraduationCap className="w-6 h-6 text-green-400" />
                            </div>
                            <CardTitle className="text-lg text-white">Educate & Onboard</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-slate-400 text-sm">
                                Help more people run participation nodes and contribute to network security.
                                Training guides, tutorials, and hands-on learning.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </section>

            {/* The Sovereignty Thesis */}
            <section className="space-y-8">
                <div className="text-center space-y-4">
                    <h2 className="text-3xl font-bold text-white">The Sovereignty Thesis</h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        Sovereignty isn't about getting rich. It's about having enough resources to make decisions
                        based on your values instead of your desperation.
                    </p>
                </div>

                <Card className="bg-slate-900/80 border-orange-500/30">
                    <CardContent className="py-8">
                        <div className="text-center mb-8">
                            <p className="text-slate-400 mb-2">We measure this with the</p>
                            <h3 className="text-2xl font-bold text-orange-400 mb-4">Sovereignty Ratio</h3>
                            <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 inline-block">
                                <code className="text-lg text-slate-200">
                                    <span className="text-orange-400">Sovereignty Ratio</span> = Hard Money Portfolio Value / Annual Fixed Expenses
                                </code>
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-slate-800">
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Status</th>
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Ratio</th>
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Meaning</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="border-b border-slate-800/50">
                                        <td className="py-3 px-4">
                                            <span className="text-red-400 font-semibold">Vulnerable</span>
                                        </td>
                                        <td className="py-3 px-4 text-slate-300">&lt; 1 year</td>
                                        <td className="py-3 px-4 text-slate-400">One crisis away from compromise</td>
                                    </tr>
                                    <tr className="border-b border-slate-800/50">
                                        <td className="py-3 px-4">
                                            <span className="text-orange-400 font-semibold">Fragile</span>
                                        </td>
                                        <td className="py-3 px-4 text-slate-300">1-3 years</td>
                                        <td className="py-3 px-4 text-slate-400">Some buffer, still dependent</td>
                                    </tr>
                                    <tr className="border-b border-slate-800/50">
                                        <td className="py-3 px-4">
                                            <span className="text-yellow-400 font-semibold">Robust</span>
                                        </td>
                                        <td className="py-3 px-4 text-slate-300">3-6 years</td>
                                        <td className="py-3 px-4 text-slate-400">Can weather most storms</td>
                                    </tr>
                                    <tr className="border-b border-slate-800/50">
                                        <td className="py-3 px-4">
                                            <span className="text-green-400 font-semibold">Antifragile</span>
                                        </td>
                                        <td className="py-3 px-4 text-slate-300">6-20 years</td>
                                        <td className="py-3 px-4 text-slate-400">Grows stronger from volatility</td>
                                    </tr>
                                    <tr>
                                        <td className="py-3 px-4">
                                            <span className="text-emerald-400 font-semibold">Generationally Sovereign</span>
                                        </td>
                                        <td className="py-3 px-4 text-slate-300">20+ years</td>
                                        <td className="py-3 px-4 text-slate-400">Wealth that outlasts you</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <p className="text-center text-orange-400 font-medium mt-8">
                            The goal isn't a number. The goal is freedom.
                        </p>
                    </CardContent>
                </Card>
            </section>

            {/* Why Algorand */}
            <section className="space-y-6">
                <h2 className="text-3xl font-bold text-white">Why Algorand?</h2>

                <Card className="bg-slate-900/50 border-slate-800">
                    <CardContent className="py-8 space-y-6">
                        <p className="text-slate-300">
                            Despite the centralization concerns, we're building on Algorand because:
                        </p>

                        <div className="grid sm:grid-cols-2 gap-4">
                            <div className="flex items-start gap-3">
                                <Shield className="w-5 h-5 text-orange-400 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-white">Pure Proof of Stake</p>
                                    <p className="text-sm text-slate-400">Your stake secures the network, not warehouses of mining rigs</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <Server className="w-5 h-5 text-orange-400 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-white">Participation Nodes are Accessible</p>
                                    <p className="text-sm text-slate-400">You can run one on a Raspberry Pi</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <Shield className="w-5 h-5 text-orange-400 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-white">Sound Technical Foundation</p>
                                    <p className="text-sm text-slate-400">Fast, cheap, carbon negative</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <Users className="w-5 h-5 text-orange-400 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-white">The Community Gets It</p>
                                    <p className="text-sm text-slate-400">Projects like iGetAlgo are already incentivizing decentralization</p>
                                </div>
                            </div>
                        </div>

                        <p className="text-slate-400 border-l-2 border-orange-500/50 pl-4 italic">
                            Algorand's problem isn't technical—it's political. And political problems can be solved
                            by building alternatives to Foundation dependency.
                        </p>
                    </CardContent>
                </Card>
            </section>

            {/* Hard Money Partners */}
            <HardMoneyPartners variant="full" />

            {/* Who Built This */}
            <section className="space-y-6">
                <h2 className="text-3xl font-bold text-white">Who Built This</h2>

                <Card className="bg-slate-900/50 border-slate-800">
                    <CardContent className="py-8">
                        <div className="flex flex-col md:flex-row items-start gap-8">
                            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-orange-500/20 to-yellow-500/20 border border-orange-500/30 flex items-center justify-center flex-shrink-0">
                                <Wallet className="w-10 h-10 text-orange-400" />
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <h3 className="text-xl font-bold text-white">Dylan Heiney</h3>
                                    <p className="text-slate-400">Sovereign Path LLC</p>
                                </div>
                                <p className="text-slate-300">
                                    I run my own Algorand participation node. I hold ALGO, iGA, and other hard money assets.
                                    I'm building this because I need it myself—and because Algorand needs more people building
                                    for decentralization rather than waiting for the Foundation to solve everything.
                                </p>
                                <p className="text-orange-400 font-medium">
                                    Sovereignty over status. Decentralization over convenience. Hard money over hype.
                                </p>
                                <a
                                    href="https://twitter.com/sovereignpath"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-orange-400 transition-colors"
                                >
                                    @sovereignpath <ExternalLink className="w-3 h-3" />
                                </a>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </section>

            {/* Get Involved CTA */}
            <section className="space-y-8">
                <h2 className="text-3xl font-bold text-white text-center">Get Involved</h2>

                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Link href="/analyze">
                        <Card className="bg-slate-900/50 border-slate-800 hover:border-orange-500/50 transition-colors cursor-pointer h-full">
                            <CardContent className="py-6 text-center space-y-3">
                                <BarChart3 className="w-8 h-8 text-orange-400 mx-auto" />
                                <h3 className="font-semibold text-white">Analyze Your Wallet</h3>
                                <p className="text-sm text-slate-400">See where you stand on the sovereignty spectrum</p>
                            </CardContent>
                        </Card>
                    </Link>

                    <a
                        href="https://meld.gold"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        <Card className="bg-slate-900/50 border-slate-800 hover:border-yellow-500/50 transition-colors cursor-pointer h-full">
                            <CardContent className="py-6 text-center space-y-3">
                                <div className="relative mx-auto w-8 h-8">
                                    <Coins className="w-8 h-8 text-yellow-400" />
                                    <ExternalLink className="w-3 h-3 text-yellow-400 absolute -top-1 -right-1" />
                                </div>
                                <h3 className="font-semibold text-white">Stack Gold</h3>
                                <p className="text-sm text-slate-400">Tokenized physical gold on Algorand</p>
                            </CardContent>
                        </Card>
                    </a>

                    <a
                        href="https://meld.gold"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        <Card className="bg-slate-900/50 border-slate-800 hover:border-slate-500/50 transition-colors cursor-pointer h-full">
                            <CardContent className="py-6 text-center space-y-3">
                                <div className="relative mx-auto w-8 h-8">
                                    <Coins className="w-8 h-8 text-slate-300" />
                                    <ExternalLink className="w-3 h-3 text-slate-300 absolute -top-1 -right-1" />
                                </div>
                                <h3 className="font-semibold text-white">Stack Silver</h3>
                                <p className="text-sm text-slate-400">Tokenized physical silver on Algorand</p>
                            </CardContent>
                        </Card>
                    </a>

                    <a
                        href="https://www.algomint.io/"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        <Card className="bg-slate-900/50 border-slate-800 hover:border-orange-500/50 transition-colors cursor-pointer h-full">
                            <CardContent className="py-6 text-center space-y-3">
                                <div className="relative mx-auto w-8 h-8">
                                    <Bitcoin className="w-8 h-8 text-orange-500" />
                                    <ExternalLink className="w-3 h-3 text-orange-500 absolute -top-1 -right-1" />
                                </div>
                                <h3 className="font-semibold text-white">Stack Bitcoin</h3>
                                <p className="text-sm text-slate-400">Wrapped Bitcoin on Algorand</p>
                            </CardContent>
                        </Card>
                    </a>
                </div>
            </section>

            {/* Whitepaper CTA */}
            <section>
                <Card className="bg-gradient-to-br from-orange-500/10 to-slate-950 border-orange-500/30">
                    <CardContent className="py-8">
                        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                            <div className="flex items-center gap-4">
                                <div className="p-4 bg-orange-500/20 rounded-xl">
                                    <FileText className="w-8 h-8 text-orange-400" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">Read the Whitepaper</h3>
                                    <p className="text-slate-400">
                                        The full technical and philosophical framework behind the Sovereignty Analyzer
                                    </p>
                                </div>
                            </div>
                            <Link href="/whitepaper">
                                <Button className="gap-2">
                                    Read Whitepaper <ArrowRight className="w-4 h-4" />
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </section>

            {/* Quote */}
            <section className="text-center py-8">
                <blockquote className="text-2xl text-slate-400 italic max-w-2xl mx-auto">
                    "Sovereignty is measured not by what you own, but by how long you can say no."
                </blockquote>
            </section>
        </div>
    )
}
