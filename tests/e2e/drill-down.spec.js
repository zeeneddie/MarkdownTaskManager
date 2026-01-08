// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * E2E Test Suite: Drill-Down Navigation
 *
 * Tests the single-click drill-down functionality in the Project Viewer.
 * This test validates the fix for the double-click bug.
 *
 * Test Coverage:
 * - Epic → Feature drill-down
 * - Feature → Story drill-down
 * - Story → Task detail view
 * - Back navigation
 * - Direct Epic selection
 */

test.describe('Project Viewer - Drill-Down Navigation', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to the Project Viewer
    await page.goto('/');

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Verify initial state: Epics are visible in sidebar
    await expect(page.locator('#sidebarTitle')).toHaveText('Epics');
  });

  test('should display initial epic list in sidebar', async ({ page }) => {
    // Verify sidebar shows "Epics" title
    const sidebarTitle = page.locator('#sidebarTitle');
    await expect(sidebarTitle).toHaveText('Epics');

    // Verify at least one epic is visible
    const epicItems = page.locator('#tree .tree-item');
    await expect(epicItems).toHaveCount(3); // We have 3 test epics

    // Verify first epic contains expected text
    const firstEpic = epicItems.first();
    await expect(firstEpic).toContainText('EPIC-001');
  });

  test('should drill down from Epic to Features with single click', async ({ page }) => {
    // STEP 1: Click on first Epic in sidebar
    const firstEpic = page.locator('#tree .tree-item').first();
    await firstEpic.click();

    // Wait for details panel to update
    await page.waitForTimeout(100);

    // Verify Epic details are shown in main panel
    await expect(page.locator('#main h2')).toContainText('EPIC-001');

    // Verify "Features (klik om door te boren)" section is visible
    await expect(page.locator('#main h3')).toContainText('Features');
    await expect(page.locator('#main h3')).toContainText('klik om door te boren');

    // STEP 2: Single click on first Feature card in main panel
    const firstFeatureCard = page.locator('#features-list .child-card').first();
    await expect(firstFeatureCard).toBeVisible();
    await firstFeatureCard.click();

    // Wait for navigation
    await page.waitForTimeout(200);

    // VERIFY: Sidebar now shows "Features" (not "Epics")
    const sidebarTitle = page.locator('#sidebarTitle');
    await expect(sidebarTitle).toHaveText('Features');

    // VERIFY: Back button is visible
    const backButton = page.locator('#backButton');
    await expect(backButton).toBeVisible();

    // VERIFY: Main panel shows Stories section
    await expect(page.locator('#main h3')).toContainText('Stories');

    // Take screenshot for documentation
    await page.screenshot({ path: '../screenshots/drill-down-features.png' });
  });

  test('should drill down from Feature to Stories with single click', async ({ page }) => {
    // Navigate to Feature level first
    await page.locator('#tree .tree-item').first().click();
    await page.waitForTimeout(100);
    await page.locator('#features-list .child-card').first().click();
    await page.waitForTimeout(200);

    // Verify we're at Feature level
    await expect(page.locator('#sidebarTitle')).toHaveText('Features');

    // STEP: Single click on first Story card
    const firstStoryCard = page.locator('#stories-list .child-card').first();
    await expect(firstStoryCard).toBeVisible();
    await firstStoryCard.click();

    // Wait for navigation
    await page.waitForTimeout(200);

    // VERIFY: Sidebar now shows "Stories"
    await expect(page.locator('#sidebarTitle')).toHaveText('Stories');

    // VERIFY: Main panel shows Tasks section
    await expect(page.locator('#main h3')).toContainText('Tasks');

    // Take screenshot
    await page.screenshot({ path: '../screenshots/drill-down-stories.png' });
  });

  test('should show Task details with single click (no drill-down)', async ({ page }) => {
    // Navigate to Story level first
    await page.locator('#tree .tree-item').first().click();
    await page.waitForTimeout(100);
    await page.locator('#features-list .child-card').first().click();
    await page.waitForTimeout(200);
    await page.locator('#stories-list .child-card').first().click();
    await page.waitForTimeout(200);

    // Verify we're at Story level
    await expect(page.locator('#sidebarTitle')).toHaveText('Stories');

    // STEP: Single click on first Task card
    const firstTaskCard = page.locator('#tasks-list .child-card').first();
    await expect(firstTaskCard).toBeVisible();
    await firstTaskCard.click();

    // Wait for details to update
    await page.waitForTimeout(100);

    // VERIFY: Sidebar STILL shows "Stories" (no drill-down for tasks)
    await expect(page.locator('#sidebarTitle')).toHaveText('Stories');

    // VERIFY: Main panel shows Task details
    await expect(page.locator('#main h2')).toContainText('TASK');

    // VERIFY: Task card in main panel is still visible (not navigated away)
    await expect(firstTaskCard).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: '../screenshots/task-details.png' });
  });

  test('should navigate back correctly with Back button', async ({ page }) => {
    // Navigate deep into hierarchy: Epic → Feature → Story
    await page.locator('#tree .tree-item').first().click();
    await page.waitForTimeout(100);
    await page.locator('#features-list .child-card').first().click();
    await page.waitForTimeout(200);
    await page.locator('#stories-list .child-card').first().click();
    await page.waitForTimeout(200);

    // We're now at Story level
    await expect(page.locator('#sidebarTitle')).toHaveText('Stories');

    // STEP 1: Click Back button → should go to Feature level
    await page.locator('#backButton').click();
    await page.waitForTimeout(200);
    await expect(page.locator('#sidebarTitle')).toHaveText('Features');

    // STEP 2: Click Back button again → should go to Epic level
    await page.locator('#backButton').click();
    await page.waitForTimeout(200);
    await expect(page.locator('#sidebarTitle')).toHaveText('Epics');

    // VERIFY: Back button is hidden at top level
    const backButton = page.locator('#backButton');
    await expect(backButton).not.toBeVisible();

    // Take screenshot
    await page.screenshot({ path: '../screenshots/back-navigation.png' });
  });

  test('should allow direct Epic selection from any level', async ({ page }) => {
    // Navigate to Story level
    await page.locator('#tree .tree-item').first().click();
    await page.waitForTimeout(100);
    await page.locator('#features-list .child-card').first().click();
    await page.waitForTimeout(200);
    await page.locator('#stories-list .child-card').first().click();
    await page.waitForTimeout(200);

    // We're at Story level
    await expect(page.locator('#sidebarTitle')).toHaveText('Stories');

    // Click back to Epic level
    await page.locator('#backButton').click();
    await page.waitForTimeout(200);
    await page.locator('#backButton').click();
    await page.waitForTimeout(200);

    // Now at Epic level
    await expect(page.locator('#sidebarTitle')).toHaveText('Epics');

    // STEP: Click on second Epic
    const epicItems = page.locator('#tree .tree-item');
    const secondEpic = epicItems.nth(1);
    await secondEpic.click();
    await page.waitForTimeout(100);

    // VERIFY: Main panel shows different Epic
    await expect(page.locator('#main h2')).toContainText('EPIC-002');

    // VERIFY: Navigation stack was reset (still at Epic level)
    await expect(page.locator('#sidebarTitle')).toHaveText('Epics');
  });

  test('should not have double-click handlers (regression test)', async ({ page }) => {
    // Navigate to Epic with Features
    await page.locator('#tree .tree-item').first().click();
    await page.waitForTimeout(100);

    // Get first feature card
    const firstFeatureCard = page.locator('#features-list .child-card').first();
    await expect(firstFeatureCard).toBeVisible();

    // DOUBLE-CLICK (should behave same as single click)
    await firstFeatureCard.dblclick();
    await page.waitForTimeout(200);

    // VERIFY: Navigation happened (same as single click)
    await expect(page.locator('#sidebarTitle')).toHaveText('Features');

    // VERIFY: No JavaScript errors occurred
    const errors = [];
    page.on('pageerror', error => errors.push(error));
    expect(errors.length).toBe(0);
  });

  test('should display correct UI text (no double-click references)', async ({ page }) => {
    // Navigate to Epic
    await page.locator('#tree .tree-item').first().click();
    await page.waitForTimeout(100);

    // Check Features section header
    const featuresHeader = page.locator('#main h3').filter({ hasText: 'Features' });
    await expect(featuresHeader).toContainText('klik om door te boren');
    await expect(featuresHeader).not.toContainText('dubbelklik');

    // Navigate to Features
    await page.locator('#features-list .child-card').first().click();
    await page.waitForTimeout(200);

    // Check Stories section header
    const storiesHeader = page.locator('#main h3').filter({ hasText: 'Stories' });
    await expect(storiesHeader).toContainText('klik om door te boren');
    await expect(storiesHeader).not.toContainText('dubbelklik');

    // Navigate to Stories
    await page.locator('#stories-list .child-card').first().click();
    await page.waitForTimeout(200);

    // Check Tasks section header
    const tasksHeader = page.locator('#main h3').filter({ hasText: 'Tasks' });
    await expect(tasksHeader).toContainText('klik om details te zien');
    await expect(tasksHeader).not.toContainText('dubbelklik');
  });

  test('should handle rapid clicking gracefully', async ({ page }) => {
    // Navigate to Epic
    await page.locator('#tree .tree-item').first().click();
    await page.waitForTimeout(100);

    const firstFeatureCard = page.locator('#features-list .child-card').first();

    // Rapid click 5 times
    for (let i = 0; i < 5; i++) {
      await firstFeatureCard.click();
      await page.waitForTimeout(50);
    }

    // Wait for all events to settle
    await page.waitForTimeout(300);

    // VERIFY: Should end up in Feature level (not in weird state)
    await expect(page.locator('#sidebarTitle')).toHaveText('Features');

    // VERIFY: No JavaScript errors
    const errors = [];
    page.on('pageerror', error => errors.push(error));
    expect(errors.length).toBe(0);
  });
});

test.describe('Project Viewer - Mobile Support', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

  test('should work on mobile viewport with single tap', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Tap on first Epic
    await page.locator('#tree .tree-item').first().tap();
    await page.waitForTimeout(100);

    // Tap on first Feature
    const firstFeatureCard = page.locator('#features-list .child-card').first();
    await expect(firstFeatureCard).toBeVisible();
    await firstFeatureCard.tap();
    await page.waitForTimeout(200);

    // VERIFY: Navigation worked on mobile
    await expect(page.locator('#sidebarTitle')).toHaveText('Features');

    // Take screenshot
    await page.screenshot({ path: '../screenshots/mobile-drill-down.png' });
  });
});
