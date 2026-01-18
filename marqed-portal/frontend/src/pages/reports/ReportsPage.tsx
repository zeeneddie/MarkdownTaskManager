import { useState } from 'react'
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
  FileText,
  Search,
  Filter,
  Download,
  Calendar,
  FolderKanban,
  Shield,
  TrendingUp,
  Clock,
  FileCode,
  BarChart3,
  Eye,
  ChevronRight,
  X,
  FileSpreadsheet,
  FileJson,
  Printer,
  Share2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import { cn, formatDate } from '@/lib/utils'

type ReportType = 'all' | 'analysis' | 'security' | 'migration' | 'debt' | 'quality'
type ReportStatus = 'all' | 'completed' | 'generating' | 'scheduled'

interface Report {
  id: string
  name: string
  type: ReportType
  status: 'completed' | 'generating' | 'scheduled'
  project: string
  projectId: string
  createdAt: string
  size?: string
  pages?: number
  findings?: number
}

// Mock reports data
const mockReports: Report[] = [
  {
    id: '1',
    name: 'Volledige Code Analyse Q1 2026',
    type: 'analysis',
    status: 'completed',
    project: 'HCI-CRS Migration',
    projectId: '1',
    createdAt: '2026-01-14',
    size: '2.4 MB',
    pages: 45,
    findings: 234,
  },
  {
    id: '2',
    name: 'Security Audit Rapport',
    type: 'security',
    status: 'completed',
    project: 'HCI-CRS Migration',
    projectId: '1',
    createdAt: '2026-01-10',
    size: '1.8 MB',
    pages: 28,
    findings: 12,
  },
  {
    id: '3',
    name: 'Migratie Roadmap 2026',
    type: 'migration',
    status: 'completed',
    project: 'Legacy ERP System',
    projectId: '2',
    createdAt: '2026-01-08',
    size: '3.2 MB',
    pages: 62,
  },
  {
    id: '4',
    name: 'Technical Debt Overzicht',
    type: 'debt',
    status: 'completed',
    project: 'Mainframe Modernisatie',
    projectId: '3',
    createdAt: '2026-01-05',
    size: '1.1 MB',
    pages: 18,
    findings: 89,
  },
  {
    id: '5',
    name: 'Code Quality Trend Analyse',
    type: 'quality',
    status: 'generating',
    project: 'HCI-CRS Migration',
    projectId: '1',
    createdAt: '2026-01-15',
  },
  {
    id: '6',
    name: 'Maandelijkse Security Scan',
    type: 'security',
    status: 'scheduled',
    project: 'Legacy ERP System',
    projectId: '2',
    createdAt: '2026-01-20',
  },
  {
    id: '7',
    name: 'Dependency Analyse',
    type: 'analysis',
    status: 'completed',
    project: 'Mainframe Modernisatie',
    projectId: '3',
    createdAt: '2025-12-28',
    size: '0.9 MB',
    pages: 15,
    findings: 45,
  },
  {
    id: '8',
    name: 'Legacy Code Assessment',
    type: 'debt',
    status: 'completed',
    project: 'Legacy ERP System',
    projectId: '2',
    createdAt: '2025-12-20',
    size: '4.5 MB',
    pages: 78,
    findings: 312,
  },
]

const reportTypeConfig: Record<string, { label: string; icon: typeof FileText; color: string; bg: string }> = {
  analysis: { label: 'Code Analyse', icon: BarChart3, color: 'text-marqed-blue', bg: 'bg-marqed-blue/10' },
  security: { label: 'Security', icon: Shield, color: 'text-purple-600', bg: 'bg-purple-100' },
  migration: { label: 'Migratie', icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-100' },
  debt: { label: 'Tech Debt', icon: Clock, color: 'text-marqed-orange', bg: 'bg-marqed-orange/10' },
  quality: { label: 'Kwaliteit', icon: CheckCircle2, color: 'text-cyan-600', bg: 'bg-cyan-100' },
}

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  completed: { label: 'Voltooid', color: 'text-green-700', bg: 'bg-green-100' },
  generating: { label: 'Genereren...', color: 'text-marqed-blue', bg: 'bg-marqed-blue/10' },
  scheduled: { label: 'Gepland', color: 'text-muted-foreground', bg: 'bg-muted' },
}

