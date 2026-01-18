import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.getByLabel('E-mailadres').fill('admin@hci.nl')
    await page.getByLabel('Wachtwoord').fill('password123')
    await page.getByRole('button', { name: 'Inloggen' }).click()
    await expect(page).toHaveURL('/')
  })

  test('shows welcome message with user name', async ({ page }) => {
    await expect(page.getByText('Welkom terug')).toBeVisible()
  })

  test('displays stats cards', async ({ page }) => {
    await expect(page.getByText('Totaal Projecten')).toBeVisible()
    await expect(page.getByText('Actieve Analyses')).toBeVisible()
    await expect(page.getByText('In Behandeling')).toBeVisible()
    await expect(page.getByText('Afgerond')).toBeVisible()
  })

  test('shows recent projects section', async ({ page }) => {
    await expect(page.getByText('Recente Projecten')).toBeVisible()
    await expect(page.getByRole('link', { name: 'Alle projecten' })).toBeVisible()
  })

  test('sidebar navigation works', async ({ page }) => {
    // Click on Projecten in sidebar
    await page.getByRole('link', { name: 'Projecten' }).click()
    await expect(page).toHaveURL('/projects')

    // Click on Dashboard to go back
    await page.getByRole('link', { name: 'Dashboard' }).click()
    await expect(page).toHaveURL('/')
  })

  test('shows tenant indicator in header', async ({ page }) => {
    // Should show tenant ID in header
    await expect(page.getByText('HCI')).toBeVisible()
  })

  test('responsive sidebar behavior', async ({ page }) => {
    // Resize to mobile view
    await page.setViewportSize({ width: 375, height: 667 })

    // Sidebar should be hidden
    const sidebar = page.locator('aside')
    await expect(sidebar).toHaveCSS('transform', 'matrix(1, 0, 0, 1, -256, 0)')

    // Open sidebar via menu button
    await page.getByRole('button').first().click()

    // Sidebar should be visible
    await expect(sidebar).toHaveCSS('transform', 'matrix(1, 0, 0, 1, 0, 0)')
  })
})
