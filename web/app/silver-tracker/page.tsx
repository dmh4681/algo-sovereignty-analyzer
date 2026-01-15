import Link from 'next/link'
import { ArrowLeft, Pickaxe, Mountain } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SilverTracker } from '@/components/SilverTracker'

export const metadata = {
  title: 'Silver Mine Operations | Sovereignty Analyzer',
  description: 'Track and analyze major silver mining companies quarterly performance, AISC costs, production, and jurisdictional risk.',
}

export default function SilverTrackerPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Back Navigation */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Mine
          </Link>
        </Button>
      </div>

      {/* Mining Header */}
      <div className="text-center space-y-4 py-4">
        <div className="flex items-center justify-center gap-3">
          <Mountain className="h-8 w-8 text-gray-400/70" />
          <h1 className="text-3xl md:text-4xl font-bold">
            <span className="silver-shimmer">Silver Mine Operations</span>
          </h1>
          <Pickaxe className="h-8 w-8 text-gray-400/70" />
        </div>
        <p className="text-amber-200/60 max-w-2xl mx-auto">
          Track the world&apos;s largest silver mining operations. Analyze production costs,
          output volumes, and jurisdictional risks across the global silver supply chain.
        </p>
      </div>

      {/* Main Component */}
      <SilverTracker />
    </div>
  )
}
