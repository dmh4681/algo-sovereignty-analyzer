import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EarningsCalendar } from '@/components/EarningsCalendar'

export const metadata = {
  title: 'Miner Earnings Calendar | Sovereignty Analyzer',
  description: 'Track gold and silver miner quarterly earnings, beat/miss history, and price reactions.',
}

export default function EarningsCalendarPage() {
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
      <EarningsCalendar />
    </div>
  )
}
