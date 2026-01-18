import { useShow } from '@refinedev/core'
import { useParams, Link } from 'react-router-dom'
import { useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  ArrowLeft,
  FolderKanban,
  Calendar,
  Clock,
  FileCode,
  FileCode2,
  GitBranch,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  Bug,
  AlertCircle,
  Download,
  Settings,
  BarChart3,
  Layers,
  ExternalLink,
  RefreshCw,
  Play,
  History,
  ChevronRight,
} from 'lucide-react'
import { cn, formatDate, formatRelativeTime } from '@/lib/utils'

interface Project {
  id: string
  name: string
  description: string
  status: string
  created_at: string
  updated_at: string
  repositories?: Array<{
    id: string
    name: string
    url: string
    branch: string
    last_analyzed: string
  }>
}

// Mock data for demonstration
const mockQualityData = {
  overallScore: 78,
  previousScore: 74,
  maintainability: 82,
  reliability: 75,
  security: 85,
  technicalDebt: '12d 4h',
  codeSmells: 234,
  bugs: 12,
  vulnerabilities: 3,
  duplications: 8.5,
  coverage: 67,
  linesOfCode: 245000,
}

const mockModules = [
  { name: 'core/services', score: 92, loc: 45000, issues: 12 },
  { name: 'api/controllers', score: 78, loc: 32000, issues: 28 },
  { name: 'data/repositories', score: 85, loc: 28000, issues: 15 },
  { name: 'ui/components', score: 65, loc: 52000, issues: 45 },
  { name: 'utils/helpers', score: 88, loc: 18000, issues: 8 },
  { name: 'legacy/modules', score: 45, loc: 70000, issues: 126 },
]

const mockHistory = [
  { date: '2026-01-14', score: 78, issues: 234 },
  { date: '2026-01-07', score: 76, issues: 248 },
  { date: '2025-12-31', score: 74, issues: 265 },
  { date: '2025-12-24', score: 72, issues: 280 },
  { date: '2025-12-17', score: 70, issues: 295 },
]

const mockReports = [
  { id: '1', name: 'Volledige Code Analyse', date: '2026-01-14', type: 'analysis' },
  { id: '2', name: 'Security Audit Rapport', date: '2026-01-10', type: 'security' },
  { id: '3', name: 'Migratie Roadmap', date: '2026-01-05', type: 'migration' },
  { id: '4', name: 'Technical Debt Overzicht', date: '2025-12-20', type: 'debt' },
]

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

