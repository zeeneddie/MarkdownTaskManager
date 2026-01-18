import { test, expect } from '@playwright/test'

test.describe('Storybook Components', () => {
  test('Button - all variants render correctly', async ({ page }) => {
    await page.goto('/iframe.html?id=ui-button--all-variants&viewMode=story')

    // Wait for story to load
    await page.waitForSelector('button')

    // Check all variant buttons are present
    await expect(page.getByRole('button', { name: 'Default' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Secondary' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Destructive' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Outline' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Ghost' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Link' })).toBeVisible()
  })

  test('Button - all sizes render correctly', async ({ page }) => {
    await page.goto('/iframe.html?id=ui-button--all-sizes&viewMode=story')

    await page.waitForSelector('button')

    await expect(page.getByRole('button', { name: 'Small' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Default' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Large' })).toBeVisible()
  })

  test('Button - loading state shows spinner', async ({ page }) => {
    await page.goto('/iframe.html?id=ui-button--loading&viewMode=story')

    await page.waitForSelector('button')

    const button = page.getByRole('button')
    await expect(button).toBeDisabled()
    await expect(page.getByText('Please wait')).toBeVisible()
  })

  test('Button - with icon renders correctly', async ({ page }) => {
    await page.goto('/iframe.html?id=ui-button--with-icon&viewMode=story')

    await page.waitForSelector('button')

    await expect(page.getByRole('button')).toBeVisible()
    // Icon should be present (SVG element)
    await expect(page.locator('button svg')).toBeVisible()
  })
})

test.describe('Storybook Pages', () => {
  test('LoginPage renders correctly', async ({ page }) => {
    await page.goto('/iframe.html?id=pages-auth-loginpage--default&viewMode=story')

    // Wait for page content
    await page.waitForSelector('form')

    // Check form elements
    await expect(page.getByText('Client Portal')).toBeVisible()
    await expect(page.getByLabel('E-mailadres')).toBeVisible()
    await expect(page.getByLabel('Wachtwoord')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Inloggen' })).toBeVisible()
  })

  test('LoginPage - mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/iframe.html?id=pages-auth-loginpage--mobile&viewMode=story')

    await page.waitForSelector('form')

    // Mobile logo should be visible
    await expect(page.locator('img[alt="MarQed.ai"]')).toBeVisible()
  })
})

test.describe('Storybook Accessibility', () => {
  test('Button has correct ARIA attributes', async ({ page }) => {
    await page.goto('/iframe.html?id=ui-button--disabled&viewMode=story')

    await page.waitForSelector('button')

    const button = page.getByRole('button')
    await expect(button).toBeDisabled()
    await expect(button).toHaveAttribute('disabled', '')
  })
})
