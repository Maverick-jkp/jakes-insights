// @ts-check
const { test, expect } = require('@playwright/test');
const { SAMPLE_POSTS } = require('./helpers/test-data.js');

test.describe('SEO Validation Tests (Simplified)', () => {
  test('should have meta description', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];
    await page.goto(postUrl, { timeout: 30000 });

    const description = await page.locator('meta[name="description"]').getAttribute('content');
    expect(description).toBeTruthy();
    expect(description.length).toBeGreaterThan(50);
  });

  test('should have Open Graph tags', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];
    await page.goto(postUrl, { timeout: 30000 });

    const ogTitle = await page.locator('meta[property="og:title"]').getAttribute('content');
    const ogDescription = await page.locator('meta[property="og:description"]').getAttribute('content');
    const ogImage = await page.locator('meta[property="og:image"]').getAttribute('content');

    expect(ogTitle).toBeTruthy();
    expect(ogDescription).toBeTruthy();
    expect(ogImage).toBeTruthy();
  });

  test('should have Twitter Card tags', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];
    await page.goto(postUrl, { timeout: 30000 });

    const twitterCard = await page.locator('meta[name="twitter:card"]').getAttribute('content');
    const twitterTitle = await page.locator('meta[name="twitter:title"]').getAttribute('content');

    expect(twitterCard).toBeTruthy();
    expect(twitterTitle).toBeTruthy();
  });
});