function ScoreRing({ score, size = 100, label, trend }: { score: number; size?: number; label: string; trend?: number }) {
  const strokeWidth = 6
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (score / 100) * circumference

  const getScoreStrokeColor = (s: number) => {
    if (s >= 80) return 'stroke-green-500'
    if (s >= 60) return 'stroke-marqed-orange'
    return 'stroke-red-500'
  }

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle
            className="stroke-muted"
            strokeWidth={strokeWidth}
            fill="transparent"
            r={radius}
            cx={size / 2}
            cy={size / 2}
          />
          <circle
            className={cn('transition-all duration-500', getScoreStrokeColor(score))}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            fill="transparent"
            r={radius}
            cx={size / 2}
            cy={size / 2}
            style={{
              strokeDasharray: circumference,
              strokeDashoffset: offset,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold">{score}</span>
          {trend !== undefined && (
            <span className={cn(
              'text-xs flex items-center',
              trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-muted-foreground'
            )}>
              {trend > 0 ? <TrendingUp className="h-3 w-3 mr-0.5" /> : trend < 0 ? <TrendingDown className="h-3 w-3 mr-0.5" /> : null}
              {trend > 0 ? '+' : ''}{trend}%
            </span>
          )}
        </div>
      </div>
      <span className="text-sm text-muted-foreground mt-2">{label}</span>
    </div>
  )
}

export function ProjectShow() {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState('overview')
  const { queryResult } = useShow<Project>({
    resource: 'projects',
    id,
  })

  const { data, isLoading, isError } = queryResult
  const project = data?.data

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-marqed-blue" />
      </div>
    )
  }

  if (isError || !project) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
          <AlertTriangle className="h-8 w-8 text-red-600" />
        </div>
        <h3 className="text-lg font-semibold">Project niet gevonden</h3>
        <p className="text-muted-foreground mt-2">
          Het gevraagde project bestaat niet of u heeft geen toegang.
        </p>
        <Button asChild className="mt-4 bg-marqed-blue hover:bg-marqed-blue-dark">
          <Link to="/projects">Terug naar projecten</Link>
        </Button>
      </div>
    )
  }

  const scoreTrend = mockQualityData.overallScore - mockQualityData.previousScore

  return (
    <div className="space-y-6">
      {/* Header with gradient */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-marqed-blue-dark via-marqed-blue to-marqed-blue-medium p-6 text-white">
        <div className="absolute inset-0 marqed-circuit-lines opacity-10" />
        <div className="relative z-10">
          <div className="flex items-start gap-4">
            <Button
              variant="ghost"
              size="icon"
              asChild
              className="text-white hover:bg-white/10 -ml-2"
            >
              <Link to="/projects">
                <ArrowLeft className="h-5 w-5" />
              </Link>
            </Button>
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-lg bg-white/10 flex items-center justify-center">
                  <FolderKanban className="h-6 w-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">{project.name}</h1>
                  <p className="text-white/80">{project.description}</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={cn(
                  'inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium',
                  project.status === 'active'
                    ? 'bg-green-500/20 text-green-100 border border-green-400/30'
                    : project.status === 'pending'
                    ? 'bg-orange-500/20 text-orange-100 border border-orange-400/30'
                    : 'bg-gray-500/20 text-gray-100 border border-gray-400/30'
                )}
              >
                {project.status === 'active'
                  ? 'Actief'
                  : project.status === 'pending'
                  ? 'In behandeling'
                  : 'Afgerond'}
              </span>
              <Button className="bg-white/10 hover:bg-white/20 border border-white/20">
                <Play className="h-4 w-4 mr-2" />
                Nieuwe Analyse
              </Button>
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white/70 text-xs">Regels code</p>
              <p className="text-xl font-bold">{formatLinesOfCode(mockQualityData.linesOfCode)}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white/70 text-xs">Kwaliteitsscore</p>
              <p className="text-xl font-bold flex items-center gap-2">
                {mockQualityData.overallScore}%
                {scoreTrend > 0 && <TrendingUp className="h-4 w-4 text-green-400" />}
              </p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white/70 text-xs">Repositories</p>
              <p className="text-xl font-bold">{project.repositories?.length || 0}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white/70 text-xs">Laatste update</p>
              <p className="text-xl font-bold">{formatRelativeTime(project.updated_at)}</p>
            </div>
          </div>
        </div>
        <div className="absolute top-4 right-4 w-32 h-32 rounded-full bg-marqed-orange/20 blur-3xl" />
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-muted/50">
          <TabsTrigger value="overview" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <BarChart3 className="h-4 w-4 mr-2" />
            Overzicht
          </TabsTrigger>
          <TabsTrigger value="modules" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <Layers className="h-4 w-4 mr-2" />
            Modules
          </TabsTrigger>
          <TabsTrigger value="repositories" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <GitBranch className="h-4 w-4 mr-2" />
            Repositories
          </TabsTrigger>
          <TabsTrigger value="reports" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <FileCode className="h-4 w-4 mr-2" />
            Rapporten
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Quality scores */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-marqed-blue" />
                  Code Kwaliteit
                </CardTitle>
                <CardDescription>
                  Huidige kwaliteitsscores en metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-center justify-around gap-6">
                  <ScoreRing
                    score={mockQualityData.overallScore}
                    label="Overall"
                    trend={scoreTrend}
                    size={120}
                  />
                  <ScoreRing score={mockQualityData.maintainability} label="Onderhoud" />
                  <ScoreRing score={mockQualityData.reliability} label="Betrouwbaar" />
                  <ScoreRing score={mockQualityData.security} label="Security" />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 pt-6 border-t">
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <Clock className="h-5 w-5 mx-auto text-marqed-orange mb-1" />
                    <p className="text-lg font-bold text-marqed-orange">{mockQualityData.technicalDebt}</p>
                    <p className="text-xs text-muted-foreground">Tech Debt</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <AlertCircle className="h-5 w-5 mx-auto text-muted-foreground mb-1" />
                    <p className="text-lg font-bold">{mockQualityData.codeSmells}</p>
                    <p className="text-xs text-muted-foreground">Code Smells</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <Bug className="h-5 w-5 mx-auto text-red-500 mb-1" />
                    <p className="text-lg font-bold text-red-500">{mockQualityData.bugs}</p>
                    <p className="text-xs text-muted-foreground">Bugs</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <ShieldCheck className="h-5 w-5 mx-auto text-purple-500 mb-1" />
                    <p className="text-lg font-bold text-purple-500">{mockQualityData.vulnerabilities}</p>
                    <p className="text-xs text-muted-foreground">Kwetsbaarheden</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* History */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5 text-marqed-orange" />
                  Score Historie
                </CardTitle>
                <CardDescription>
                  Ontwikkeling over tijd
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockHistory.map((entry, idx) => (
                    <div key={entry.date} className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50">
                      <div>
                        <p className="text-sm font-medium">{formatDate(entry.date)}</p>
                        <p className="text-xs text-muted-foreground">{entry.issues} issues</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={cn('text-lg font-bold', getScoreColor(entry.score))}>
                          {entry.score}%
                        </span>
                        {idx > 0 && (
                          <span className={cn(
                            'text-xs',
                            entry.score > mockHistory[idx - 1].score ? 'text-red-500' : 'text-green-500'
                          )}>
                            {entry.score > mockHistory[idx - 1].score ? '↓' : '↑'}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Additional metrics */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileCode2 className="h-4 w-4 text-marqed-blue" />
                  Test Coverage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-bold">{mockQualityData.coverage}%</span>
                  <span className="text-sm text-muted-foreground mb-1">van de code</span>
                </div>
                <Progress value={mockQualityData.coverage} className="h-2 mt-2" indicatorClassName="bg-marqed-blue" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="h-4 w-4 text-marqed-orange" />
                  Duplicatie
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-bold">{mockQualityData.duplications}%</span>
                  <span className="text-sm text-muted-foreground mb-1">gedupliceerd</span>
                </div>
                <Progress value={mockQualityData.duplications} className="h-2 mt-2" indicatorClassName="bg-marqed-orange" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  Project Info
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Aangemaakt</span>
                    <span className="font-medium">{formatDate(project.created_at)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Bijgewerkt</span>
                    <span className="font-medium">{formatDate(project.updated_at)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Modules Tab */}
        <TabsContent value="modules" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Code Modules</CardTitle>
                  <CardDescription>
                    Kwaliteitsanalyse per module
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Exporteer
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockModules.map((module) => (
                  <div
                    key={module.name}
                    className="flex items-center justify-between p-4 rounded-lg border hover:border-marqed-blue/30 hover:bg-marqed-blue/5 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center gap-4">
                      <div className={cn(
                        'h-10 w-10 rounded-lg flex items-center justify-center',
                        module.score >= 80 ? 'bg-green-100' : module.score >= 60 ? 'bg-marqed-orange/10' : 'bg-red-100'
                      )}>
                        <Layers className={cn(
                          'h-5 w-5',
                          module.score >= 80 ? 'text-green-600' : module.score >= 60 ? 'text-marqed-orange' : 'text-red-600'
                        )} />
                      </div>
                      <div>
                        <h4 className="font-medium group-hover:text-marqed-blue transition-colors">
                          {module.name}
                        </h4>
                        <p className="text-sm text-muted-foreground">
                          {formatLinesOfCode(module.loc)} regels
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-center">
                        <p className={cn('text-lg font-bold', getScoreColor(module.score))}>
                          {module.score}%
                        </p>
                        <p className="text-xs text-muted-foreground">Score</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold">{module.issues}</p>
                        <p className="text-xs text-muted-foreground">Issues</p>
                      </div>
                      <div className="w-24">
                        <Progress
                          value={module.score}
                          className="h-2"
                          indicatorClassName={getScoreBgColor(module.score)}
                        />
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-marqed-blue group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Repositories Tab */}
        <TabsContent value="repositories" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Code Repositories</CardTitle>
                  <CardDescription>
                    Gekoppelde code repositories voor analyse
                  </CardDescription>
                </div>
                <Button className="bg-marqed-blue hover:bg-marqed-blue-dark">
                  <GitBranch className="h-4 w-4 mr-2" />
                  Repository Toevoegen
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {!project.repositories || project.repositories.length === 0 ? (
                <div className="text-center py-12 border-2 border-dashed rounded-lg">
                  <div className="mx-auto w-16 h-16 rounded-full bg-marqed-blue/10 flex items-center justify-center mb-4">
                    <GitBranch className="h-8 w-8 text-marqed-blue" />
                  </div>
                  <h3 className="text-lg font-semibold">
                    Geen repositories gekoppeld
                  </h3>
                  <p className="text-muted-foreground mt-2 max-w-sm mx-auto">
                    Koppel een code repository om te beginnen met analyseren.
                  </p>
                  <Button className="mt-4 bg-marqed-blue hover:bg-marqed-blue-dark">
                    <GitBranch className="h-4 w-4 mr-2" />
                    Repository Toevoegen
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {project.repositories.map((repo) => (
                    <div
                      key={repo.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:border-marqed-blue/30 hover:bg-marqed-blue/5 transition-all group"
                    >
                      <div className="flex items-center gap-4">
                        <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-marqed-blue to-marqed-blue-dark flex items-center justify-center">
                          <GitBranch className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <h4 className="font-medium group-hover:text-marqed-blue transition-colors">
                            {repo.name}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            Branch: {repo.branch}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Laatste analyse</p>
                          <p className="text-sm font-medium">
                            {repo.last_analyzed
                              ? formatRelativeTime(repo.last_analyzed)
                              : 'Nog niet geanalyseerd'}
                          </p>
                        </div>
                        <Button variant="outline" size="sm">
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Analyseer
                        </Button>
                        <Button variant="ghost" size="icon">
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Rapporten</CardTitle>
                  <CardDescription>
                    Gegenereerde analyse rapporten
                  </CardDescription>
                </div>
                <Button className="bg-marqed-blue hover:bg-marqed-blue-dark">
                  <FileCode className="h-4 w-4 mr-2" />
                  Nieuw Rapport
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockReports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 rounded-lg border hover:border-marqed-blue/30 hover:bg-marqed-blue/5 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center gap-4">
                      <div className={cn(
                        'h-10 w-10 rounded-lg flex items-center justify-center',
                        report.type === 'analysis' ? 'bg-marqed-blue/10' :
                        report.type === 'security' ? 'bg-purple-100' :
                        report.type === 'migration' ? 'bg-green-100' :
                        'bg-marqed-orange/10'
                      )}>
                        <FileCode className={cn(
                          'h-5 w-5',
                          report.type === 'analysis' ? 'text-marqed-blue' :
                          report.type === 'security' ? 'text-purple-600' :
                          report.type === 'migration' ? 'text-green-600' :
                          'text-marqed-orange'
                        )} />
                      </div>
                      <div>
                        <h4 className="font-medium group-hover:text-marqed-blue transition-colors">
                          {report.name}
                        </h4>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(report.date)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-marqed-blue group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
