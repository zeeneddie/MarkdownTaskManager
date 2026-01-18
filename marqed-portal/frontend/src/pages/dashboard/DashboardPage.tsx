import { useList, useGetIdentity } from '@refinedev/core'
import { Link } from 'react-router-dom'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  FolderKanban,
  TrendingUp,
  Clock,
  CheckCircle2,
  ArrowRight,
  AlertCircle,
  FileCode2,
  ShieldCheck,
  Zap,
  Activity,
  Bug,
  RefreshCw,
  FileSearch,
  BarChart3,
  Calendar,
  ChevronRight,
} from 'lucide-react'
import { cn, formatRelativeTime } from '@/lib/utils'

interface Project {
  id: string
  name: string
  description: string
  status: string
  updated_at: string
}

// Mock data for code quality metrics
const codeQualityMetrics = {
  overallScore: 78,
  maintainability: 82,
  reliability: 75,
  security: 85,
  technicalDebt: '12d 4h',
  codeSmells: 234,
  bugs: 12,
  vulnerabilities: 3,
}

// Mock data for recent activity
const recentActivity = [
  {
    id: 1,
    type: 'analysis',
    project: 'HCI-CRS Migration',
    message: 'Code analyse voltooid',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    icon: FileSearch,
    color: 'text-marqed-blue',
  },
  {
    id: 2,
    type: 'finding',
    project: 'Legacy ERP System',
    message: '5 nieuwe bevindingen',
    timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    icon: Bug,
    color: 'text-marqed-orange',
  },
  {
    id: 3,
    type: 'update',
    project: 'Mainframe Modernisatie',
    message: 'Migratie rapport bijgewerkt',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    icon: RefreshCw,
    color: 'text-green-600',
  },
  {
    id: 4,
    type: 'milestone',
    project: 'HCI-CRS Migration',
    message: 'Fase 2 afgerond',
    timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    icon: CheckCircle2,
    color: 'text-purple-600',
  },
]

function ScoreRing({ score, size = 120, label }: { score: number; size?: number; label: string }) {
  const strokeWidth = 8
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (score / 100) * circumference

  const getScoreColor = (s: number) => {
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
            className={cn('transition-all duration-500', getScoreColor(score))}
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
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-3xl font-bold">{score}</span>
        </div>
      </div>
      <span className="text-sm text-muted-foreground mt-2">{label}</span>
    </div>
  )
}

function MetricBar({ label, value, max = 100, color }: { label: string; value: number; max?: number; color: string }) {
  const percentage = Math.min((value / max) * 100, 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{value}%</span>
      </div>
      <Progress value={percentage} className="h-2" indicatorClassName={color} />
    </div>
  )
}

