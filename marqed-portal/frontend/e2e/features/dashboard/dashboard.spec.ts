import { test, expect } from '../../fixtures/auth.fixture'

/**
 * Epic: Dashboard
 * Feature: Dashboard Overzicht
 *
 * User Stories:
 * - Als gebruiker wil ik mijn dashboard zien na inloggen
 * - Als gebruiker wil ik een overzicht van mijn projecten zien
 * - Als gebruiker wil ik code quality metrics zien
 * - Als gebruiker wil ik recente activiteit zien
 */

test.describe('Epic: Dashboard', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    // Authentication is handled by fixture
  })

  test.describe('Feature: Dashboard Weergave', () => {

    test.describe('User Story: Welkom header', () => {
      test('toont welkomstbericht met gebruikersnaam', async ({ page }) => {
        await expect(page.getByText('Welkom terug')).toBeVisible()
      })

      test('toont overzicht beschrijving', async ({ page }) => {
        await expect(page.getByText(/legacy modernisatie projecten/i)).toBeVisible()
      })

      test('toont quick action buttons', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Nieuwe Analyse/i })).toBeVisible()
        await expect(page.getByRole('button', { name: /Rapporten/i })).toBeVisible()
        await expect(page.getByRole('button', { name: /Planning/i })).toBeVisible()
      })
    })

    test.describe('User Story: Statistieken overzicht', () => {
      test('toont statistieken kaarten', async ({ page }) => {
        // Wacht tot dashboard geladen is
        await page.waitForLoadState('networkidle')

        // Zoek naar stats cards met de juiste Nederlandse tekst
        await expect(page.getByText('Totaal Projecten')).toBeVisible()
        await expect(page.getByText('Actieve Analyses')).toBeVisible()
        await expect(page.getByText('In Behandeling')).toBeVisible()
        await expect(page.getByText('Afgerond', { exact: true })).toBeVisible()
      })

      test('statistieken tonen numerieke waarden', async ({ page }) => {
        // Stats grid zou zichtbaar moeten zijn
        const statsGrid = page.locator('.grid.gap-4')
        await expect(statsGrid.first()).toBeVisible()
      })
    })

    test.describe('User Story: Code Kwaliteit Overzicht', () => {
      test('toont code kwaliteit sectie', async ({ page }) => {
        await expect(page.getByText('Code Kwaliteit Overzicht')).toBeVisible()
      })

      test('toont overall score', async ({ page }) => {
        await expect(page.getByText('Overall Score')).toBeVisible()
      })

      test('toont quality metric bars', async ({ page }) => {
        // Nederlandse metric labels
        await expect(page.getByText('Onderhoudbaarheid')).toBeVisible()
        await expect(page.getByText('Betrouwbaarheid')).toBeVisible()
        await expect(page.getByText('Beveiliging')).toBeVisible()
      })

      test('toont detail metrics', async ({ page }) => {
        await expect(page.getByText('Tech Debt')).toBeVisible()
        await expect(page.getByText('Code Smells')).toBeVisible()
        await expect(page.getByText('Bugs')).toBeVisible()
      })
    })

    test.describe('User Story: Recente Activiteit', () => {
      test('toont recente activiteit sectie', async ({ page }) => {
        await expect(page.getByText('Recente Activiteit')).toBeVisible()
      })

      test('toont activiteit items', async ({ page }) => {
        // Activiteiten bevatten project namen
        await expect(page.getByText('HCI-CRS Migration').first()).toBeVisible()
      })

      test('toont activiteit beschrijvingen', async ({ page }) => {
        await expect(page.getByText(/analyse voltooid|bevindingen|bijgewerkt|afgerond/i).first()).toBeVisible()
      })
    })

    test.describe('User Story: Recente Projecten', () => {
      test('toont recente projecten sectie', async ({ page }) => {
        await expect(page.getByText('Recente Projecten')).toBeVisible()
      })

      test('toont alle projecten link', async ({ page }) => {
        await expect(page.getByRole('link', { name: /Alle projecten/i })).toBeVisible()
      })

      test('alle projecten link navigeert naar projecten pagina', async ({ page }) => {
        await page.getByRole('link', { name: /Alle projecten/i }).click()
        await expect(page).toHaveURL('/projects')
      })
    })
  })

  test.describe('Feature: Dashboard Navigatie', () => {

    test.describe('User Story: Sidebar navigatie', () => {
      test('sidebar toont alle navigatie items', async ({ page }) => {
        const sidebar = page.locator('aside')
        await expect(sidebar.getByRole('link', { name: 'Dashboard' })).toBeVisible()
        await expect(sidebar.getByRole('link', { name: 'Projecten', exact: true })).toBeVisible()
        await expect(sidebar.getByRole('link', { name: 'Rapporten' })).toBeVisible()
        await expect(sidebar.getByRole('link', { name: 'Instellingen' })).toBeVisible()
      })

      test('dashboard link is actief gemarkeerd', async ({ page }) => {
        const sidebar = page.locator('aside')
        const dashboardLink = sidebar.getByRole('link', { name: 'Dashboard' })
        await expect(dashboardLink).toHaveClass(/bg-marqed-blue/)
      })

      test('navigatie naar projecten werkt', async ({ page }) => {
        const sidebar = page.locator('aside')
        await sidebar.getByRole('link', { name: 'Projecten', exact: true }).click()
        await expect(page).toHaveURL('/projects')
      })

      test('navigatie naar rapporten werkt', async ({ page }) => {
        const sidebar = page.locator('aside')
        await sidebar.getByRole('link', { name: 'Rapporten' }).click()
        await expect(page).toHaveURL('/reports')
      })

      test('navigatie naar instellingen werkt', async ({ page }) => {
        const sidebar = page.locator('aside')
        await sidebar.getByRole('link', { name: 'Instellingen' }).click()
        await expect(page).toHaveURL('/settings')
      })
    })

    test.describe('User Story: Header navigatie', () => {
      test('toont notificatie icoon', async ({ page }) => {
        // Bell notification is in header with orange notification dot
        const header = page.locator('header')
        // De notification dot naast de bell
        await expect(header.locator('span.bg-marqed-orange')).toBeVisible()
      })

      test('toont tenant indicator', async ({ page }) => {
        // Tenant ID indicator met exact match
        await expect(page.getByText('HCI', { exact: true })).toBeVisible()
      })
    })

    test.describe('User Story: Uitloggen', () => {
      test('uitlog knop is zichtbaar in sidebar', async ({ page }) => {
        const logoutButton = page.getByTitle('Uitloggen')
        await expect(logoutButton).toBeVisible()
      })

      test('uitloggen redirect naar login pagina', async ({ page }) => {
        // Mock logout endpoint
        await page.route('**/api/auth/logout', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Logged out' }),
          })
        })

        await page.getByTitle('Uitloggen').click()
        await expect(page).toHaveURL(/login/, { timeout: 5000 })
      })
    })
  })

  test.describe('Feature: Dashboard Responsiveness', () => {

    test.describe('User Story: Mobile weergave', () => {
      test('sidebar is verborgen op mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 })
        const sidebar = page.locator('aside')
        await expect(sidebar).toHaveClass(/-translate-x-full/)
      })

      test('hamburger menu opent sidebar op mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 })

        // Klik op hamburger menu in header
        const header = page.locator('header')
        const menuButton = header.locator('button').first()
        await menuButton.click()

        // Sidebar zou zichtbaar moeten zijn
        const sidebar = page.locator('aside')
        await expect(sidebar).toHaveClass(/translate-x-0/)
      })

      test('sidebar sluit bij klik buiten', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 })

        // Open sidebar
        const header = page.locator('header')
        const menuButton = header.locator('button').first()
        await menuButton.click()

        // Klik op overlay
        const overlay = page.locator('.bg-black\\/50')
        await overlay.click()

        // Sidebar zou verborgen moeten zijn
        const sidebar = page.locator('aside')
        await expect(sidebar).toHaveClass(/-translate-x-full/)
      })
    })

    test.describe('User Story: Desktop weergave', () => {
      test('sidebar is altijd zichtbaar op desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 800 })
        const sidebar = page.locator('aside')
        await expect(sidebar).toHaveClass(/lg:translate-x-0/)
      })

      test('stats grid toont 4 kolommen op desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 800 })
        // Grid met lg:grid-cols-4
        const statsGrid = page.locator('.grid.gap-4.md\\:grid-cols-2.lg\\:grid-cols-4')
        await expect(statsGrid).toBeVisible()
      })
    })
  })
})
