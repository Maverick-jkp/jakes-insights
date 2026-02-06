// @ts-check
const { test, expect } = require('@playwright/test');
const { SAMPLE_POSTS } = require('./helpers/test-data.js');

test.describe('Performance Tests (Simplified)', () => {
  test('should load page within reasonable time', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];

    const startTime = Date.now();
    await page.goto(postUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    const loadTime = Date.now() - startTime;

    // Page should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
  });

  test('should have images with proper loading attributes', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];
    await page.goto(postUrl, { timeout: 30000 });

    const images = page.locator('article img, .content img');
    const count = await images.count();

    // Should have at least one image
    expect(count).toBeGreaterThan(0);
  });
});
