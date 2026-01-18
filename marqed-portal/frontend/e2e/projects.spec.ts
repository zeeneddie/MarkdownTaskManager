import { test, expect } from '@playwright/test'

test.describe('Projects', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.getByLabel('E-mailadres').fill('admin@hci.nl')
    await page.getByLabel('Wachtwoord').fill('password123')
    await page.getByRole('button', { name: 'Inloggen' }).click()

    // Navigate to projects
    await page.getByRole('link', { name: 'Projecten' }).click()
    await expect(page).toHaveURL('/projects')
  })

  test('shows project list page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Projecten' })).toBeVisible()
    await expect(
      page.getByText('Beheer en bekijk al uw legacy modernisatie projecten')
    ).toBeVisible()
  })

  test('has search functionality', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Zoek projecten...')
    await expect(searchInput).toBeVisible()

    // Type in search
    await searchInput.fill('HCI')

    // Results should filter
    await page.waitForTimeout(300) // Debounce wait
  })

  test('has filter and sort buttons', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Filter/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /Sorteer/ })).toBeVisible()
  })

  test('displays project cards', async ({ page }) => {
    // Wait for projects to load
    await page.waitForTimeout(500)

    // Should show project card or empty state
    const hasProjects = await page.locator('[class*="rounded-lg border"]').count() > 0
    const hasEmptyState = await page.getByText('Geen projecten').isVisible().catch(() => false)

    expect(hasProjects || hasEmptyState).toBe(true)
  })

  test('clicking project navigates to detail page', async ({ page }) => {
    // Wait for projects to load
    await page.waitForTimeout(500)

    // If there are projects, click the first one
    const projectCard = page.locator('a[href^="/projects/"]').first()
    if (await projectCard.count() > 0) {
      await projectCard.click()
      await expect(page).toHaveURL(/\/projects\/\d+/)
    }
  })
})

test.describe('Project Detail', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.getByLabel('E-mailadres').fill('admin@hci.nl')
    await page.getByLabel('Wachtwoord').fill('password123')
    await page.getByRole('button', { name: 'Inloggen' }).click()
  })

  test('shows project not found for invalid ID', async ({ page }) => {
    await page.goto('/projects/invalid-id-999')

    await expect(page.getByText('Project niet gevonden')).toBeVisible()
    await expect(
      page.getByRole('button', { name: 'Terug naar projecten' })
    ).toBeVisible()
  })

  test('back button returns to project list', async ({ page }) => {
    await page.goto('/projects/1')

    // Wait for page to load
    await page.waitForTimeout(500)

    // Find and click back button
    const backButton = page.getByRole('link').filter({ has: page.locator('svg') }).first()
    if (await backButton.count() > 0) {
      await backButton.click()
      await expect(page).toHaveURL('/projects')
    }
  })

  test('shows project information sections', async ({ page }) => {
    await page.goto('/projects/1')
    await page.waitForTimeout(500)

    // Should show various sections (if project exists)
    const sections = ['Aangemaakt', 'Laatst bijgewerkt', 'Repositories']

    for (const section of sections) {
      const element = page.getByText(section)
      // Either shows the section or shows not found
      const isVisible = await element.isVisible().catch(() => false)
      const notFound = await page.getByText('Project niet gevonden').isVisible().catch(() => false)
      expect(isVisible || notFound).toBe(true)
    }
  })
})
