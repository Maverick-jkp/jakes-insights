// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Image Loading Tests', () => {
  test('should load images on homepage', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find all images
    const images = page.locator('img');
    const count = await images.count();

    // Should have at least one image
    expect(count).toBeGreaterThan(0);

    // Check first image loads successfully
    if (count > 0) {
      const firstImg = images.first();
      await expect(firstImg).toBeVisible();

      // Check image has src attribute
      const src = await firstImg.getAttribute('src');
      expect(src).toBeTruthy();
    }
  });

  test('should have alt text for images', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const images = page.locator('img');
    const count = await images.count();

    if (count > 0) {
      // Check at least 80% of images have alt text
      let imagesWithAlt = 0;

      for (let i = 0; i < Math.min(count, 10); i++) {
        const img = images.nth(i);
        const alt = await img.getAttribute('alt');
        if (alt && alt.length > 0) {
          imagesWithAlt++;
        }
      }

      const checkedCount = Math.min(count, 10);
      const altPercentage = (imagesWithAlt / checkedCount) * 100;

      // At least 80% should have alt text
      expect(altPercentage).toBeGreaterThanOrEqual(80);
    }
  });

  test('should load post thumbnail images', async ({ page }) => {
    await page.goto('/');

    // Find first post link
    const postLink = page.locator('article a, .post a, [class*="post"] a').first();

    if (await postLink.count() > 0) {
      await postLink.click();
      await page.waitForLoadState('networkidle');

      // Check if post has images
      const postImages = page.locator('article img, .content img, main img');
      const imageCount = await postImages.count();

      if (imageCount > 0) {
        const firstImage = postImages.first();
        await expect(firstImage).toBeVisible();

        // Verify image loaded (naturalWidth > 0)
        const naturalWidth = await firstImage.evaluate((img) => img.naturalWidth);
        expect(naturalWidth).toBeGreaterThan(0);
      }
    }
  });

  test('should handle broken images gracefully', async ({ page }) => {
    await page.goto('/');

    // Check for any broken images (images with 0 natural width)
    const allImages = page.locator('img');
    const count = await allImages.count();

    let brokenImages = 0;
    for (let i = 0; i < Math.min(count, 10); i++) {
      try {
        const img = allImages.nth(i);
        const naturalWidth = await img.evaluate((el) => el.naturalWidth);
        if (naturalWidth === 0) {
          brokenImages++;
        }
      } catch (e) {
        // Image might not be loaded yet, skip
      }
    }

    // Less than 20% broken images is acceptable
    const checkedCount = Math.min(count, 10);
    const brokenPercentage = (brokenImages / checkedCount) * 100;
    expect(brokenPercentage).toBeLessThan(20);
  });
});
