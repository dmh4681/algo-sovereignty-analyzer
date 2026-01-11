import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { CentralBankTracker } from '@/components/CentralBankTracker'

export const metadata = {
  title: 'Central Bank Gold Tracker | Sovereignty Analyzer',
  description: 'Track global central bank gold holdings, net purchases, and de-dollarization trends.',
}

export default function CentralBankGoldPage() {
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
      <CentralBankTracker />
    </div>
  )
}
