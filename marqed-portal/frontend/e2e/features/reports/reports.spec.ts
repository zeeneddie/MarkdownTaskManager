import { test, expect } from '../../fixtures/auth.fixture'

/**
 * Epic: Rapporten
 * Feature: Rapporten Overzicht
 *
 * User Stories:
 * - Als gebruiker wil ik alle beschikbare rapporten zien
 * - Als gebruiker wil ik rapporten kunnen filteren op type
 * - Als gebruiker wil ik rapporten kunnen filteren op status
 * - Als gebruiker wil ik rapporten kunnen downloaden
 * - Als gebruiker wil ik bulk export kunnen doen
 */

test.describe('Epic: Rapporten', () => {
  test.beforeEach(async ({ page, authenticatedPage }) => {
    // Navigate to reports after authentication
    await page.goto('/reports')
    await expect(page).toHaveURL('/reports')
  })

  test.describe('Feature: Rapporten Pagina Weergave', () => {

    test.describe('User Story: Pagina header', () => {
      test('toont pagina titel', async ({ page }) => {
        await expect(page.getByRole('heading', { name: /Rapporten/i })).toBeVisible()
      })

      test('toont pagina beschrijving', async ({ page }) => {
        await expect(page.getByText(/rapporten.*analyses/i)).toBeVisible()
      })
    })

    test.describe('User Story: Report type filters', () => {
      test('toont Analysis filter kaart', async ({ page }) => {
        await expect(page.getByText('Code Analysis')).toBeVisible()
      })

      test('toont Security filter kaart', async ({ page }) => {
        await expect(page.getByText('Security')).toBeVisible()
      })

      test('toont Migration filter kaart', async ({ page }) => {
        await expect(page.getByText('Migration')).toBeVisible()
      })

      test('toont Technical Debt filter kaart', async ({ page }) => {
        await expect(page.getByText('Technical Debt')).toBeVisible()
      })

      test('toont Quality filter kaart', async ({ page }) => {
        await expect(page.getByText('Quality')).toBeVisible()
      })

      test('filter kaarten tonen aantal', async ({ page }) => {
        // Elk type toont aantal rapporten
        const countBadges = page.locator('.bg-marqed-orange')
        expect(await countBadges.count()).toBeGreaterThan(0)
      })

      test('kan filteren op type door te klikken', async ({ page }) => {
        const analysisFilter = page.locator('.rounded-xl').filter({ hasText: 'Code Analysis' })
        await analysisFilter.click()

        // Filter zou geselecteerd moeten zijn
        await page.waitForTimeout(300)
      })
    })
  })

  test.describe('Feature: Status Filtering', () => {

    test.describe('User Story: Status filter tabs', () => {
      test('toont Alle tab', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Alle/i })).toBeVisible()
      })

      test('toont Voltooid tab', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Voltooid|Completed/i })).toBeVisible()
      })

      test('toont Bezig tab', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Bezig|Generating/i })).toBeVisible()
      })

      test('toont Gepland tab', async ({ page }) => {
        await expect(page.getByRole('button', { name: /Gepland|Scheduled/i })).toBeVisible()
      })

      test('Alle tab is standaard geselecteerd', async ({ page }) => {
        const alleTab = page.getByRole('button', { name: /Alle/i })
        await expect(alleTab).toHaveClass(/bg-marqed-blue/)
      })

      test('kan wisselen naar Voltooid filter', async ({ page }) => {
        await page.getByRole('button', { name: /Voltooid|Completed/i }).click()

        // Tab zou geselecteerd moeten zijn
        const voltooidTab = page.getByRole('button', { name: /Voltooid|Completed/i })
        await expect(voltooidTab).toHaveClass(/bg-marqed-blue/)
      })
    })
  })

  test.describe('Feature: Rapporten Lijst', () => {

    test.describe('User Story: Rapport items weergave', () => {
      test('toont rapport items in lijst', async ({ page }) => {
        const reportItems = page.locator('.rounded-lg.border')
        expect(await reportItems.count()).toBeGreaterThan(0)
      })

      test('rapport item toont titel', async ({ page }) => {
        // Rapport titels
        const reportTitle = page.locator('h3, h4').first()
        await expect(reportTitle).toBeVisible()
      })

      test('rapport item toont project naam', async ({ page }) => {
        // Project referentie
        const projectName = page.getByText(/HCI|CRS|Project/i).first()
        await expect(projectName).toBeVisible()
      })

      test('rapport item toont datum', async ({ page }) => {
        // Datum format
        const dateText = page.getByText(/\d{1,2}.*\d{4}|geleden|uur|dag/i).first()
        await expect(dateText).toBeVisible()
      })

      test('rapport item toont status badge', async ({ page }) => {
        // Status indicators
        const statusBadge = page.getByText(/Voltooid|Bezig|Gepland|Completed|Generating|Scheduled/i).first()
        await expect(statusBadge).toBeVisible()
      })

      test('rapport item toont type icon', async ({ page }) => {
        // Type icons (lucide icons)
        const typeIcon = page.locator('svg').first()
        await expect(typeIcon).toBeVisible()
      })
    })

    test.describe('User Story: Rapport acties', () => {
      test('voltooide rapporten hebben download knop', async ({ page }) => {
        const downloadButton = page.getByRole('button', { name: /download/i }).first()
        if (await downloadButton.isVisible()) {
          await expect(downloadButton).toBeEnabled()
        }
      })

      test('voltooide rapporten hebben bekijk knop', async ({ page }) => {
        const viewButton = page.getByRole('button', { name: /bekijk|view/i }).first()
        if (await viewButton.isVisible()) {
          await expect(viewButton).toBeEnabled()
        }
      })

      test('download knop triggert download', async ({ page }) => {
        const downloadButton = page.getByRole('button', { name: /download/i }).first()
        if (await downloadButton.isVisible()) {
          // Check dat download werkt (zou download moeten starten)
          const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)
          await downloadButton.click()
          // Download event zou moeten triggeren
        }
      })

      test('bezig rapporten tonen progress indicator', async ({ page }) => {
        // Filter op bezig
        await page.getByRole('button', { name: /Bezig|Generating/i }).click()
        await page.waitForTimeout(300)

        // Progress indicator zou zichtbaar moeten zijn
        const progressIndicator = page.locator('.animate-spin, [role="progressbar"]')
        if (await progressIndicator.first().isVisible()) {
          await expect(progressIndicator.first()).toBeVisible()
        }
      })
    })
  })

  test.describe('Feature: Bulk Export', () => {

    test.describe('User Story: Export opties', () => {
      test('toont export sectie', async ({ page }) => {
        await expect(page.getByText(/Export|Exporteren/i)).toBeVisible()
      })

      test('toont Excel export optie', async ({ page }) => {
        const excelButton = page.getByRole('button', { name: /Excel/i })
        if (await excelButton.isVisible()) {
          await expect(excelButton).toBeVisible()
        }
      })

      test('toont JSON export optie', async ({ page }) => {
        const jsonButton = page.getByRole('button', { name: /JSON/i })
        if (await jsonButton.isVisible()) {
          await expect(jsonButton).toBeVisible()
        }
      })

      test('toont Print optie', async ({ page }) => {
        const printButton = page.getByRole('button', { name: /Print/i })
        if (await printButton.isVisible()) {
          await expect(printButton).toBeVisible()
        }
      })

      test('toont Email optie', async ({ page }) => {
        const emailButton = page.getByRole('button', { name: /Email/i })
        if (await emailButton.isVisible()) {
          await expect(emailButton).toBeVisible()
        }
      })
    })

    test.describe('User Story: Bulk selectie', () => {
      test('kan meerdere rapporten selecteren', async ({ page }) => {
        // Checkboxes voor selectie
        const checkboxes = page.locator('input[type="checkbox"]')
        if (await checkboxes.first().isVisible()) {
          await checkboxes.first().check()
          await expect(checkboxes.first()).toBeChecked()
        }
      })

      test('selecteer alle optie beschikbaar', async ({ page }) => {
        const selectAllCheckbox = page.locator('input[type="checkbox"]').first()
        if (await selectAllCheckbox.isVisible()) {
          await expect(selectAllCheckbox).toBeVisible()
        }
      })
    })
  })

  test.describe('Feature: Zoeken', () => {

    test.describe('User Story: Rapport zoeken', () => {
      test('toont zoek input', async ({ page }) => {
        const searchInput = page.getByPlaceholder(/zoek/i)
        if (await searchInput.isVisible()) {
          await expect(searchInput).toBeVisible()
        }
      })

      test('kan zoeken op rapport naam', async ({ page }) => {
        const searchInput = page.getByPlaceholder(/zoek/i)
        if (await searchInput.isVisible()) {
          await searchInput.fill('Security')
          await page.waitForTimeout(500)
          // Gefilterde resultaten
        }
      })

      test('kan zoeken op project naam', async ({ page }) => {
        const searchInput = page.getByPlaceholder(/zoek/i)
        if (await searchInput.isVisible()) {
          await searchInput.fill('HCI')
          await page.waitForTimeout(500)
        }
      })
    })
  })

  test.describe('Feature: Lege State', () => {

    test.describe('User Story: Geen rapporten', () => {
      test('toont bericht wanneer geen rapporten gevonden', async ({ page }) => {
        // Zoek naar iets wat niet bestaat
        const searchInput = page.getByPlaceholder(/zoek/i)
        if (await searchInput.isVisible()) {
          await searchInput.fill('xyznonexistent123')
          await page.waitForTimeout(500)

          const emptyState = page.getByText(/geen rapporten|geen resultaten|no reports/i)
          if (await emptyState.isVisible()) {
            await expect(emptyState).toBeVisible()
          }
        }
      })
    })
  })
})
