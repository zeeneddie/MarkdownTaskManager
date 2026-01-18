import { ReactNode, useState } from 'react'
import { useGetIdentity, useLogout } from '@refinedev/core'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Bell,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface LayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Projecten', href: '/projects', icon: FolderKanban },
  { name: 'Rapporten', href: '/reports', icon: FileText },
  { name: 'Instellingen', href: '/settings', icon: Settings },
]

export function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const { data: user } = useGetIdentity<{
    id: string
    email: string
    full_name: string
    role: string
    tenant_id: string
  }>()
  const { mutate: logout } = useLogout()

  return (
    <div className="min-h-screen bg-background marqed-watermark">
      {/* Subtle background pattern */}
      <div className="fixed inset-0 marqed-bg-subtle pointer-events-none" />

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-card/95 backdrop-blur-sm border-r border-marqed-blue-light/20 transition-transform duration-200 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-marqed-blue-light/20">
          <Link to="/" className="flex items-center gap-3">
            <img
              src="/marqed-icon.svg"
              alt="arQed.ai"
              className="h-8 w-auto"
              onError={(e) => {
                // Fallback to gradient box if image not found
                const target = e.currentTarget
                target.style.display = 'none'
                const fallback = target.nextElementSibling as HTMLElement
                if (fallback) fallback.style.display = 'flex'
              }}
            />
            {/* Fallback logo */}
            <div
              className="h-8 w-8 rounded-lg marqed-gradient items-center justify-center hidden"
              style={{ display: 'none' }}
            >
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-base marqed-headline">arQed<span className="text-marqed-orange">.ai</span></span>
              <span className="text-[10px] text-muted-foreground -mt-0.5">Client Portal</span>
            </div>
          </Link>
          <button
            className="lg:hidden p-2 hover:bg-marqed-blue-light/10 rounded-md transition-colors"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5 text-marqed-blue" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navigation.map((item) => {
            const isActive =
              item.href === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.href)
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-marqed-blue text-white shadow-md shadow-marqed-blue/25'
                    : 'text-muted-foreground hover:bg-marqed-blue-light/10 hover:text-marqed-blue'
                )}
              >
                <item.icon className={cn('h-5 w-5', isActive && 'text-white')} />
                {item.name}
                {isActive && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-marqed-orange" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Decorative circuit element */}
        <div className="px-4 py-3">
          <div className="h-px bg-gradient-to-r from-transparent via-marqed-blue-light/30 to-transparent" />
        </div>

        {/* User info at bottom */}
        <div className="p-4">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-marqed-blue-light/5 border border-marqed-blue-light/10">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-marqed-blue to-marqed-blue-dark flex items-center justify-center">
              <span className="text-sm font-bold text-white">
                {user?.full_name?.charAt(0) || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate text-foreground">
                {user?.full_name || 'Gebruiker'}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.email}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => logout()}
              title="Uitloggen"
              className="hover:bg-marqed-orange/10 hover:text-marqed-orange"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64 relative z-10">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 bg-background/80 backdrop-blur-md border-b border-marqed-blue-light/20 flex items-center px-4 gap-4">
          <button
            className="lg:hidden p-2 hover:bg-marqed-blue-light/10 rounded-md transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5 text-marqed-blue" />
          </button>

          <div className="flex-1" />

          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className="relative hover:bg-marqed-blue-light/10"
          >
            <Bell className="h-5 w-5 text-muted-foreground" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-marqed-orange rounded-full" />
          </Button>

          {/* Tenant indicator */}
          {user?.tenant_id && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-marqed-blue-light/10 rounded-full border border-marqed-blue-light/20">
              <div className="w-2 h-2 rounded-full bg-marqed-orange" />
              <span className="text-xs font-semibold text-marqed-blue-dark">
                {user.tenant_id.toUpperCase()}
              </span>
              <ChevronDown className="h-3 w-3 text-marqed-blue" />
            </div>
          )}
        </header>

        {/* Page content */}
        <main className="p-6 relative">
          {/* Circuit pattern background for main content */}
          <div className="marqed-circuit-bg">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
