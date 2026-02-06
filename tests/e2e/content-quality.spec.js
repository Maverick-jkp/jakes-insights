// @ts-check
const { test, expect } = require('@playwright/test');
const { SAMPLE_POSTS, VALID_CATEGORIES } = require('./helpers/test-data.js');

test.describe('Content Quality Tests (Simplified)', () => {
  test('should have at least one image', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];
    await page.goto(postUrl, { timeout: 30000 });

    const images = page.locator('article img, .content img');
    const count = await images.count();

    expect(count).toBeGreaterThan(0);
  });

  test('should have valid category in URL', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];

    // Extract category from URL (e.g., /ko/tech/2026-02-05-post/)
    const categoryMatch = postUrl.match(/\/ko\/([^\/]+)\//);
    expect(categoryMatch).toBeTruthy();

    const category = categoryMatch[1];
    expect(VALID_CATEGORIES).toContain(category);
  });

  test('should have proper heading structure', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];
    await page.goto(postUrl, { timeout: 30000 });

    const h1Count = await page.locator('h1').count();
    const h2Count = await page.locator('h2').count();

    // Should have exactly 1 h1 (main title)
    expect(h1Count).toBe(1);

    // Should have at least some h2 for structure
    expect(h2Count).toBeGreaterThan(0);
  });

  test('should have reasonable content length', async ({ page }) => {
    const postUrl = SAMPLE_POSTS.ko[0];
    await page.goto(postUrl, { timeout: 30000 });

    const content = await page.locator('article, .post-content, .content').first().textContent();

    // Content should exist and be substantial (> 500 words)
    expect(content).toBeTruthy();
    const wordCount = content.split(/\s+/).length;
    expect(wordCount).toBeGreaterThan(500);
  });
});
