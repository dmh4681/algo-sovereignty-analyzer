'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Shield, Coins, Building, Gamepad2, Fingerprint, Server, Sparkles } from 'lucide-react'
import type { EcosystemProject } from '@/lib/algorand-2025-research'

// ============================================================================
// Types
// ============================================================================

interface EcosystemGridProps {
  projects: EcosystemProject[]
  className?: string
}

type FilterType = 'all' | 'sovereignty' | EcosystemProject['category']

// ============================================================================
// Constants
// ============================================================================

const CATEGORY_CONFIG: Record<EcosystemProject['category'], { icon: React.ReactNode; color: string; bgColor: string }> = {
  'DeFi': { icon: <Coins className="h-3 w-3" />, color: 'text-cyan-400', bgColor: 'bg-cyan-500/20' },
  'RWA': { icon: <Building className="h-3 w-3" />, color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  'Gaming': { icon: <Gamepad2 className="h-3 w-3" />, color: 'text-purple-400', bgColor: 'bg-purple-500/20' },
  'Identity': { icon: <Fingerprint className="h-3 w-3" />, color: 'text-pink-400', bgColor: 'bg-pink-500/20' },
  'Infrastructure': { icon: <Server className="h-3 w-3" />, color: 'text-slate-400', bgColor: 'bg-slate-500/20' },
}

const FILTER_OPTIONS: { value: FilterType; label: string; icon?: React.ReactNode }[] = [
  { value: 'all', label: 'All' },
  { value: 'sovereignty', label: 'Sovereignty', icon: <Shield className="h-3 w-3" /> },
  { value: 'DeFi', label: 'DeFi', icon: <Coins className="h-3 w-3" /> },
  { value: 'RWA', label: 'RWA', icon: <Building className="h-3 w-3" /> },
  { value: 'Gaming', label: 'Gaming', icon: <Gamepad2 className="h-3 w-3" /> },
  { value: 'Identity', label: 'Identity', icon: <Fingerprint className="h-3 w-3" /> },
  { value: 'Infrastructure', label: 'Infra', icon: <Server className="h-3 w-3" /> },
]

// ============================================================================
// Project Card Component
// ============================================================================

interface ProjectCardProps {
  project: EcosystemProject
}

function ProjectCard({ project }: ProjectCardProps) {
  const categoryConfig = CATEGORY_CONFIG[project.category]

  return (
    <Card className={`border-slate-700 bg-slate-900/50 hover:border-slate-600 transition-all duration-300 group ${
      project.sovereigntyRelevant ? 'ring-1 ring-green-500/20' : ''
    }`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base font-semibold text-slate-200 group-hover:text-white transition-colors">
            {project.name}
          </CardTitle>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {project.sovereigntyRelevant && (
              <Badge className="bg-green-500/20 text-green-400 border border-green-500/30 text-xs px-1.5 py-0">
                <Shield className="h-2.5 w-2.5 mr-1" />
                Sovereignty
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <Badge className={`${categoryConfig.bgColor} ${categoryConfig.color} border-0 text-xs flex items-center gap-1`}>
            {categoryConfig.icon}
            {project.category}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Status */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-xs text-slate-400">{project.status}</span>
        </div>

        {/* Description */}
        <p className="text-sm text-slate-400 leading-relaxed">
          {project.description}
        </p>

        {/* Link */}
        {project.url && (
          <a
            href={project.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-orange-400 hover:text-orange-300 transition-colors pt-1"
          >
            Visit {project.name}
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Sovereignty Highlight Card
// ============================================================================

function SovereigntyHighlight() {
  return (
    <Card className="border-green-500/30 bg-gradient-to-br from-green-500/5 to-green-500/10 col-span-full">
      <CardContent className="py-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <Shield className="h-5 w-5 text-green-500" />
          </div>
          <div>
            <h4 className="font-semibold text-green-400 mb-1">Sovereignty Relevant Projects</h4>
            <p className="text-sm text-slate-400">
              These projects directly support financial sovereignty through hard money assets,
              real-world asset backing, or infrastructure that enables self-custody and decentralization.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function EcosystemGrid({ projects, className = '' }: EcosystemGridProps) {
  const [filter, setFilter] = useState<FilterType>('all')

  // Filter projects
  const filteredProjects = useMemo(() => {
    if (filter === 'all') return projects
    if (filter === 'sovereignty') return projects.filter(p => p.sovereigntyRelevant)
    return projects.filter(p => p.category === filter)
  }, [projects, filter])

  // Count projects per category
  const counts = useMemo(() => {
    const result: Record<string, number> = {
      all: projects.length,
      sovereignty: projects.filter(p => p.sovereigntyRelevant).length,
    }
    projects.forEach(p => {
      result[p.category] = (result[p.category] || 0) + 1
    })
    return result
  }, [projects])

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Filter Bar */}
      <div className="flex flex-wrap gap-2">
        {FILTER_OPTIONS.map((option) => {
          const isActive = filter === option.value
          const count = counts[option.value] || 0

          return (
            <Button
              key={option.value}
              variant={isActive ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(option.value)}
              className={`
                ${isActive
                  ? option.value === 'sovereignty'
                    ? 'bg-green-500 hover:bg-green-600 text-white'
                    : 'bg-orange-500 hover:bg-orange-600 text-white'
                  : 'border-slate-600 hover:border-slate-500 text-slate-300'
                }
                transition-all duration-200
              `}
            >
              {option.icon && <span className="mr-1.5">{option.icon}</span>}
              {option.label}
              <span className={`ml-1.5 text-xs ${isActive ? 'opacity-80' : 'text-slate-500'}`}>
                ({count})
              </span>
            </Button>
          )
        })}
      </div>

      {/* Sovereignty Highlight (only when filter is sovereignty) */}
      {filter === 'sovereignty' && <SovereigntyHighlight />}

      {/* Project Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredProjects.map((project) => (
          <ProjectCard key={project.name} project={project} />
        ))}
      </div>

      {/* Empty State */}
      {filteredProjects.length === 0 && (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">🔍</div>
          <p className="text-slate-400">No projects found in this category.</p>
        </div>
      )}

      {/* Summary Stats */}
      <div className="flex justify-center gap-6 pt-4 border-t border-slate-800 text-sm text-slate-500">
        <span>
          Showing <span className="text-slate-300 font-medium">{filteredProjects.length}</span> of {projects.length} projects
        </span>
        <span className="text-slate-700">|</span>
        <span className="flex items-center gap-1.5">
          <Shield className="h-3 w-3 text-green-500" />
          <span className="text-green-400 font-medium">{counts.sovereignty}</span> sovereignty-relevant
        </span>
      </div>
    </div>
  )
}

// ============================================================================
// Compact Grid (for summaries)
// ============================================================================

interface EcosystemCompactProps {
  projects: EcosystemProject[]
  maxItems?: number
  showSovereigntyOnly?: boolean
  className?: string
}

export function EcosystemCompact({
  projects,
  maxItems = 6,
  showSovereigntyOnly = false,
  className = ''
}: EcosystemCompactProps) {
  const displayProjects = useMemo(() => {
    let filtered = showSovereigntyOnly ? projects.filter(p => p.sovereigntyRelevant) : projects
    return filtered.slice(0, maxItems)
  }, [projects, maxItems, showSovereigntyOnly])

  return (
    <div className={`space-y-3 ${className}`}>
      {displayProjects.map((project) => {
        const categoryConfig = CATEGORY_CONFIG[project.category]
        return (
          <div
            key={project.name}
            className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700"
          >
            <div className="flex items-center gap-3">
              <div className={`p-1.5 rounded ${categoryConfig.bgColor}`}>
                {categoryConfig.icon}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-200 text-sm">{project.name}</span>
                  {project.sovereigntyRelevant && (
                    <Shield className="h-3 w-3 text-green-500" />
                  )}
                </div>
                <span className="text-xs text-slate-500">{project.status}</span>
              </div>
            </div>
            {project.url && (
              <a
                href={project.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-500 hover:text-orange-400 transition-colors"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ============================================================================
// Featured Projects (horizontal scroll)
// ============================================================================

interface FeaturedProjectsProps {
  projects: EcosystemProject[]
  className?: string
}

export function FeaturedProjects({ projects, className = '' }: FeaturedProjectsProps) {
  // Only show sovereignty-relevant projects as "featured"
  const featured = projects.filter(p => p.sovereigntyRelevant)

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-200 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-amber-500" />
          Featured: Sovereignty Partners
        </h3>
        <Badge variant="outline" className="text-green-400 border-green-500/30">
          {featured.length} projects
        </Badge>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-2 -mx-2 px-2">
        {featured.map((project) => {
          const categoryConfig = CATEGORY_CONFIG[project.category]
          return (
            <a
              key={project.name}
              href={project.url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 w-64 p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-green-500/30 transition-all group"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg ${categoryConfig.bgColor}`}>
                  {categoryConfig.icon}
                </div>
                <div>
                  <div className="font-medium text-slate-200 group-hover:text-white">
                    {project.name}
                  </div>
                  <Badge className={`${categoryConfig.bgColor} ${categoryConfig.color} text-xs`}>
                    {project.category}
                  </Badge>
                </div>
              </div>
              <p className="text-xs text-slate-400 line-clamp-2">
                {project.description}
              </p>
              <div className="flex items-center gap-1 mt-3 text-xs text-green-400">
                <Shield className="h-3 w-3" />
                Sovereignty Relevant
              </div>
            </a>
          )
        })}
      </div>
    </div>
  )
}

export default EcosystemGrid
