'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Calendar,
  TrendingUp,
  TrendingDown,
  Clock,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Target,
  BarChart3,
  AlertCircle,
} from 'lucide-react'
import { DataDisclaimer } from '@/components/DataDisclaimer'
import {
  getUpcomingEarnings,
  getEarningsCalendar,
  getEarningsStats,
  getSectorEarningsStats,
  EarningsEvent,
  BeatMissStats,
  SectorEarningsStats,
} from '@/lib/api'

type ViewMode = 'upcoming' | 'calendar' | 'stats'
type MetalFilter = 'all' | 'gold' | 'silver'

export function EarningsCalendar() {
  const [view, setView] = useState<ViewMode>('upcoming')
  const [metalFilter, setMetalFilter] = useState<MetalFilter>('all')
  const [upcomingEvents, setUpcomingEvents] = useState<EarningsEvent[]>([])
  const [calendarEvents, setCalendarEvents] = useState<EarningsEvent[]>([])
  const [sectorStats, setSectorStats] = useState<SectorEarningsStats | null>(null)
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)
  const [tickerStats, setTickerStats] = useState<BeatMissStats | null>(null)
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch upcoming earnings
  useEffect(() => {
    if (view === 'upcoming') {
      setLoading(true)
      getUpcomingEarnings(60)
        .then((data) => {
          setUpcomingEvents(data.events)
          setError(null)
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }
  }, [view])

  // Fetch calendar events
  useEffect(() => {
    if (view === 'calendar') {
      setLoading(true)
      getEarningsCalendar(currentMonth)
        .then((data) => {
          setCalendarEvents(data.events)
          setError(null)
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }
  }, [view, currentMonth])

  // Fetch sector stats
  useEffect(() => {
    if (view === 'stats') {
      setLoading(true)
      const metal = metalFilter === 'all' ? undefined : metalFilter
      getSectorEarningsStats(metal)
        .then((data) => {
          setSectorStats(data.stats)
          setError(null)
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false))
    }
  }, [view, metalFilter])

  // Fetch individual ticker stats
  useEffect(() => {
    if (selectedTicker) {
      getEarningsStats(selectedTicker)
        .then((data) => setTickerStats(data.stats))
        .catch(() => setTickerStats(null))
    } else {
      setTickerStats(null)
    }
  }, [selectedTicker])

  const filteredUpcoming = upcomingEvents.filter(
    (e) => metalFilter === 'all' || e.metal === metalFilter
  )

  const filteredCalendar = calendarEvents.filter(
    (e) => metalFilter === 'all' || e.metal === metalFilter
  )

  const navigateMonth = (direction: -1 | 1) => {
    const [year, month] = currentMonth.split('-').map(Number)
    const date = new Date(year, month - 1 + direction, 1)
    setCurrentMonth(`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`)
  }

  const formatMonthYear = (monthStr: string) => {
    const [year, month] = monthStr.split('-').map(Number)
    return new Date(year, month - 1).toLocaleDateString('en-US', {
      month: 'long',
      year: 'numeric',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Calendar className="h-8 w-8 text-amber-500" />
            Miner Earnings Calendar
          </h1>
          <p className="text-slate-400 mt-1">
            Track quarterly earnings, beat/miss history, and price reactions
          </p>
        </div>

        {/* Metal Filter */}
        <div className="flex gap-2">
          {(['all', 'gold', 'silver'] as const).map((filter) => (
            <Button
              key={filter}
              variant={metalFilter === filter ? 'default' : 'outline'}
              size="sm"
              onClick={() => setMetalFilter(filter)}
              className={
                metalFilter === filter
                  ? filter === 'gold'
                    ? 'bg-amber-600 hover:bg-amber-700'
                    : filter === 'silver'
                    ? 'bg-slate-500 hover:bg-slate-600'
                    : ''
                  : ''
              }
            >
              {filter === 'all' ? 'All' : filter === 'gold' ? 'Gold' : 'Silver'}
            </Button>
          ))}
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 border-b border-slate-700 pb-2">
        {[
          { id: 'upcoming', label: 'Upcoming', icon: Clock },
          { id: 'calendar', label: 'Calendar', icon: Calendar },
          { id: 'stats', label: 'Statistics', icon: BarChart3 },
        ].map(({ id, label, icon: Icon }) => (
          <Button
            key={id}
            variant={view === id ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setView(id as ViewMode)}
            className="gap-2"
          >
            <Icon className="h-4 w-4" />
            {label}
          </Button>
        ))}
      </div>

      {error && (
        <Card className="bg-red-900/20 border-red-800">
          <CardContent className="pt-6">
            <p className="text-red-400 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {error}
            </p>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-slate-700 rounded w-1/3" />
              <div className="h-24 bg-slate-700 rounded" />
              <div className="h-24 bg-slate-700 rounded" />
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Upcoming View */}
          {view === 'upcoming' && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredUpcoming.length === 0 ? (
                <Card className="bg-slate-800/50 border-slate-700 col-span-full">
                  <CardContent className="pt-6 text-center text-slate-400">
                    No upcoming earnings in the next 60 days
                  </CardContent>
                </Card>
              ) : (
                filteredUpcoming.map((event) => (
                  <EarningsCard
                    key={event.id}
                    event={event}
                    onSelect={() => setSelectedTicker(event.ticker)}
                    isSelected={selectedTicker === event.ticker}
                  />
                ))
              )}
            </div>
          )}

          {/* Calendar View */}
          {view === 'calendar' && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Button variant="ghost" size="sm" onClick={() => navigateMonth(-1)}>
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <CardTitle className="text-white">{formatMonthYear(currentMonth)}</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => navigateMonth(1)}>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <CalendarGrid
                  month={currentMonth}
                  events={filteredCalendar}
                  onSelectTicker={setSelectedTicker}
                />
              </CardContent>
            </Card>
          )}

          {/* Statistics View */}
          {view === 'stats' && sectorStats && (
            <div className="space-y-6">
              {/* Sector Summary */}
              <div className="grid gap-4 md:grid-cols-4">
                <StatCard
                  label="Companies Tracked"
                  value={sectorStats.total_companies}
                  icon={Target}
                />
                <StatCard
                  label="Upcoming Earnings"
                  value={sectorStats.upcoming_count}
                  icon={Clock}
                />
                <StatCard
                  label="Sector EPS Beat Rate"
                  value={`${sectorStats.sector_avg_eps_beat_rate.toFixed(0)}%`}
                  icon={CheckCircle2}
                  color="green"
                />
                <StatCard
                  label="Avg 1-Day Reaction"
                  value={
                    sectorStats.sector_avg_1d_reaction
                      ? `${sectorStats.sector_avg_1d_reaction > 0 ? '+' : ''}${sectorStats.sector_avg_1d_reaction.toFixed(1)}%`
                      : 'N/A'
                  }
                  icon={sectorStats.sector_avg_1d_reaction && sectorStats.sector_avg_1d_reaction > 0 ? TrendingUp : TrendingDown}
                  color={sectorStats.sector_avg_1d_reaction && sectorStats.sector_avg_1d_reaction > 0 ? 'green' : 'red'}
                />
              </div>

              {/* Next Earnings */}
              {sectorStats.next_earnings.ticker && (
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Next Scheduled Earnings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4">
                      <div className="text-2xl font-bold text-amber-500">
                        {sectorStats.next_earnings.ticker}
                      </div>
                      <div className="text-slate-400">
                        {sectorStats.next_earnings.date &&
                          new Date(sectorStats.next_earnings.date).toLocaleDateString('en-US', {
                            weekday: 'long',
                            month: 'long',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedTicker(sectorStats.next_earnings.ticker)}
                      >
                        View Stats
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Ticker Detail Modal */}
          {selectedTicker && tickerStats && (
            <Card className="bg-slate-800/50 border-amber-600/50">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white flex items-center gap-2">
                    <span
                      className={
                        tickerStats.metal === 'gold' ? 'text-amber-500' : 'text-slate-400'
                      }
                    >
                      {tickerStats.ticker}
                    </span>
                    <span className="text-slate-500 font-normal">
                      {tickerStats.company_name}
                    </span>
                  </CardTitle>
                  <CardDescription>
                    Last {tickerStats.quarters_tracked} quarters tracked
                  </CardDescription>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setSelectedTicker(null)}>
                  Close
                </Button>
              </CardHeader>
              <CardContent>
                <BeatMissScorecard stats={tickerStats} />
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Disclaimer */}
      <DataDisclaimer className="mt-8" />
    </div>
  )
}

// Sub-components

function EarningsCard({
  event,
  onSelect,
  isSelected,
}: {
  event: EarningsEvent
  onSelect: () => void
  isSelected: boolean
}) {
  const isPast = new Date(event.earnings_date) < new Date()
  const metalColor = event.metal === 'gold' ? 'amber' : 'slate'

  return (
    <Card
      className={`bg-slate-800/50 border-slate-700 cursor-pointer transition-all hover:border-${metalColor}-500/50 ${
        isSelected ? `border-${metalColor}-500` : ''
      }`}
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={`text-lg font-bold ${
                event.metal === 'gold' ? 'text-amber-500' : 'text-slate-400'
              }`}
            >
              {event.ticker}
            </span>
            <span className="text-xs text-slate-500">{event.quarter}</span>
          </div>
          {event.days_until !== undefined && event.days_until >= 0 && (
            <span className="text-xs bg-slate-700 px-2 py-1 rounded text-slate-300">
              {event.days_until === 0
                ? 'Today'
                : event.days_until === 1
                ? 'Tomorrow'
                : `${event.days_until} days`}
            </span>
          )}
        </div>
        <CardDescription className="text-sm">{event.company_name}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Calendar className="h-4 w-4" />
          {new Date(event.earnings_date).toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
          })}
          <span className="text-xs">({event.time_of_day})</span>
          {!event.is_confirmed && (
            <span className="text-xs text-yellow-500">(Est.)</span>
          )}
        </div>

        {isPast && event.eps_actual !== null ? (
          // Past earnings - show results
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex items-center gap-1">
              {event.eps_beat ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <XCircle className="h-4 w-4 text-red-500" />
              )}
              <span className="text-slate-400">EPS:</span>
              <span className="text-white">${event.eps_actual?.toFixed(2)}</span>
            </div>
            {event.price_reaction_1d !== null && (
              <div className="flex items-center gap-1">
                {event.price_reaction_1d >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500" />
                )}
                <span
                  className={event.price_reaction_1d >= 0 ? 'text-green-500' : 'text-red-500'}
                >
                  {event.price_reaction_1d > 0 ? '+' : ''}
                  {event.price_reaction_1d.toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        ) : (
          // Future earnings - show estimates
          <div className="text-sm">
            {event.eps_estimate !== null && (
              <div className="text-slate-400">
                EPS Est: <span className="text-white">${event.eps_estimate.toFixed(2)}</span>
              </div>
            )}
            {event.aisc_guidance !== null && (
              <div className="text-slate-400">
                AISC Guide: <span className="text-white">${event.aisc_guidance}/oz</span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function CalendarGrid({
  month,
  events,
  onSelectTicker,
}: {
  month: string
  events: EarningsEvent[]
  onSelectTicker: (ticker: string) => void
}) {
  const [year, monthNum] = month.split('-').map(Number)
  const firstDay = new Date(year, monthNum - 1, 1)
  const lastDay = new Date(year, monthNum, 0)
  const startPad = firstDay.getDay()
  const totalDays = lastDay.getDate()

  // Group events by day
  const eventsByDay: Record<number, EarningsEvent[]> = {}
  events.forEach((e) => {
    const day = new Date(e.earnings_date).getDate()
    if (!eventsByDay[day]) eventsByDay[day] = []
    eventsByDay[day].push(e)
  })

  const days = []
  for (let i = 0; i < startPad; i++) {
    days.push(<div key={`pad-${i}`} className="h-24 bg-slate-900/30" />)
  }

  for (let day = 1; day <= totalDays; day++) {
    const dayEvents = eventsByDay[day] || []
    const isToday =
      new Date().toDateString() === new Date(year, monthNum - 1, day).toDateString()

    days.push(
      <div
        key={day}
        className={`h-24 p-1 border border-slate-700/50 ${
          isToday ? 'bg-amber-900/20 border-amber-600/50' : 'bg-slate-900/30'
        }`}
      >
        <div className={`text-xs mb-1 ${isToday ? 'text-amber-500 font-bold' : 'text-slate-500'}`}>
          {day}
        </div>
        <div className="space-y-0.5 overflow-y-auto max-h-[70px]">
          {dayEvents.map((e) => (
            <button
              key={e.id}
              onClick={() => onSelectTicker(e.ticker)}
              className={`w-full text-xs px-1 py-0.5 rounded text-left truncate ${
                e.metal === 'gold'
                  ? 'bg-amber-900/50 text-amber-300 hover:bg-amber-800/50'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/50'
              }`}
            >
              {e.ticker}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="grid grid-cols-7 text-center text-xs text-slate-500 mb-1">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
          <div key={d} className="py-1">
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-px">{days}</div>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon: Icon,
  color = 'amber',
}: {
  label: string
  value: string | number
  icon: React.ElementType
  color?: 'amber' | 'green' | 'red'
}) {
  const colorClasses = {
    amber: 'text-amber-500',
    green: 'text-green-500',
    red: 'text-red-500',
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="pt-4">
        <div className="flex items-center gap-3">
          <Icon className={`h-8 w-8 ${colorClasses[color]}`} />
          <div>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-xs text-slate-400">{label}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function BeatMissScorecard({ stats }: { stats: BeatMissStats }) {
  const metrics = [
    { label: 'EPS', data: stats.eps },
    { label: 'Revenue', data: stats.revenue },
    { label: 'Production', data: stats.production },
    { label: 'AISC', data: stats.aisc },
  ]

  return (
    <div className="space-y-4">
      {/* Beat/Miss Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map(({ label, data }) => (
          <div key={label} className="text-center">
            <div className="text-sm text-slate-400 mb-1">{label}</div>
            <div className="flex justify-center gap-1 mb-1">
              {Array.from({ length: data.beats + data.misses }).map((_, i) => (
                <div
                  key={i}
                  className={`w-4 h-4 rounded ${
                    i < data.beats ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
              ))}
            </div>
            <div className="text-lg font-bold text-white">{data.beat_rate.toFixed(0)}%</div>
            <div className="text-xs text-slate-500">
              {data.beats}/{data.beats + data.misses}
            </div>
          </div>
        ))}
      </div>

      {/* Price Reactions */}
      <div className="border-t border-slate-700 pt-4">
        <div className="text-sm text-slate-400 mb-2">Average Price Reactions</div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-slate-500 mb-1">Overall 1-Day</div>
            <div
              className={`text-lg font-bold ${
                stats.price_reactions.avg_1d && stats.price_reactions.avg_1d >= 0
                  ? 'text-green-500'
                  : 'text-red-500'
              }`}
            >
              {stats.price_reactions.avg_1d !== null
                ? `${stats.price_reactions.avg_1d > 0 ? '+' : ''}${stats.price_reactions.avg_1d.toFixed(1)}%`
                : 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">On Beat</div>
            <div className="text-lg font-bold text-green-500">
              {stats.price_reactions.avg_on_beat !== null
                ? `+${stats.price_reactions.avg_on_beat.toFixed(1)}%`
                : 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">On Miss</div>
            <div className="text-lg font-bold text-red-500">
              {stats.price_reactions.avg_on_miss !== null
                ? `${stats.price_reactions.avg_on_miss.toFixed(1)}%`
                : 'N/A'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
