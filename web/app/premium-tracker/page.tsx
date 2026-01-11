import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PremiumTracker } from '@/components/PremiumTracker'

export const metadata = {
  title: 'Physical Premium Tracker | Sovereignty Analyzer',
  description: 'Compare premiums on physical gold and silver products across major dealers.',
}

export default function PremiumTrackerPage() {
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
      <PremiumTracker />
    </div>
  )
}