export function DashboardPage() {
  const { data: user } = useGetIdentity<{
    full_name: string
    role: string
    tenant_id: string
  }>()

  const { data: projectsData, isLoading } = useList<Project>({
    resource: 'projects',
    pagination: { current: 1, pageSize: 5 },
    sorters: [{ field: 'updated_at', order: 'desc' }],
  })

  const projects = projectsData?.data || []
  const totalProjects = projectsData?.total || 0

  const stats = [
    {
      title: 'Totaal Projecten',
      value: totalProjects,
      icon: FolderKanban,
      color: 'text-marqed-blue',
      bgColor: 'bg-marqed-blue/10',
      borderColor: 'border-marqed-blue/20',
    },
    {
      title: 'Actieve Analyses',
      value: projects.filter((p) => p.status === 'active').length,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      borderColor: 'border-green-200',
    },
    {
      title: 'In Behandeling',
      value: projects.filter((p) => p.status === 'pending').length,
      icon: Clock,
      color: 'text-marqed-orange',
      bgColor: 'bg-marqed-orange/10',
      borderColor: 'border-marqed-orange/20',
    },
    {
      title: 'Afgerond',
      value: projects.filter((p) => p.status === 'completed').length,
      icon: CheckCircle2,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      borderColor: 'border-purple-200',
    },
  ]

  const quickActions = [
    { label: 'Nieuwe Analyse', icon: FileSearch, href: '/projects/new' },
    { label: 'Rapporten', icon: BarChart3, href: '/reports' },
    { label: 'Planning', icon: Calendar, href: '/planning' },
  ]

  return (
    <div className="space-y-8">
      {/* Welcome header with gradient */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-marqed-blue-dark via-marqed-blue to-marqed-blue-medium p-6 text-white">
        <div className="absolute inset-0 marqed-circuit-lines opacity-10" />
        <div className="relative z-10">
          <h1 className="text-2xl font-bold">
            Welkom terug, {user?.full_name?.split(' ')[0] || 'Gebruiker'}
          </h1>
          <p className="text-white/80 mt-1">
            Hier is een overzicht van uw legacy modernisatie projecten
          </p>

          {/* Quick actions */}
          <div className="flex flex-wrap gap-3 mt-4">
            {quickActions.map((action) => (
              <Link key={action.label} to={action.href}>
                <Button
                  variant="secondary"
                  className="bg-white/10 hover:bg-white/20 text-white border-white/20"
                >
                  <action.icon className="h-4 w-4 mr-2" />
                  {action.label}
                </Button>
              </Link>
            ))}
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-4 right-4 w-20 h-20 rounded-full bg-marqed-orange/20 blur-2xl" />
        <div className="absolute bottom-4 right-20 w-32 h-32 rounded-full bg-white/10 blur-3xl" />
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title} className={cn('border', stat.borderColor)}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className={cn('p-2 rounded-lg', stat.bgColor)}>
                <stat.icon className={cn('h-4 w-4', stat.color)} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Code Quality Overview - takes 2 columns */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-marqed-blue" />
                  Code Kwaliteit Overzicht
                </CardTitle>
                <CardDescription>
                  Gemiddelde scores over alle actieve projecten
                </CardDescription>
              </div>
              <Button variant="outline" size="sm">
                Details
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row gap-8">
              {/* Main score ring */}
              <div className="flex justify-center">
                <ScoreRing score={codeQualityMetrics.overallScore} label="Overall Score" />
              </div>

              {/* Metric bars */}
              <div className="flex-1 space-y-4">
                <MetricBar
                  label="Onderhoudbaarheid"
                  value={codeQualityMetrics.maintainability}
                  color="bg-marqed-blue"
                />
                <MetricBar
                  label="Betrouwbaarheid"
                  value={codeQualityMetrics.reliability}
                  color="bg-green-500"
                />
                <MetricBar
                  label="Beveiliging"
                  value={codeQualityMetrics.security}
                  color="bg-purple-500"
                />
              </div>
            </div>

            {/* Bottom stats */}
            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t">
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 text-muted-foreground mb-1">
                  <Clock className="h-4 w-4" />
                  <span className="text-xs">Tech Debt</span>
                </div>
                <span className="text-lg font-semibold text-marqed-orange">
                  {codeQualityMetrics.technicalDebt}
                </span>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 text-muted-foreground mb-1">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-xs">Code Smells</span>
                </div>
                <span className="text-lg font-semibold">
                  {codeQualityMetrics.codeSmells}
                </span>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 text-muted-foreground mb-1">
                  <Bug className="h-4 w-4" />
                  <span className="text-xs">Bugs</span>
                </div>
                <span className="text-lg font-semibold text-red-500">
                  {codeQualityMetrics.bugs}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-marqed-orange" />
              Recente Activiteit
            </CardTitle>
            <CardDescription>
              Laatste updates van uw projecten
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className={cn('p-2 rounded-lg bg-muted', activity.color)}>
                    <activity.icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {activity.project}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {activity.message}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatRelativeTime(activity.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent projects */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FolderKanban className="h-5 w-5 text-marqed-blue" />
              Recente Projecten
            </CardTitle>
            <CardDescription>
              Uw meest recent bijgewerkte projecten
            </CardDescription>
          </div>
          <Button variant="outline" asChild>
            <Link to="/projects">
              Alle projecten
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 bg-muted animate-pulse rounded-lg"
                />
              ))}
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-8">
              <div className="mx-auto w-16 h-16 rounded-full bg-marqed-blue/10 flex items-center justify-center mb-4">
                <FolderKanban className="h-8 w-8 text-marqed-blue" />
              </div>
              <h3 className="text-lg font-semibold">Geen projecten</h3>
              <p className="text-muted-foreground mt-2 mb-4">
                Er zijn nog geen projecten voor uw organisatie.
              </p>
              <Button className="bg-marqed-blue hover:bg-marqed-blue-dark">
                <FileCode2 className="h-4 w-4 mr-2" />
                Start nieuw project
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {projects.map((project) => (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="flex items-center justify-between p-4 rounded-lg border border-transparent hover:border-marqed-blue/20 hover:bg-marqed-blue/5 transition-all group"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-marqed-blue to-marqed-blue-dark flex items-center justify-center group-hover:shadow-md group-hover:shadow-marqed-blue/20 transition-shadow">
                      <FolderKanban className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium group-hover:text-marqed-blue transition-colors">
                        {project.name}
                      </h4>
                      <p className="text-sm text-muted-foreground line-clamp-1">
                        {project.description}
                      </p>
                    </div>
                  </div>
                  <div className="text-right flex items-center gap-4">
                    <div>
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
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatRelativeTime(project.updated_at)}
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-marqed-blue group-hover:translate-x-1 transition-all" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
