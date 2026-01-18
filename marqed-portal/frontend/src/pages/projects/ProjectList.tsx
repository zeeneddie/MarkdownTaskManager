import { useList } from '@refinedev/core'
import { Link } from 'react-router-dom'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import {
  FolderKanban,
  Search,
  Filter,
  Calendar,
  LayoutGrid,
  List,
  ChevronRight,
  GitBranch,
  FileCode2,
  TrendingUp,
  Clock,
  CheckCircle2,
  X,
} from 'lucide-react'
import { cn, formatDate, formatRelativeTime } from '@/lib/utils'
import { useState } from 'react'

interface Project {
  id: string
  name: string
  description: string
  status: string
  created_at: string
  updated_at: string
  lines_of_code?: number
  quality_score?: number
  repositories_count?: number
}

// Mock additional data for demonstration
const mockProjectData: Record<string, { lines_of_code: number; quality_score: number; repositories_count: number }> = {
  '1': { lines_of_code: 245000, quality_score: 78, repositories_count: 3 },
  '2': { lines_of_code: 1200000, quality_score: 65, repositories_count: 8 },
  '3': { lines_of_code: 89000, quality_score: 92, repositories_count: 2 },
}

function getScoreColor(score: number) {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-marqed-orange'
  return 'text-red-600'
}

function getScoreBgColor(score: number) {
  if (score >= 80) return 'bg-green-500'
  if (score >= 60) return 'bg-marqed-orange'
  return 'bg-red-500'
}

function formatLinesOfCode(loc: number) {
  if (loc >= 1000000) return `${(loc / 1000000).toFixed(1)}M`
  if (loc >= 1000) return `${(loc / 1000).toFixed(0)}K`
  return loc.toString()
}

type ViewMode = 'grid' | 'list'
type StatusFilter = 'all' | 'active' | 'pending' | 'completed'

