import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle2, XCircle, Server, ShieldCheck, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface NodeStatusCardProps {
    isParticipating: boolean
}

export function NodeStatusCard({ isParticipating }: NodeStatusCardProps) {
    if (isParticipating) {
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
                <CardContent>
                    <p className="text-slate-300 mb-4">
                        You are running a participation node and securing the Algorand network. This is the highest level of sovereignty.
                    </p>
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
