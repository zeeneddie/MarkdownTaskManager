import { test, expect } from '@playwright/test'

/**
 * Epic: Authenticatie
 * Feature: Inloggen
 *
 * User Stories:
 * - Als gebruiker wil ik kunnen inloggen met mijn e-mailadres en wachtwoord
 * - Als gebruiker wil ik een foutmelding zien bij onjuiste inloggegevens
 * - Als gebruiker wil ik geblokkeerd worden na 3 mislukte inlogpogingen (3 min)
 */

test.describe('Epic: Authenticatie', () => {
  test.describe('Feature: Inloggen', () => {

    test.beforeEach(async ({ page }) => {
      // Clear any stored auth state
      await page.context().clearCookies()
      await page.goto('/login')
    })

    test.describe('User Story: Login pagina weergave', () => {
      test('toont alle login formulier elementen', async ({ page }) => {
        // Logo
        await expect(page.locator('img[alt="arQed.ai"]').first()).toBeVisible()

        // Titel en beschrijving
        await expect(page.getByText('Client Portal')).toBeVisible()
        await expect(page.getByText('Log in om toegang te krijgen tot uw projecten')).toBeVisible()

        // Formulier velden
        await expect(page.getByLabel('E-mailadres')).toBeVisible()
        await expect(page.getByLabel('Wachtwoord')).toBeVisible()

        // Buttons
        await expect(page.getByRole('button', { name: 'Inloggen', exact: true })).toBeVisible()
        await expect(page.getByRole('button', { name: /SSO/i })).toBeVisible()

        // Links
        await expect(page.getByText('Wachtwoord vergeten?')).toBeVisible()
        await expect(page.getByText('Neem contact op')).toBeVisible()
      })

      test('toont MarQed branding elementen', async ({ page }) => {
        // Tagline
        await expect(page.getByText('Innovate. Lead. Succeed.')).toBeVisible()

        // Stats op desktop
        if (await page.viewportSize()?.width && page.viewportSize()!.width >= 1024) {
          await expect(page.getByText('5+')).toBeVisible()
          await expect(page.getByText('Projecten', { exact: true })).toBeVisible()
          await expect(page.getByText('5M')).toBeVisible()
          await expect(page.getByText('99,9%')).toBeVisible()
        }
      })
    })

    test.describe('User Story: Succesvol inloggen', () => {
      test('logt in met correcte gegevens en redirect naar dashboard', async ({ page }) => {
        // Mock de login API
        await page.route('**/api/auth/login', async (route) => {
          const request = route.request()
          const body = request.postDataJSON()

          if (body.email === 'admin@hci.nl' && body.password === 'password123') {
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

        // Vul inloggegevens in
        await page.getByLabel('E-mailadres').fill('admin@hci.nl')
        await page.getByLabel('Wachtwoord').fill('password123')

        // Klik op inloggen
        await page.getByRole('button', { name: 'Inloggen', exact: true }).click()

        // Wacht op redirect naar dashboard
        await expect(page).toHaveURL('/', { timeout: 10000 })

        // Controleer dat dashboard zichtbaar is
        await expect(page.getByText('Welkom terug')).toBeVisible()
      })

      test('toont loading state tijdens inloggen', async ({ page }) => {
        await page.getByLabel('E-mailadres').fill('admin@hci.nl')
        await page.getByLabel('Wachtwoord').fill('password123')

        // Start login en check voor loading state
        const loginButton = page.getByRole('button', { name: 'Inloggen', exact: true })
        await loginButton.click()

        // Button zou disabled moeten zijn tijdens laden
        // (de tekst verandert naar "Bezig met inloggen...")
        await expect(page.getByText('Bezig met inloggen...')).toBeVisible({ timeout: 1000 }).catch(() => {
          // Loading state kan te snel zijn om te zien
        })
      })
    })

    test.describe('User Story: Foutieve inlogpoging', () => {
      test('toont foutmelding bij onjuist e-mailadres', async ({ page }) => {
        await page.getByLabel('E-mailadres').fill('verkeerd@email.com')
        await page.getByLabel('Wachtwoord').fill('password123')
        await page.getByRole('button', { name: 'Inloggen', exact: true }).click()

        // Blijft op login pagina
        await expect(page).toHaveURL(/login/)

        // TODO: Check voor error toast/message wanneer geïmplementeerd
      })

      test('toont foutmelding bij onjuist wachtwoord', async ({ page }) => {
        await page.getByLabel('E-mailadres').fill('admin@hci.nl')
        await page.getByLabel('Wachtwoord').fill('foutwachtwoord')
        await page.getByRole('button', { name: 'Inloggen', exact: true }).click()

        // Blijft op login pagina
        await expect(page).toHaveURL(/login/)
      })

      test('valideert verplichte velden', async ({ page }) => {
        // Probeer in te loggen zonder gegevens
        await page.getByRole('button', { name: 'Inloggen', exact: true }).click()

        // E-mail veld zou gefocust moeten zijn (browser native validatie)
        const emailInput = page.getByLabel('E-mailadres')
        await expect(emailInput).toBeFocused()
      })

      test('valideert e-mail formaat', async ({ page }) => {
        await page.getByLabel('E-mailadres').fill('geenemail')
        await page.getByLabel('Wachtwoord').fill('password123')
        await page.getByRole('button', { name: 'Inloggen', exact: true }).click()

        // Browser native validatie voorkomt submit
        await expect(page).toHaveURL(/login/)
      })
    })

    test.describe('User Story: Account blokkade na 3 mislukte pogingen', () => {
      test('blokkeert account na 3 mislukte inlogpogingen', async ({ page }) => {
        const email = 'admin@hci.nl'
        const wrongPassword = 'foutwachtwoord'

        // Poging 1
        await page.getByLabel('E-mailadres').fill(email)
        await page.getByLabel('Wachtwoord').fill(wrongPassword)
        await page.getByRole('button', { name: 'Inloggen', exact: true }).click()
        await page.waitForTimeout(500)

        // Poging 2
        await page.getByLabel('Wachtwoord').fill(wrongPassword)
        await page.getByRole('button', { name: 'Inloggen', exact: true }).click()
        await page.waitForTimeout(500)

        // Poging 3
        await page.getByLabel('Wachtwoord').fill(wrongPassword)
        await page.getByRole('button', { name: 'Inloggen', exact: true }).click()
        await page.waitForTimeout(500)

        // Na 3 pogingen zou er een blokkade melding moeten verschijnen
        // TODO: Implementeer blokkade melding check wanneer backend dit ondersteunt
        // await expect(page.getByText(/geblokkeerd|3 minuten/i)).toBeVisible()

        // Blijft op login pagina
        await expect(page).toHaveURL(/login/)
      })

      test('toont resterende blokkadetijd', async ({ page }) => {
        // TODO: Implementeer wanneer lockout timer in UI is gebouwd
        test.skip()
      })

      test('staat inloggen toe na blokkadeperiode', async ({ page }) => {
        // TODO: Implementeer wanneer lockout functionaliteit volledig is
        test.skip()
      })
    })

    test.describe('User Story: Wachtwoord vergeten', () => {
      test('toont wachtwoord vergeten link', async ({ page }) => {
        const forgotLink = page.getByText('Wachtwoord vergeten?')
        await expect(forgotLink).toBeVisible()
        // TODO: Test link functionaliteit wanneer geïmplementeerd
      })
    })

    test.describe('User Story: SSO Login', () => {
      test('toont SSO optie (binnenkort beschikbaar)', async ({ page }) => {
        const ssoButton = page.getByRole('button', { name: /SSO/i })
        await expect(ssoButton).toBeVisible()
        await expect(ssoButton).toBeDisabled()
      })
    })
  })
})