export function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<ReportType>('all')
  const [statusFilter, setStatusFilter] = useState<ReportStatus>('all')
  const [showFilters, setShowFilters] = useState(false)

  // Filter reports
  const filteredReports = mockReports.filter((report) => {
    const matchesSearch = report.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      report.project.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = typeFilter === 'all' || report.type === typeFilter
    const matchesStatus = statusFilter === 'all' || report.status === statusFilter
    return matchesSearch && matchesType && matchesStatus
  })

  // Count by type
  const typeCounts = {
    all: mockReports.length,
    analysis: mockReports.filter((r) => r.type === 'analysis').length,
    security: mockReports.filter((r) => r.type === 'security').length,
    migration: mockReports.filter((r) => r.type === 'migration').length,
    debt: mockReports.filter((r) => r.type === 'debt').length,
    quality: mockReports.filter((r) => r.type === 'quality').length,
  }

  const completedReports = mockReports.filter((r) => r.status === 'completed').length
  const generatingReports = mockReports.filter((r) => r.status === 'generating').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-marqed-blue-dark via-marqed-blue to-marqed-blue-medium p-6 text-white">
        <div className="absolute inset-0 marqed-circuit-lines opacity-10" />
        <div className="relative z-10">
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <FileText className="h-7 w-7" />
            Rapporten
          </h1>
          <p className="text-white/80 mt-1">
            Bekijk en download analyse rapporten van al uw projecten
          </p>

          {/* Quick stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white/70 text-xs">Totaal rapporten</p>
              <p className="text-xl font-bold">{mockReports.length}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white/70 text-xs">Voltooid</p>
              <p className="text-xl font-bold">{completedReports}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white/70 text-xs">In verwerking</p>
              <p className="text-xl font-bold flex items-center gap-2">
                {generatingReports}
                {generatingReports > 0 && <RefreshCw className="h-4 w-4 animate-spin" />}
              </p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white/70 text-xs">Deze maand</p>
              <p className="text-xl font-bold">
                {mockReports.filter((r) => r.createdAt.startsWith('2026-01')).length}
              </p>
            </div>
          </div>
        </div>
        <div className="absolute top-4 right-4 w-20 h-20 rounded-full bg-marqed-orange/20 blur-2xl" />
      </div>

      {/* Report type cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {Object.entries(reportTypeConfig).map(([type, config]) => (
          <Card
            key={type}
            className={cn(
              'cursor-pointer transition-all hover:shadow-md',
              typeFilter === type && 'ring-2 ring-marqed-blue'
            )}
            onClick={() => setTypeFilter(typeFilter === type ? 'all' : type as ReportType)}
          >
            <CardContent className="p-4 flex items-center gap-3">
              <div className={cn('p-2 rounded-lg', config.bg)}>
                <config.icon className={cn('h-5 w-5', config.color)} />
              </div>
              <div>
                <p className="text-lg font-bold">{typeCounts[type as ReportType]}</p>
                <p className="text-xs text-muted-foreground">{config.label}</p>
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
                placeholder="Zoek rapporten..."
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
                {(typeFilter !== 'all' || statusFilter !== 'all') && (
                  <span className="ml-2 px-1.5 py-0.5 bg-marqed-orange text-white text-xs rounded-full">
                    {(typeFilter !== 'all' ? 1 : 0) + (statusFilter !== 'all' ? 1 : 0)}
                  </span>
                )}
              </Button>
            </div>
          </div>

          {/* Filter panel */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-muted-foreground mr-2">Status:</span>
                {(['all', 'completed', 'generating', 'scheduled'] as ReportStatus[]).map((status) => (
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
                    {status === 'completed' && 'Voltooid'}
                    {status === 'generating' && 'In verwerking'}
                    {status === 'scheduled' && 'Gepland'}
                  </Button>
                ))}
              </div>

              {(typeFilter !== 'all' || statusFilter !== 'all') && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setTypeFilter('all')
                    setStatusFilter('all')
                  }}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4 mr-1" />
                  Filters wissen
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reports list */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Alle Rapporten</CardTitle>
              <CardDescription>
                {filteredReports.length} {filteredReports.length === 1 ? 'rapport' : 'rapporten'} gevonden
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredReports.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed rounded-lg">
              <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                <FileText className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold">Geen rapporten gevonden</h3>
              <p className="text-muted-foreground mt-2 max-w-sm mx-auto">
                {searchQuery || typeFilter !== 'all' || statusFilter !== 'all'
                  ? 'Probeer andere zoek- of filteropties.'
                  : 'Er zijn nog geen rapporten beschikbaar.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredReports.map((report) => {
                const typeConfig = reportTypeConfig[report.type]
                const status = statusConfig[report.status]

                return (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 rounded-lg border hover:border-marqed-blue/30 hover:bg-marqed-blue/5 transition-all group"
                  >
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      <div className={cn('h-12 w-12 rounded-lg flex items-center justify-center', typeConfig.bg)}>
                        <typeConfig.icon className={cn('h-6 w-6', typeConfig.color)} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                          <h4 className="font-medium group-hover:text-marqed-blue transition-colors truncate">
                            {report.name}
                          </h4>
                          <span className={cn(
                            'px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0',
                            status.bg, status.color
                          )}>
                            {report.status === 'generating' && (
                              <RefreshCw className="h-3 w-3 inline mr-1 animate-spin" />
                            )}
                            {status.label}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                          <Link
                            to={`/projects/${report.projectId}`}
                            className="flex items-center gap-1 hover:text-marqed-blue"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <FolderKanban className="h-3.5 w-3.5" />
                            {report.project}
                          </Link>
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3.5 w-3.5" />
                            {formatDate(report.createdAt)}
                          </span>
                          {report.pages && (
                            <span>{report.pages} pagina's</span>
                          )}
                          {report.findings !== undefined && (
                            <span className="flex items-center gap-1">
                              <AlertTriangle className="h-3.5 w-3.5" />
                              {report.findings} bevindingen
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {report.status === 'completed' && (
                        <>
                          <div className="hidden md:block text-right mr-4">
                            <p className="text-sm font-medium">{report.size}</p>
                            <p className="text-xs text-muted-foreground">PDF</p>
                          </div>
                          <Button variant="outline" size="sm" className="hidden sm:flex">
                            <Eye className="h-4 w-4 mr-2" />
                            Bekijken
                          </Button>
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 sm:mr-2" />
                            <span className="hidden sm:inline">Download</span>
                          </Button>
                        </>
                      )}
                      {report.status === 'generating' && (
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <div className="w-24">
                            <Progress value={65} className="h-1.5" indicatorClassName="bg-marqed-blue" />
                          </div>
                          <span>65%</span>
                        </div>
                      )}
                      {report.status === 'scheduled' && (
                        <span className="text-sm text-muted-foreground">
                          Gepland voor {formatDate(report.createdAt)}
                        </span>
                      )}
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-marqed-blue group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Export options */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5 text-marqed-orange" />
            Bulk Acties
          </CardTitle>
          <CardDescription>
            Exporteer of deel meerdere rapporten tegelijk
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline">
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Exporteer als Excel
            </Button>
            <Button variant="outline">
              <FileJson className="h-4 w-4 mr-2" />
              Exporteer als JSON
            </Button>
            <Button variant="outline">
              <Printer className="h-4 w-4 mr-2" />
              Afdrukken
            </Button>
            <Button variant="outline">
              <Share2 className="h-4 w-4 mr-2" />
              Delen via e-mail
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
