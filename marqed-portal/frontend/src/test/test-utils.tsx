import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Refine } from '@refinedev/core'
import routerBindings from '@refinedev/react-router-v6'

// Create a test query client
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })

interface WrapperProps {
  children: React.ReactNode
}

// All providers wrapper for testing
const AllTheProviders = ({ children }: WrapperProps) => {
  const queryClient = createTestQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Refine
          routerProvider={routerBindings}
          options={{
            syncWithLocation: false,
            warnWhenUnsavedChanges: false,
            disableTelemetry: true,
          }}
        >
          {children}
        </Refine>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything from testing-library
export * from '@testing-library/react'
export { customRender as render }

// Helper to wait for async operations
export const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0))

// Mock auth context for testing
export const mockAuthContext = {
  isAuthenticated: true,
  user: {
    id: '1',
    email: 'admin@hci.nl',
    full_name: 'Admin User',
    role: 'ADMIN',
    tenant_id: 'hci',
  },
  login: vi.fn(),
  logout: vi.fn(),
  checkAuth: vi.fn(),
}