export function ProjectList() {
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [showFilters, setShowFilters] = useState(false)

  const { data: projectsData, isLoading } = useList<Project>({
    resource: 'projects',
    pagination: { current: 1, pageSize: 20 },
    sorters: [{ field: 'updated_at', order: 'desc' }],
    filters: [
      ...(searchQuery
        ? [{ field: 'name', operator: 'contains' as const, value: searchQuery }]
        : []),
      ...(statusFilter !== 'all'
        ? [{ field: 'status', operator: 'eq' as const, value: statusFilter }]
        : []),
    ],
  })

  const projects = projectsData?.data || []
  const totalProjects = projectsData?.total || 0

  // Enrich projects with mock data
  const enrichedProjects = projects.map((p) => ({
    ...p,
    ...mockProjectData[p.id] || { lines_of_code: 50000, quality_score: 75, repositories_count: 1 },
  }))

  const statusCounts = {
    all: totalProjects,
    active: projects.filter((p) => p.status === 'active').length,
    pending: projects.filter((p) => p.status === 'pending').length,
    completed: projects.filter((p) => p.status === 'completed').length,
  }

  return (
    <div className="space-y-6">
      {/* Header with gradient */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-marqed-blue-dark via-marqed-blue to-marqed-blue-medium p-6 text-white">
        <div className="absolute inset-0 marqed-circuit-lines opacity-10" />
        <div className="relative z-10">
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <FolderKanban className="h-7 w-7" />
            Projecten
          </h1>
          <p className="text-white/80 mt-1">
            Beheer en bekijk al uw legacy modernisatie projecten
          </p>
        </div>
        <div className="absolute top-4 right-4 w-20 h-20 rounded-full bg-marqed-orange/20 blur-2xl" />
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Totaal', value: statusCounts.all, icon: FolderKanban, color: 'text-marqed-blue', bg: 'bg-marqed-blue/10' },
          { label: 'Actief', value: statusCounts.active, icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-100' },
          { label: 'In behandeling', value: statusCounts.pending, icon: Clock, color: 'text-marqed-orange', bg: 'bg-marqed-orange/10' },
          { label: 'Afgerond', value: statusCounts.completed, icon: CheckCircle2, color: 'text-purple-600', bg: 'bg-purple-100' },
        ].map((stat) => (
          <Card key={stat.label} className="border-0 shadow-sm">
            <CardContent className="p-4 flex items-center gap-3">
              <div className={cn('p-2 rounded-lg', stat.bg)}>
                <stat.icon className={cn('h-5 w-5', stat.color)} />
              </div>
              <div>
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Search and filters */}
      <Card className="border-marqed-blue/10">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Zoek projecten..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 focus-marqed"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={showFilters ? 'default' : 'outline'}
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
                className={showFilters ? 'bg-marqed-blue hover:bg-marqed-blue-dark' : ''}
              >
                <Filter className="mr-2 h-4 w-4" />
                Filter
                {statusFilter !== 'all' && (
                  <span className="ml-2 px-1.5 py-0.5 bg-marqed-orange text-white text-xs rounded-full">1</span>
                )}
              </Button>
              <div className="flex border rounded-lg overflow-hidden">
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    'rounded-none px-3',
                    viewMode === 'grid' && 'bg-marqed-blue/10 text-marqed-blue'
                  )}
                  onClick={() => setViewMode('grid')}
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    'rounded-none px-3',
                    viewMode === 'list' && 'bg-marqed-blue/10 text-marqed-blue'
                  )}
                  onClick={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Filter panel */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t flex flex-wrap gap-2">
              <span className="text-sm text-muted-foreground mr-2 py-1">Status:</span>
              {(['all', 'active', 'pending', 'completed'] as StatusFilter[]).map((status) => (
                <Button
                  key={status}
                  variant={statusFilter === status ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter(status)}
                  className={cn(
                    statusFilter === status && 'bg-marqed-blue hover:bg-marqed-blue-dark'
                  )}
                >
                  {status === 'all' && 'Alle'}
                  {status === 'active' && 'Actief'}
                  {status === 'pending' && 'In behandeling'}
                  {status === 'completed' && 'Afgerond'}
                  <span className="ml-2 text-xs opacity-70">({statusCounts[status]})</span>
                </Button>
              ))}
              {statusFilter !== 'all' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setStatusFilter('all')}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4 mr-1" />
                  Reset
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Projects */}
      {isLoading ? (
        <div className={cn(
          viewMode === 'grid' ? 'grid gap-4 md:grid-cols-2 lg:grid-cols-3' : 'space-y-3'
        )}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-5 bg-muted rounded w-3/4" />
                <div className="h-4 bg-muted rounded w-1/2 mt-2" />
              </CardHeader>
              <CardContent>
                <div className="h-20 bg-muted rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : enrichedProjects.length === 0 ? (
        <Card className="border-dashed border-2">
          <CardContent className="py-12">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 rounded-full bg-marqed-blue/10 flex items-center justify-center mb-4">
                <FolderKanban className="h-8 w-8 text-marqed-blue" />
              </div>
              <h3 className="text-lg font-semibold">
                {searchQuery || statusFilter !== 'all' ? 'Geen resultaten' : 'Geen projecten'}
              </h3>
              <p className="text-muted-foreground mt-2 max-w-sm mx-auto">
                {searchQuery
                  ? `Geen projecten gevonden voor "${searchQuery}"`
                  : statusFilter !== 'all'
                  ? `Geen projecten met status "${statusFilter === 'active' ? 'actief' : statusFilter === 'pending' ? 'in behandeling' : 'afgerond'}"`
                  : 'Er zijn nog geen projecten voor uw organisatie. Projecten worden aangemaakt via het brownpaper proces.'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : viewMode === 'grid' ? (
        // Grid view
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {enrichedProjects.map((project) => (
            <Link key={project.id} to={`/projects/${project.id}`}>
              <Card className="h-full group hover:border-marqed-blue/30 hover:shadow-lg hover:shadow-marqed-blue/5 transition-all cursor-pointer">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-marqed-blue to-marqed-blue-dark flex items-center justify-center group-hover:shadow-md group-hover:shadow-marqed-blue/20 transition-shadow">
                      <FolderKanban className="h-5 w-5 text-white" />
                    </div>
                    <span
                      className={cn(
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        project.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : project.status === 'pending'
                          ? 'bg-marqed-orange/10 text-marqed-orange'
                          : 'bg-gray-100 text-gray-800'
                      )}
                    >
                      {project.status === 'active'
                        ? 'Actief'
                        : project.status === 'pending'
                        ? 'In behandeling'
                        : 'Afgerond'}
                    </span>
                  </div>
                  <CardTitle className="mt-4 group-hover:text-marqed-blue transition-colors">
                    {project.name}
                  </CardTitle>
                  <CardDescription className="line-clamp-2">
                    {project.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  {/* Quality score */}
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Kwaliteit</span>
                      <span className={cn('font-semibold', getScoreColor(project.quality_score))}>
                        {project.quality_score}%
                      </span>
                    </div>
                    <Progress
                      value={project.quality_score}
                      className="h-1.5"
                      indicatorClassName={getScoreBgColor(project.quality_score)}
                    />
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <FileCode2 className="h-4 w-4" />
                      <span>{formatLinesOfCode(project.lines_of_code)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <GitBranch className="h-4 w-4" />
                      <span>{project.repositories_count}</span>
                    </div>
                    <div className="flex items-center gap-1 ml-auto">
                      <Calendar className="h-4 w-4" />
                      <span>{formatRelativeTime(project.updated_at)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        // List view
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {enrichedProjects.map((project) => (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="flex items-center justify-between p-4 hover:bg-marqed-blue/5 transition-colors group"
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-marqed-blue to-marqed-blue-dark flex items-center justify-center flex-shrink-0 group-hover:shadow-md group-hover:shadow-marqed-blue/20 transition-shadow">
                      <FolderKanban className="h-6 w-6 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <h4 className="font-semibold group-hover:text-marqed-blue transition-colors truncate">
                          {project.name}
                        </h4>
                        <span
                          className={cn(
                            'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0',
                            project.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : project.status === 'pending'
                              ? 'bg-marqed-orange/10 text-marqed-orange'
                              : 'bg-gray-100 text-gray-800'
                          )}
                        >
                          {project.status === 'active'
                            ? 'Actief'
                            : project.status === 'pending'
                            ? 'In behandeling'
                            : 'Afgerond'}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate mt-0.5">
                        {project.description}
                      </p>
                    </div>
                  </div>

                  <div className="hidden md:flex items-center gap-6 mx-4">
                    <div className="text-center">
                      <p className={cn('text-lg font-semibold', getScoreColor(project.quality_score))}>
                        {project.quality_score}%
                      </p>
                      <p className="text-xs text-muted-foreground">Kwaliteit</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold">{formatLinesOfCode(project.lines_of_code)}</p>
                      <p className="text-xs text-muted-foreground">Regels</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-semibold">{project.repositories_count}</p>
                      <p className="text-xs text-muted-foreground">Repos</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right hidden sm:block">
                      <p className="text-sm text-muted-foreground">
                        {formatRelativeTime(project.updated_at)}
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-marqed-blue group-hover:translate-x-1 transition-all" />
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
