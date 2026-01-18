import { test as base, expect } from '@playwright/test'

// Extend base test with authentication fixture
export const test = base.extend<{ authenticatedPage: void }>({
  authenticatedPage: async ({ page }, use) => {
    // Mock de login API
    await page.route('**/api/auth/login', async (route) => {
      const request = route.request()
      const body = request.postDataJSON()

      if (body?.email === 'admin@hci.nl' && body?.password === 'password123') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'mock-token',
            refresh_token: 'mock-refresh',
            token_type: 'bearer',
            user: {
              id: '1',
              email: 'admin@hci.nl',
              full_name: 'Admin User',
              role: 'ADMIN',
              tenant_id: 'hci',
            },
          }),
        })
      } else {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Invalid credentials' }),
        })
      }
    })

    // Mock de /me endpoint
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '1',
          email: 'admin@hci.nl',
          full_name: 'Admin User',
          role: 'ADMIN',
          tenant_id: 'hci',
        }),
      })
    })

    // Mock projects API
    await page.route('**/api/projects**', async (route) => {
      const url = route.request().url()

      if (url.includes('/api/projects/')) {
        // Single project
        const projectId = url.split('/').pop()?.split('?')[0]
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: projectId || '1',
            name: 'HCI Legacy Migration',
            description: 'Migrating legacy COBOL systems to modern Java stack',
            status: 'active',
            tenant_id: 'hci',
            quality_score: 78,
            created_at: '2024-01-15T10:00:00Z',
            updated_at: '2024-01-20T14:30:00Z',
          }),
        })
      } else {
        // Project list
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [
              {
                id: '1',
                name: 'HCI Legacy Migration',
                description: 'Migrating legacy COBOL systems',
                status: 'active',
                tenant_id: 'hci',
                quality_score: 78,
                created_at: '2024-01-15T10:00:00Z',
                updated_at: '2024-01-20T14:30:00Z',
              },
              {
                id: '2',
                name: 'CRS Modernization',
                description: 'Customer relationship system upgrade',
                status: 'active',
                tenant_id: 'hci',
                quality_score: 85,
                created_at: '2024-02-01T09:00:00Z',
                updated_at: '2024-02-15T11:00:00Z',
              },
            ],
            total: 2,
            page: 1,
            pageSize: 10,
          }),
        })
      }
    })

    // Mock reports API
    await page.route('**/api/reports**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            {
              id: '1',
              title: 'Security Analysis Report',
              type: 'security',
              status: 'completed',
              project_id: '1',
              project_name: 'HCI Legacy Migration',
              created_at: '2024-01-20T10:00:00Z',
            },
            {
              id: '2',
              title: 'Code Quality Report',
              type: 'quality',
              status: 'completed',
              project_id: '1',
              project_name: 'HCI Legacy Migration',
              created_at: '2024-01-19T14:00:00Z',
            },
          ],
          total: 2,
          page: 1,
          pageSize: 10,
        }),
      })
    })

    // Login
    await page.goto('/login')
    await page.getByLabel('E-mailadres').fill('admin@hci.nl')
    await page.getByLabel('Wachtwoord').fill('password123')
    await page.getByRole('button', { name: 'Inloggen', exact: true }).click()

    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/', { timeout: 10000 })

    // Use the authenticated page
    await use()
  },
})

export { expect }
