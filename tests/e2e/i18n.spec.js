// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Multilingual Navigation Tests', () => {
  const languages = [
    { code: 'en', name: 'English', path: '/en/' },
    { code: 'ko', name: 'Korean', path: '/ko/' },
    { code: 'ja', name: 'Japanese', path: '/ja/' },
  ];

  for (const lang of languages) {
    test(`should load ${lang.name} homepage`, async ({ page }) => {
      await page.goto(lang.path);
      await page.waitForLoadState('networkidle');

      // Check page loaded successfully
      await expect(page).not.toHaveURL(/.*error.*/);

      // Check for content
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test(`should have ${lang.name} posts`, async ({ page }) => {
      await page.goto(lang.path);
      await page.waitForLoadState('networkidle');

      // Check for posts/articles
      const posts = page.locator('article, .post, [class*="post"]');
      const count = await posts.count();

      // Should have at least one post
      expect(count).toBeGreaterThan(0);
    });
  }

  test('should have language switcher', async ({ page }) => {
    await page.goto('/');

    // Look for language selector (common patterns)
    const langSwitcher = page.locator(
      '[class*="language"], [class*="lang"], [id*="language"], [id*="lang"], a[href*="/en/"], a[href*="/ko/"], a[href*="/ja/"]'
    );

    // Should find at least one language-related element
    const count = await langSwitcher.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should switch between languages', async ({ page }) => {
    // Start with English
    await page.goto('/en/');
    let url1 = page.url();
    expect(url1).toContain('/en/');

    // Look for Korean link
    const koLink = page.locator('a[href*="/ko/"]').first();
    if (await koLink.count() > 0) {
      await koLink.click();
      await page.waitForLoadState('networkidle');

      let url2 = page.url();
      expect(url2).toContain('/ko/');
    }
  });

  test('should maintain content structure across languages', async ({ page }) => {
    const structures = [];

    for (const lang of languages) {
      await page.goto(lang.path);
      await page.waitForLoadState('networkidle');

      // Count main elements
      const headers = await page.locator('header, nav').count();
      const mains = await page.locator('main, [role="main"], article').count();
      const footers = await page.locator('footer').count();

      structures.push({ lang: lang.code, headers, mains, footers });
    }

    // All languages should have similar structure
    const firstStruct = structures[0];
    for (const struct of structures.slice(1)) {
      // Headers should be consistent
      expect(struct.headers).toBe(firstStruct.headers);
      // Footers should be consistent
      expect(struct.footers).toBe(firstStruct.footers);
    }
  });

  test('should have proper lang attribute', async ({ page }) => {
    for (const lang of languages) {
      await page.goto(lang.path);

      // Check html lang attribute
      const htmlLang = await page.locator('html').getAttribute('lang');

      // Should start with the language code
      expect(htmlLang).toMatch(new RegExp(`^${lang.code}`, 'i'));
    }
  });
});
