import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
    Wallet,
    Activity,
    Brain,
    Clock,
    Database,
    Users,
    Shield,
    TrendingUp,
    ArrowRight
} from 'lucide-react'

export default function PhilosophyPage() {
    return (
        <div className="container mx-auto px-4 py-12 max-w-5xl space-y-24">

            {/* Hero Section */}
            <section className="text-center space-y-8 animate-in fade-in duration-700">
                <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent pb-2">
                    The Sovereignty Manifesto
                </h1>
                <blockquote className="text-2xl md:text-3xl text-slate-300 italic font-light max-w-3xl mx-auto leading-relaxed border-l-4 border-orange-500 pl-6 py-2">
                    "Sovereignty is measured not by what you own, but by how long you can say no."
                </blockquote>
                <p className="text-slate-500 uppercase tracking-widest text-sm font-semibold">
                    — Dylan Heiney, Founder, Sovereign Path LLC
                </p>
            </section>

            {/* The Illusion of Independence */}
            <section className="grid md:grid-cols-2 gap-12 items-center">
                <div className="space-y-6">
                    <h2 className="text-3xl font-bold text-white">The Illusion of Independence</h2>
                    <div className="space-y-4 text-slate-400 text-lg leading-relaxed">
                        <p>
                            We tell ourselves we're free. We have choices. We're independent. Then Friday rolls around and we realize we can't miss the paycheck. Then the rent is due. Then a medical emergency hits.
                        </p>
                        <p>
                            How free are you really if you can't say no to:
                        </p>
                        <ul className="list-disc pl-6 space-y-2 text-slate-300">
                            <li>A job that drains you because you need the insurance?</li>
                            <li>Processed food because it's cheap and convenient?</li>
                            <li>A commute that steals 10 hours a week?</li>
                            <li>Doom-scrolling because your dopamine system is hijacked?</li>
                        </ul>
                        <p className="font-semibold text-orange-400">
                            This isn't freedom. It's a treadmill with better marketing.
                        </p>
                    </div>
                </div>
                <div className="bg-slate-900/50 p-8 rounded-2xl border border-slate-800 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/10 blur-3xl rounded-full -mr-32 -mt-32" />
                    <h3 className="text-2xl font-bold text-white mb-6">The Sovereignty Test</h3>
                    <p className="text-slate-400 mb-8">
                        How long could you maintain your current quality of life if your primary income disappeared tomorrow?
                    </p>

                    <div className="space-y-6">
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-red-400 font-bold">&lt; 3 Months</span>
                                <span className="text-slate-500">Vulnerable</span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full w-[20%] bg-red-500/50" />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-yellow-400 font-bold">3-12 Months</span>
                                <span className="text-slate-500">Breathing Room</span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full w-[50%] bg-yellow-500/50" />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-green-400 font-bold">1-3 Years</span>
                                <span className="text-slate-500">Sovereign</span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full w-[80%] bg-green-500/50" />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-emerald-400 font-bold">3+ Years</span>
                                <span className="text-slate-500">Deep Sovereignty</span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full w-full bg-emerald-500/50" />
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* The Six Paths */}
            <section className="space-y-12">
                <div className="text-center max-w-3xl mx-auto">
                    <h2 className="text-3xl font-bold text-white mb-4">The Six Paths to Sovereignty</h2>
                    <p className="text-slate-400 text-lg">
                        Sovereignty isn't built in one dimension. It's built across six interconnected areas. Neglect any one, and you create a point of failure.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <PathCard
                        icon={<Wallet className="w-8 h-8 text-green-400" />}
                        title="Financial Sovereignty"
                        description="Control over your economic future. The ability to weather storms and seize opportunities."
                        metrics={["Runway (Months)", "Debt-to-Income", "Hard Assets %", "Income Streams"]}
                    />
                    <PathCard
                        icon={<Activity className="w-8 h-8 text-red-400" />}
                        title="Physical Sovereignty"
                        description="Your body is either an asset or a liability. Health determines your longevity and clarity."
                        metrics={["VO2 Max", "Strength/Weight", "Resting HR/HRV", "Clean Eating Streak"]}
                    />
                    <PathCard
                        icon={<Brain className="w-8 h-8 text-purple-400" />}
                        title="Cognitive Sovereignty"
                        description="Control over your attention. In an economy of distraction, deep thought is a superpower."
                        metrics={["Deep Work Hours", "Screen Time", "Books Read", "Sleep Quality"]}
                    />
                    <PathCard
                        icon={<Clock className="w-8 h-8 text-blue-400" />}
                        title="Temporal Sovereignty"
                        description="The difference between being owned by your calendar and owning it."
                        metrics={["Uninterrupted Time", "Meeting Load", "Commute Time", "Schedule Control"]}
                    />
                    <PathCard
                        icon={<Database className="w-8 h-8 text-orange-400" />}
                        title="Data Sovereignty"
                        description="Control over your digital footprint. Your data is valuable—who profits from it?"
                        metrics={["Data Ownership %", "Account Resilience", "Backup Capability", "Privacy Tools"]}
                    />
                    <PathCard
                        icon={<Users className="w-8 h-8 text-pink-400" />}
                        title="Social Sovereignty"
                        description="The network of people who would help you without expecting payment."
                        metrics={["Crisis Contacts", "Face-to-Face Hours", "Reciprocity", "Community Role"]}
                    />
                </div>
            </section>

            {/* Data as Foundation */}
            <section className="bg-slate-900/30 border border-slate-800 rounded-3xl p-8 md:p-12 text-center space-y-8">
                <div className="inline-flex items-center justify-center p-4 bg-slate-800 rounded-full mb-4">
                    <TrendingUp className="w-8 h-8 text-blue-400" />
                </div>
                <h2 className="text-3xl font-bold text-white">Why Data is the Foundation</h2>
                <div className="max-w-3xl mx-auto text-slate-400 text-lg space-y-6">
                    <p>
                        Every tech company tracks everything about you: your clicks, your location, your purchases. They use this data to optimize <em>their</em> outcomes: more engagement, more revenue.
                    </p>
                    <p className="text-white font-medium text-xl">
                        What if you tracked the same data and optimized for <em>your</em> outcomes?
                    </p>
                    <div className="bg-slate-950/50 p-6 rounded-xl border border-slate-800 text-left">
                        <h4 className="text-blue-400 font-bold mb-2 uppercase tracking-wider text-sm">The Sovereignty Tracker Thesis</h4>
                        <p className="italic text-slate-300">
                            "If you systematically track the metrics that matter for sovereignty across all six paths, and you review that data daily with the goal of incremental improvement, you will become more sovereign over time. It's not magic. It's physics."
                        </p>
                    </div>
                </div>
            </section>

            {/* Daily Practice */}
            <section className="grid md:grid-cols-2 gap-12 items-start">
                <div className="space-y-8">
                    <h2 className="text-3xl font-bold text-white">The Practice of Daily Sovereignty</h2>
                    <p className="text-slate-400 text-lg">
                        Sovereignty isn't a destination. It's a daily practice.
                    </p>

                    <div className="space-y-6">
                        <PracticeStep number="1" title="Morning Review" time="5 min" desc="Check your dashboard. Where are you strong? Where are you slipping? Set one intention." />
                        <PracticeStep number="2" title="Daily Tracking" time="30 sec" desc="Log your data. Workouts, expenses, deep work, Bitcoin buys." />
                        <PracticeStep number="3" title="Evening Reflection" time="2 min" desc="Did today move you toward sovereignty or away? What will you change tomorrow?" />
                        <PracticeStep number="4" title="Weekly Analysis" time="15 min" desc="Review trends. Identify patterns. Adjust systems." />
                    </div>
                </div>

                <div className="space-y-8">
                    <h2 className="text-3xl font-bold text-white">The Compound Effect</h2>
                    <div className="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-8 space-y-6">
                        <p className="text-slate-400 leading-relaxed">
                            Improving 1% per day doesn't feel like much. But compounded over a year, it's <span className="text-white font-bold">37x improvement</span>.
                        </p>
                        <p className="text-slate-400">
                            The person who:
                        </p>
                        <ul className="space-y-3">
                            <CheckItem text="Saves 20% of income into hard assets" />
                            <CheckItem text="Trains strength 4x/week" />
                            <CheckItem text="Protects 20 hours/week for deep work" />
                            <CheckItem text="Owns their data and systems" />
                        </ul>
                        <p className="text-slate-300 font-medium pt-4 border-t border-slate-800">
                            That person will be sovereign in 5 years. Not just rich. Free.
                        </p>
                    </div>

                    <div className="pt-4">
                        <Link href="/">
                            <Button className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white font-bold py-8 text-xl shadow-lg shadow-orange-900/20">
                                Start Tracking Your Sovereignty <ArrowRight className="ml-2 w-6 h-6" />
                            </Button>
                        </Link>
                        <p className="text-center text-slate-500 mt-4 text-sm">
                            Read more at <a href="https://www.sovereigntytracker.com/sovereignty" target="_blank" rel="noopener noreferrer" className="text-orange-500 hover:underline">SovereigntyTracker.com</a>
                        </p>
                    </div>
                </div>
            </section>
        </div>
    )
}

