import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('shows login page', async ({ page }) => {
    await expect(page.getByText('Welkom bij MarQed.ai')).toBeVisible()
    await expect(page.getByLabel('E-mailadres')).toBeVisible()
    await expect(page.getByLabel('Wachtwoord')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Inloggen' })).toBeVisible()
  })

  test('shows validation for empty fields', async ({ page }) => {
    await page.getByRole('button', { name: 'Inloggen' }).click()

    // Browser native validation should prevent submission
    const emailInput = page.getByLabel('E-mailadres')
    await expect(emailInput).toBeFocused()
  })

  test('shows error for invalid credentials', async ({ page }) => {
    await page.getByLabel('E-mailadres').fill('wrong@email.com')
    await page.getByLabel('Wachtwoord').fill('wrongpassword')
    await page.getByRole('button', { name: 'Inloggen' }).click()

    // Wait for error response
    await page.waitForTimeout(500)

    // Should show error message or stay on login page
    await expect(page).toHaveURL(/login/)
  })

  test('successful login redirects to dashboard', async ({ page }) => {
    // Using mock credentials from MSW handlers
    await page.getByLabel('E-mailadres').fill('admin@hci.nl')
    await page.getByLabel('Wachtwoord').fill('password123')
    await page.getByRole('button', { name: 'Inloggen' }).click()

    // Should redirect to dashboard
    await expect(page).toHaveURL('/')
    await expect(page.getByText('Welkom terug')).toBeVisible()
  })

  test('remembers login state after page refresh', async ({ page }) => {
    // Login first
    await page.getByLabel('E-mailadres').fill('admin@hci.nl')
    await page.getByLabel('Wachtwoord').fill('password123')
    await page.getByRole('button', { name: 'Inloggen' }).click()

    await expect(page).toHaveURL('/')

    // Refresh page
    await page.reload()

    // Should still be on dashboard (authenticated)
    await expect(page.getByText('Welkom terug')).toBeVisible()
  })

  test('logout redirects to login page', async ({ page }) => {
    // Login first
    await page.getByLabel('E-mailadres').fill('admin@hci.nl')
    await page.getByLabel('Wachtwoord').fill('password123')
    await page.getByRole('button', { name: 'Inloggen' }).click()

    await expect(page).toHaveURL('/')

    // Click logout button
    await page.getByRole('button', { name: 'Uitloggen' }).click()

    // Should redirect to login
    await expect(page).toHaveURL(/login/)
  })
})
