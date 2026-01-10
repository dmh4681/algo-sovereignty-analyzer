import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { GoldTracker } from '@/components/GoldTracker'

export const metadata = {
  title: 'Gold Sector Analyst | Sovereignty Analyzer',
  description: 'Track and analyze major gold mining companies quarterly performance, AISC costs, production, and jurisdictional risk.',
}

export default function GoldTrackerPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Back Navigation */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
        </Button>
      </div>

      {/* Main Component */}
      <GoldTracker />
    </div>
  )
}
