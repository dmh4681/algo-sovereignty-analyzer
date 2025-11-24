import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle2, XCircle, Server, ShieldCheck, TrendingUp, Calendar, Award } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ParticipationInfo {
    staked_amount: number
    vote_first_valid: number | null
    vote_last_valid: number | null
    key_expiration_rounds: number | null
    is_incentive_eligible: boolean
    estimated_apy: number
}

interface NodeStatusCardProps {
    isParticipating: boolean
    participationInfo?: ParticipationInfo
}

export function NodeStatusCard({ isParticipating, participationInfo }: NodeStatusCardProps) {
    if (isParticipating && participationInfo) {
        return (
            <Card className="bg-emerald-950/30 border-emerald-500/30 overflow-hidden relative">
                <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-3xl rounded-full -mr-16 -mt-16" />
                <CardHeader className="pb-2">
                    <div className="flex items-center gap-2 text-emerald-500 mb-1">
                        <ShieldCheck className="h-5 w-5" />
                        <span className="text-sm font-bold tracking-wider uppercase">Network Sovereignty</span>
                    </div>
                    <CardTitle className="text-2xl text-white flex items-center gap-3">
                        <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                        Participating Node
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p className="text-slate-300 text-sm">
                        You are running a participation node and securing the Algorand network. This is the highest level of sovereignty.
                    </p>

                    {/* Metrics Grid */}
                    <div className="grid grid-cols-2 gap-3 pt-2">
                        <div className="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/20">
                            <div className="flex items-center gap-2 text-emerald-400 mb-1">
                                <TrendingUp className="h-4 w-4" />
                                <span className="text-xs font-semibold uppercase tracking-wider">Staked</span>
                            </div>
                            <div className="text-lg font-bold text-white">
                                {participationInfo.staked_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })} ALGO
                            </div>
                        </div>

                        <div className="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/20">
                            <div className="flex items-center gap-2 text-emerald-400 mb-1">
                                <TrendingUp className="h-4 w-4" />
                                <span className="text-xs font-semibold uppercase tracking-wider">Est. APY</span>
                            </div>
                            <div className="text-lg font-bold text-white">
                                ~{participationInfo.estimated_apy.toFixed(1)}%
                            </div>
                        </div>

                        {participationInfo.key_expiration_rounds && (
                            <div className="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/20">
                                <div className="flex items-center gap-2 text-emerald-400 mb-1">
                                    <Calendar className="h-4 w-4" />
                                    <span className="text-xs font-semibold uppercase tracking-wider">Key Expires</span>
                                </div>
                                <div className="text-sm font-mono text-white">
                                    Round {participationInfo.key_expiration_rounds.toLocaleString()}
                                </div>
                            </div>
                        )}

                        <div className="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/20">
                            <div className="flex items-center gap-2 text-emerald-400 mb-1">
                                <Award className="h-4 w-4" />
                                <span className="text-xs font-semibold uppercase tracking-wider">Eligible</span>
                            </div>
                            <div className="text-sm font-bold text-white">
                                {participationInfo.is_incentive_eligible ? (
                                    <span className="text-emerald-400">✓ Yes</span>
                                ) : (
                                    <span className="text-yellow-400">⚠ No</span>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-emerald-400 bg-emerald-500/10 w-fit px-3 py-1 rounded-full border border-emerald-500/20">
                        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                        Online & Consensus Active
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className="bg-slate-900/50 border-slate-800 overflow-hidden relative group hover:border-orange-500/30 transition-colors">
            <CardHeader className="pb-2">
                <div className="flex items-center gap-2 text-slate-500 mb-1">
                    <Server className="h-5 w-5" />
                    <span className="text-sm font-bold tracking-wider uppercase">Network Sovereignty</span>
                </div>
                <CardTitle className="text-xl text-slate-300 flex items-center gap-3">
                    <XCircle className="h-6 w-6 text-slate-500" />
                    Not Running a Node
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-slate-400 mb-4 text-sm leading-relaxed">
                    "Running a node is the ultimate act of sovereignty. By not running one, you are trusting others to verify your money."
                </p>
                <div className="flex flex-col sm:flex-row gap-3">
                    <Button
                        variant="outline"
                        className="border-orange-500/50 text-orange-500 hover:bg-orange-500 hover:text-white w-full sm:w-auto"
                        onClick={() => window.open('https://developer.algorand.org/docs/run-a-node/setup/install/', '_blank')}
                    >
                        <Server className="w-4 h-4 mr-2" />
                        Run a Node
                    </Button>
                    <Button
                        variant="ghost"
                        className="text-slate-400 hover:text-white w-full sm:w-auto"
                        onClick={() => window.open('https://www.algorand.foundation/general-faq#nodes', '_blank')}
                    >
                        Why it matters
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
