import { Refine } from '@refinedev/core'
import routerBindings, {
  NavigateToResource,
  UnsavedChangesNotifier,
} from '@refinedev/react-router-v6'
import { Routes, Route, Outlet } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { dataProvider } from './providers/data-provider'
import { authProvider } from './providers/auth-provider'
import { Layout } from './components/layout/Layout'
import { LoginPage } from './pages/auth/LoginPage'
import { DashboardPage } from './pages/dashboard/DashboardPage'
import { ProjectList } from './pages/projects/ProjectList'
import { ProjectShow } from './pages/projects/ProjectShow'
import { SettingsPage } from './pages/settings/SettingsPage'
import { ReportsPage } from './pages/reports/ReportsPage'
import { Toaster } from './components/ui/toaster'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Refine
        routerProvider={routerBindings}
        dataProvider={dataProvider}
        authProvider={authProvider}
        resources={[
          {
            name: 'dashboard',
            list: '/',
          },
          {
            name: 'projects',
            list: '/projects',
            show: '/projects/:id',
            meta: {
              label: 'Projecten',
              icon: 'folder',
            },
          },
        ]}
        options={{
          syncWithLocation: true,
          warnWhenUnsavedChanges: true,
          disableTelemetry: true,
        }}
      >
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <Layout>
                <Outlet />
              </Layout>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="/projects">
              <Route index element={<ProjectList />} />
              <Route path=":id" element={<ProjectShow />} />
            </Route>
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Route>
          <Route path="*" element={<NavigateToResource resource="dashboard" />} />
        </Routes>
        <Toaster />
        <UnsavedChangesNotifier />
      </Refine>
    </QueryClientProvider>
  )
}

export default App
