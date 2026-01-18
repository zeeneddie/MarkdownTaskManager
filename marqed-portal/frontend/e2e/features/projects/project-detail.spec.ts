import { test, expect } from '../../fixtures/auth.fixture'

/**
 * Epic: Projecten
 * Feature: Project Detail
 *
 * User Stories:
 * - Als gebruiker wil ik gedetailleerde project informatie zien
 * - Als gebruiker wil ik code quality metrics per project zien
 * - Als gebruiker wil ik modules en repositories zien
 * - Als gebruiker wil ik project rapporten kunnen bekijken
 */

test.describe('Epic: Projecten - Detail', () => {
  test.beforeEach(async ({ page, authenticatedPage }) => {
    // Navigate to project detail after authentication
    await page.goto('/projects/1')
    await expect(page).toHaveURL(/\/projects\/\d+/)
  })

  test.describe('Feature: Project Detail Weergave', () => {

    test.describe('User Story: Project header', () => {
      test('toont terug link naar projecten', async ({ page }) => {
        const backLink = page.locator('a[href="/projects"]')
        await expect(backLink).toBeVisible()
      })

      test('terug link navigeert naar projecten lijst', async ({ page }) => {
        const backLink = page.locator('a[href="/projects"]')
        await backLink.click()
        await expect(page).toHaveURL('/projects')
      })
    })

    test.describe('User Story: Project tabs', () => {
      test('toont Overzicht tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /overzicht/i })).toBeVisible()
      })

      test('toont Modules tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /modules/i })).toBeVisible()
      })

      test('toont Repositories tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /repositories/i })).toBeVisible()
      })

      test('toont Rapporten tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /rapporten/i })).toBeVisible()
      })
    })
  })

  test.describe('Feature: Overzicht Tab', () => {

    test.describe('User Story: Code Quality Score', () => {
      test('toont quality score sectie', async ({ page }) => {
        await page.waitForLoadState('networkidle')
        // Score ring of quality indicator
        const scoreElement = page.locator('text=/\\d+/').first()
        await expect(scoreElement).toBeVisible()
      })
    })

    test.describe('User Story: Quality Metrics', () => {
      test('toont metric labels', async ({ page }) => {
        await page.waitForLoadState('networkidle')
        // Nederlandse of Engelse labels
        const metricLabel = page.getByText(/Onderhoudbaarheid|Betrouwbaarheid|Beveiliging|Maintainability|Reliability|Security/i).first()
        await expect(metricLabel).toBeVisible()
      })
    })
  })

  test.describe('Feature: Modules Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('tab', { name: /modules/i }).click()
      await page.waitForTimeout(300)
    })

    test.describe('User Story: Module lijst', () => {
      test('toont modules sectie na tab klik', async ({ page }) => {
        // Na tab klik zou content moeten laden
        const tabContent = page.locator('[role="tabpanel"]')
        await expect(tabContent).toBeVisible()
      })
    })
  })

  test.describe('Feature: Repositories Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('tab', { name: /repositories/i }).click()
      await page.waitForTimeout(300)
    })

    test.describe('User Story: Repository lijst', () => {
      test('toont repositories sectie na tab klik', async ({ page }) => {
        const tabContent = page.locator('[role="tabpanel"]')
        await expect(tabContent).toBeVisible()
      })
    })
  })

  test.describe('Feature: Rapporten Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('tab', { name: /rapporten/i }).click()
      await page.waitForTimeout(300)
    })

    test.describe('User Story: Rapporten lijst', () => {
      test('toont rapporten sectie na tab klik', async ({ page }) => {
        const tabContent = page.locator('[role="tabpanel"]')
        await expect(tabContent).toBeVisible()
      })
    })
  })
})
