import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { InflationCharts } from '@/components/InflationCharts'

export const metadata = {
  title: 'Inflation-Adjusted Charts | Sovereignty Analyzer',
  description: 'View gold and silver prices adjusted for inflation, M2 money supply comparison, and dollar purchasing power analysis.',
}

export default function InflationChartsPage() {
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
      <InflationCharts />
    </div>
  )
}
