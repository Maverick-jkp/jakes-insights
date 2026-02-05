// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Homepage Tests', () => {
  test('should load homepage successfully', async ({ page }) => {
    await page.goto('/');

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Check page title
    await expect(page).toHaveTitle(/Jake's.*Insights/i);

    // Check main heading exists
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible();
  });

  test('should have navigation menu', async ({ page }) => {
    await page.goto('/');

    // Check for navigation elements (header or any links)
    const hasNav = await page.locator('nav').count();
    const hasLinks = await page.locator('a').count();

    // Should have either nav or at least some links
    expect(hasNav + hasLinks).toBeGreaterThan(0);
  });

  test('should display recent posts', async ({ page }) => {
    await page.goto('/');

    // Check for article/post elements
    const posts = page.locator('article, .post, [class*="post"]');
    const count = await posts.count();

    // Should have at least one post
    expect(count).toBeGreaterThan(0);
  });

  test('should have footer', async ({ page }) => {
    await page.goto('/');

    // Check footer exists
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Page should still load
    await expect(page).toHaveTitle(/Jake's.*Insights/i);
  });
});
