'use client'

import { Coins, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

// Hard money partner data - centralized for consistency
const HARD_MONEY_PARTNERS = [
    {
        id: 'meld',
        name: 'Meld Gold & Silver',
        shortName: 'Meld',
        description: "Tokenized precious metals on Algorand. Real gold and silver, fully backed, redeemable. Hard money that's been hard money for 5,000 years.",
        shortDescription: 'Tokenized precious metals. Fully backed, redeemable.',
        asaIds: { gold: '246516580', silver: '246519683' },
        link: 'https://meld.gold',
        icon: Coins,
        color: 'yellow',
    },
    {
        id: 'gobtc',
        name: 'goBTC (Wrapped Bitcoin)',
        shortName: 'goBTC',
        description: "Bitcoin is the hardest money ever created. goBTC brings it to Algorand, letting you hold the apex predator of crypto assets while using Algorand's infrastructure.",
        shortDescription: 'Wrapped Bitcoin on Algorand. The apex predator.',
        asaId: '386192725',
        link: 'https://app.algomint.io/',
        icon: Coins,
        color: 'orange',
    },
] as const

interface PartnerCardProps {
    name: string
    description: string
    asaId?: string
    asaIds?: { gold: string; silver: string }
    supply?: string
    link: string
    icon: React.ReactNode
    color: string
    variant: 'full' | 'compact'
}

function PartnerCard({ name, description, asaId, asaIds, supply, link, icon, color, variant }: PartnerCardProps) {
    // Map colors to Tailwind classes (can't use dynamic classes)
    const colorClasses = {
        yellow: {
            border: 'hover:border-yellow-500/50',
            bg: 'bg-yellow-500/10',
            borderBg: 'border-yellow-500/30',
            text: 'text-yellow-400',
            link: 'text-yellow-400 hover:text-yellow-300',
        },
        orange: {
            border: 'hover:border-orange-500/50',
            bg: 'bg-orange-500/10',
            borderBg: 'border-orange-500/30',
            text: 'text-orange-400',
            link: 'text-orange-400 hover:text-orange-300',
        },
    }[color] || {
        border: 'hover:border-slate-500/50',
        bg: 'bg-slate-500/10',
        borderBg: 'border-slate-500/30',
        text: 'text-slate-400',
        link: 'text-slate-400 hover:text-slate-300',
    }

    if (variant === 'compact') {
        return (
            <Card className={`bg-slate-900/50 border-slate-800 ${colorClasses.border} transition-colors`}>
                <CardContent className="py-4">
                    <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg ${colorClasses.bg} border ${colorClasses.borderBg} flex items-center justify-center flex-shrink-0`}>
                            {icon}
                        </div>
                        <div className="flex-1 min-w-0">
                            <h4 className="font-semibold text-white truncate">{name}</h4>
                            {asaId && (
                                <p className="text-xs text-slate-500">ASA: {asaId}</p>
                            )}
                            {asaIds && (
                                <p className="text-xs text-slate-500">ASA: {asaIds.gold} / {asaIds.silver}</p>
                            )}
                        </div>
                        <a
                            href={link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`${colorClasses.link} transition-colors`}
                            aria-label={`Learn more about ${name}`}
                        >
                            <ExternalLink className="w-4 h-4" />
                        </a>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className={`bg-slate-900/50 border-slate-800 ${colorClasses.border} transition-colors`}>
            <CardHeader>
                <div className={`mb-2 w-12 h-12 rounded-xl ${colorClasses.bg} border ${colorClasses.borderBg} flex items-center justify-center`}>
                    {icon}
                </div>
                <CardTitle className="text-xl text-white">{name}</CardTitle>
                {(asaId || asaIds) && (
                    <div className="flex gap-3 text-xs text-slate-500">
                        {asaId && <span>ASA: {asaId}</span>}
                        {asaIds && <span>ASA: {asaIds.gold} (GOLD$) / {asaIds.silver} (SILVER$)</span>}
                        {supply && <span>Supply: {supply}</span>}
                    </div>
                )}
            </CardHeader>
            <CardContent className="space-y-4">
                <CardDescription className="text-slate-400">
                    {description}
                </CardDescription>
                <a
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-flex items-center gap-2 text-sm ${colorClasses.link} transition-colors`}
                >
                    Learn more <ExternalLink className="w-3 h-3" />
                </a>
            </CardContent>
        </Card>
    )
}

interface HardMoneyPartnersProps {
    variant?: 'full' | 'compact'
    showTitle?: boolean
    className?: string
}

export function HardMoneyPartners({ variant = 'full', showTitle = true, className = '' }: HardMoneyPartnersProps) {
    const gridCols = variant === 'full'
        ? 'grid-cols-1 md:grid-cols-2'
        : 'grid-cols-1 sm:grid-cols-2'

    return (
        <section className={`space-y-8 ${className}`}>
            {showTitle && (
                <div className="text-center space-y-4">
                    <h2 className="text-3xl font-bold text-white">Hard Money Partners</h2>
                    <p className="text-slate-400">
                        Projects aligned with sovereignty principles on Algorand.
                    </p>
                </div>
            )}

            <div className={`grid ${gridCols} gap-6`}>
                {HARD_MONEY_PARTNERS.map((partner) => {
                    const Icon = partner.icon
                    const iconColor = {
                        yellow: 'text-yellow-400',
                        orange: 'text-orange-400',
                    }[partner.color] || 'text-slate-400'

                    return (
                        <PartnerCard
                            key={partner.id}
                            name={variant === 'compact' ? partner.shortName : partner.name}
                            description={variant === 'compact' ? partner.shortDescription : partner.description}
                            asaId={'asaId' in partner ? partner.asaId : undefined}
                            asaIds={'asaIds' in partner ? partner.asaIds : undefined}
                            supply={'supply' in partner ? partner.supply : undefined}
                            link={partner.link}
                            icon={<Icon className={`w-6 h-6 ${iconColor}`} />}
                            color={partner.color}
                            variant={variant}
                        />
                    )
                })}
            </div>
        </section>
    )
}

// Export partner data for use elsewhere if needed
export { HARD_MONEY_PARTNERS }