function PathCard({ icon, title, description, metrics }: { icon: any, title: string, description: string, metrics: string[] }) {
    return (
        <Card className="bg-slate-900/50 border-slate-800 hover:border-slate-700 transition-colors">
            <CardHeader>
                <div className="mb-4 bg-slate-950 w-fit p-3 rounded-xl border border-slate-800">
                    {icon}
                </div>
                <CardTitle className="text-xl text-white">{title}</CardTitle>
                <CardDescription className="text-slate-400 h-16">
                    {description}
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-2">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Key Metrics</p>
                    <ul className="text-sm text-slate-300 space-y-1">
                        {metrics.map((m, i) => (
                            <li key={i} className="flex items-center gap-2">
                                <div className="w-1 h-1 bg-slate-600 rounded-full" />
                                {m}
                            </li>
                        ))}
                    </ul>
                </div>
            </CardContent>
        </Card>
    )
}

function PracticeStep({ number, title, time, desc }: { number: string, title: string, time: string, desc: string }) {
    return (
        <div className="flex gap-4 items-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-800 text-white font-bold flex items-center justify-center border border-slate-700">
                {number}
            </div>
            <div>
                <div className="flex items-baseline gap-3 mb-1">
                    <h4 className="text-white font-bold">{title}</h4>
                    <span className="text-xs text-orange-400 font-mono bg-orange-400/10 px-2 py-0.5 rounded">{time}</span>
                </div>
                <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
            </div>
        </div>
    )
}

function CheckItem({ text }: { text: string }) {
    return (
        <li className="flex items-center gap-3 text-slate-300">
            <Shield className="w-4 h-4 text-green-500 flex-shrink-0" />
            <span>{text}</span>
        </li>
    )
}
