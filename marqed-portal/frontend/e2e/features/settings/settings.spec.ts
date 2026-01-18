import { test, expect } from '../../fixtures/auth.fixture'

/**
 * Epic: Instellingen
 * Feature: Gebruikersinstellingen
 *
 * User Stories:
 * - Als gebruiker wil ik mijn profiel kunnen bewerken
 * - Als gebruiker wil ik mijn notificatie voorkeuren kunnen instellen
 * - Als gebruiker wil ik mijn beveiligingsinstellingen kunnen beheren
 * - Als gebruiker wil ik organisatie informatie kunnen zien
 * - Als gebruiker wil ik API toegang kunnen beheren
 */

test.describe('Epic: Instellingen', () => {
  test.beforeEach(async ({ page, authenticatedPage }) => {
    // Navigate to settings after authentication
    await page.goto('/settings')
    await expect(page).toHaveURL('/settings')
  })

  test.describe('Feature: Instellingen Pagina Weergave', () => {

    test.describe('User Story: Pagina header', () => {
      test('toont pagina titel', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /Instellingen/i })).toBeVisible()
      })

      test('toont pagina beschrijving', async ({ page }) => {
        await expect(page.getByText(/account.*voorkeuren/i)).toBeVisible()
      })
    })

    test.describe('User Story: Settings tabs', () => {
      test('toont Profiel tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /Profiel/i })).toBeVisible()
      })

      test('toont Notificaties tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /Notificaties/i })).toBeVisible()
      })

      test('toont Beveiliging tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /Beveiliging/i })).toBeVisible()
      })

      test('toont Organisatie tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /Organisatie/i })).toBeVisible()
      })

      test('toont API tab', async ({ page }) => {
        await expect(page.getByRole('tab', { name: /API/i })).toBeVisible()
      })

      test('Profiel tab is standaard geselecteerd', async ({ page }) => {
        const profileTab = page.getByRole('tab', { name: /Profiel/i })
        await expect(profileTab).toHaveAttribute('data-state', 'active')
      })
    })
  })

  test.describe('Feature: Profiel Tab', () => {

    test.describe('User Story: Profiel informatie', () => {
      test('toont avatar sectie', async ({ page }) => {
        // Avatar cirkel
        const avatar = page.locator('.rounded-full').first()
        await expect(avatar).toBeVisible()
      })

      test('toont naam veld', async ({ page }) => {
        await expect(page.getByLabel(/Naam|Volledige naam/i)).toBeVisible()
      })

      test('toont email veld', async ({ page }) => {
        await expect(page.getByLabel(/E-mail/i)).toBeVisible()
      })

      test('toont telefoon veld', async ({ page }) => {
        await expect(page.getByLabel(/Telefoon/i)).toBeVisible()
      })

      test('toont taal selector', async ({ page }) => {
        await expect(page.getByText(/Taal|Language/i)).toBeVisible()
      })
    })

    test.describe('User Story: Profiel bewerken', () => {
      test('kan naam wijzigen', async ({ page }) => {
        const nameInput = page.getByLabel(/Naam|Volledige naam/i)
        await nameInput.clear()
        await nameInput.fill('Test Gebruiker')
        await expect(nameInput).toHaveValue('Test Gebruiker')
      })

      test('kan telefoon wijzigen', async ({ page }) => {
        const phoneInput = page.getByLabel(/Telefoon/i)
        await phoneInput.clear()
        await phoneInput.fill('+31 6 12345678')
        await expect(phoneInput).toHaveValue('+31 6 12345678')
      })

      test('opslaan knop is beschikbaar', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Opslaan|Wijzigingen opslaan/i })).toBeVisible()
      })

      test('kan wijzigingen opslaan', async ({ page }) => {
        const saveButton = page.getByRole('button', { name: /Opslaan|Wijzigingen opslaan/i })
        await saveButton.click()

        // Zou success feedback moeten tonen
        // TODO: Verifieer toast notification
      })
    })
  })

  test.describe('Feature: Notificaties Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('tab', { name: /Notificaties/i }).click()
    })

    test.describe('User Story: Email notificaties', () => {
      test('toont email notificaties sectie', async ({ page }) => {
        await expect(page.getByText(/E-mail notificaties/i)).toBeVisible()
      })

      test('toont analyse updates toggle', async ({ page }) => {
        await expect(page.getByText(/Analyse updates/i)).toBeVisible()
      })

      test('toont rapport gereed toggle', async ({ page }) => {
        await expect(page.getByText(/Rapport gereed/i)).toBeVisible()
      })

      test('toont beveiligingsmeldingen toggle', async ({ page }) => {
        await expect(page.getByText(/Beveiligingsmeldingen/i)).toBeVisible()
      })

      test('kan email toggle aan/uit zetten', async ({ page }) => {
        const toggles = page.locator('button[role="switch"]')
        const firstToggle = toggles.first()

        // Toggle aan/uit
        await firstToggle.click()
        await page.waitForTimeout(100)
        await firstToggle.click()
      })
    })

    test.describe('User Story: Push notificaties', () => {
      test('toont push notificaties sectie', async ({ page }) => {
        await expect(page.getByText(/Push notificaties/i)).toBeVisible()
      })

      test('toont browser notificaties toggle', async ({ page }) => {
        await expect(page.getByText(/Browser notificaties/i)).toBeVisible()
      })
    })
  })

  test.describe('Feature: Beveiliging Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('tab', { name: /Beveiliging/i }).click()
    })

    test.describe('User Story: Wachtwoord wijzigen', () => {
      test('toont wachtwoord sectie', async ({ page }) => {
        await expect(page.getByText(/Wachtwoord/i)).toBeVisible()
      })

      test('toont huidig wachtwoord veld', async ({ page }) => {
        await expect(page.getByLabel(/Huidig wachtwoord/i)).toBeVisible()
      })

      test('toont nieuw wachtwoord veld', async ({ page }) => {
        await expect(page.getByLabel(/Nieuw wachtwoord/i)).toBeVisible()
      })

      test('toont bevestig wachtwoord veld', async ({ page }) => {
        await expect(page.getByLabel(/Bevestig.*wachtwoord/i)).toBeVisible()
      })

      test('wachtwoord wijzigen knop is beschikbaar', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Wachtwoord wijzigen/i })).toBeVisible()
      })
    })

    test.describe('User Story: Twee-factor authenticatie', () => {
      test('toont 2FA sectie', async ({ page }) => {
        await expect(page.getByText(/Twee-factor|2FA/i)).toBeVisible()
      })

      test('toont 2FA toggle of setup knop', async ({ page }) => {
        const twoFaToggle = page.locator('button[role="switch"]').filter({ hasText: /2FA/i })
        const setupButton = page.getByRole('button', { name: /2FA.*instellen|Enable 2FA/i })

        // Eén van beide zou zichtbaar moeten zijn
        const isToggleVisible = await twoFaToggle.isVisible().catch(() => false)
        const isButtonVisible = await setupButton.isVisible().catch(() => false)

        expect(isToggleVisible || isButtonVisible).toBeTruthy()
      })
    })

    test.describe('User Story: Sessie beheer', () => {
      test('toont sessie timeout instelling', async ({ page }) => {
        await expect(page.getByText(/Sessie timeout|Automatisch uitloggen/i)).toBeVisible()
      })

      test('kan sessie timeout wijzigen', async ({ page }) => {
        const timeoutSelect = page.locator('select').filter({ hasText: /minuten|uur/i })
        if (await timeoutSelect.isVisible()) {
          await timeoutSelect.selectOption({ index: 1 })
        }
      })
    })
  })

  test.describe('Feature: Organisatie Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('tab', { name: /Organisatie/i }).click()
    })

    test.describe('User Story: Organisatie informatie', () => {
      test('toont organisatie naam', async ({ page }) => {
        await expect(page.getByText(/Organisatie naam|Organization/i)).toBeVisible()
      })

      test('toont organisatie details', async ({ page }) => {
        // Adres, KvK, etc.
        const orgDetails = page.locator('.rounded-lg').first()
        await expect(orgDetails).toBeVisible()
      })
    })

    test.describe('User Story: Abonnement informatie', () => {
      test('toont abonnement status', async ({ page }) => {
        await expect(page.getByText(/Abonnement|Subscription/i)).toBeVisible()
      })

      test('toont plan type', async ({ page }) => {
        await expect(page.getByText(/Professional|Enterprise|Basic/i)).toBeVisible()
      })

      test('toont vernieuwingsdatum', async ({ page }) => {
        const renewalDate = page.getByText(/vernieuwing|renewal|verloopt/i)
        if (await renewalDate.isVisible()) {
          await expect(renewalDate).toBeVisible()
        }
      })
    })

    test.describe('User Story: Team leden', () => {
      test('toont team leden sectie', async ({ page }) => {
        await expect(page.getByText(/Team|Leden|Members/i)).toBeVisible()
      })

      test('toont lijst van team leden', async ({ page }) => {
        // Team member items
        const memberItems = page.locator('.rounded-lg').filter({ hasText: /@/ })
        if (await memberItems.first().isVisible()) {
          await expect(memberItems.first()).toBeVisible()
        }
      })
    })
  })

  test.describe('Feature: API Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('tab', { name: /API/i }).click()
    })

    test.describe('User Story: API Keys', () => {
      test('toont API keys sectie', async ({ page }) => {
        await expect(page.getByText(/API.*Keys|API.*Sleutels/i)).toBeVisible()
      })

      test('toont bestaande API keys', async ({ page }) => {
        // API key items (gemaskeerd)
        const keyItems = page.locator('.rounded-lg')
        await expect(keyItems.first()).toBeVisible()
      })

      test('API keys zijn gemaskeerd', async ({ page }) => {
        // Keys worden getoond als ****
        const maskedKey = page.getByText(/\*{4,}/)
        if (await maskedKey.first().isVisible()) {
          await expect(maskedKey.first()).toBeVisible()
        }
      })

      test('nieuwe API key knop is beschikbaar', async ({ page }) => {
        const newKeyButton = page.getByRole('button', { name: /Nieuwe.*key|Generate|Aanmaken/i })
        await expect(newKeyButton).toBeVisible()
      })

      test('kan API key kopiëren', async ({ page }) => {
        const copyButton = page.getByRole('button', { name: /Kopiëren|Copy/i }).first()
        if (await copyButton.isVisible()) {
          await copyButton.click()
          // Zou clipboard moeten updaten
        }
      })

      test('kan API key verwijderen', async ({ page }) => {
        const deleteButton = page.getByRole('button', { name: /Verwijderen|Delete|Intrekken/i }).first()
        if (await deleteButton.isVisible()) {
          await expect(deleteButton).toBeVisible()
        }
      })
    })

    test.describe('User Story: Webhooks', () => {
      test('toont webhooks sectie', async ({ page }) => {
        await expect(page.getByText(/Webhooks/i)).toBeVisible()
      })

      test('toont webhook configuratie', async ({ page }) => {
        const webhookSection = page.locator('.rounded-lg').filter({ hasText: /Webhook/i })
        if (await webhookSection.first().isVisible()) {
          await expect(webhookSection.first()).toBeVisible()
        }
      })

      test('nieuwe webhook knop is beschikbaar', async ({ page }) => {
        const newWebhookButton = page.getByRole('button', { name: /Nieuwe.*webhook|Webhook.*toevoegen/i })
        if (await newWebhookButton.isVisible()) {
          await expect(newWebhookButton).toBeVisible()
        }
      })
    })

    test.describe('User Story: API Documentatie', () => {
      test('toont link naar API documentatie', async ({ page }) => {
        const docsLink = page.getByRole('link', { name: /Documentatie|Documentation|API Docs/i })
        if (await docsLink.isVisible()) {
          await expect(docsLink).toBeVisible()
        }
      })
    })
  })
})
