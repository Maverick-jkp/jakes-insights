// @ts-check
const { test, expect } = require('@playwright/test');
const { SAMPLE_POSTS } = require('./helpers/test-data.js');

test.describe('Link Validation Tests', () => {
  test('should not have 404 errors in related posts', async ({ page }) => {
    const languages = ['en', 'ko', 'ja'];
    const errors = [];

    for (const lang of languages) {
      // Test sample posts for each language
      const posts = SAMPLE_POSTS[lang];

      for (const postUrl of posts.slice(0, 2)) {  // Test 2 posts per language
        try {
          await page.goto(postUrl, { waitUntil: 'networkidle' });

          // Find related posts section
          const relatedSection = page.locator('.related-posts');
          const hasRelated = await relatedSection.count() > 0;

          if (hasRelated) {
            // Find all related post links
            const relatedLinks = page.locator('.related-card');
            const count = await relatedLinks.count();

            for (let i = 0; i < count; i++) {
              const link = relatedLinks.nth(i);
              const href = await link.getAttribute('href');

              if (href) {
                // Navigate to the related post and check status
                const response = await page.goto(href, { waitUntil: 'domcontentloaded' });

                if (response && response.status() !== 200) {
                  errors.push({
                    sourcePost: postUrl,
                    relatedPost: href,
                    status: response.status(),
                  });
                }

                // Go back to the original post for next iteration
                await page.goBack();
              }
            }
          }
        } catch (error) {
          console.error(`Error testing ${postUrl}:`, error.message);
        }
      }
    }

    // Assert no 404 errors found
    if (errors.length > 0) {
      const errorMessages = errors.map(e =>
        `\n- Source: ${e.sourcePost}\n  Related: ${e.relatedPost}\n  Status: ${e.status}`
      ).join('');

      throw new Error(`Found ${errors.length} related post link(s) with errors:${errorMessages}`);
    }
  });

  test('should have working category links', async ({ page }) => {
    await page.goto('/');

    // Test main category links
    const categories = ['tech', 'business', 'society', 'entertainment', 'sports'];

    for (const category of categories) {
      const categoryLink = page.locator(`a[href*="/categories/${category}"]`).first();

      if (await categoryLink.count() > 0) {
        const response = await page.goto(`/categories/${category}/`);
        expect(response?.status()).toBe(200);
      }
    }
  });

  test('should have working language switcher links', async ({ page }) => {
    // Start with an English post
    const enPost = SAMPLE_POSTS.en[0];
    await page.goto(enPost);

    // Check for language switcher
    const langSwitcher = page.locator('.lang-switch, [class*="lang"], [class*="language"]');

    if (await langSwitcher.count() > 0) {
      const langLinks = page.locator('a[href^="/ko/"], a[href^="/ja/"], a[href^="/en/"]');
      const count = await langLinks.count();

      // Test first 3 language links
      for (let i = 0; i < Math.min(count, 3); i++) {
        const link = langLinks.nth(i);
        const href = await link.getAttribute('href');

        if (href) {
          const response = await page.goto(href);
          expect(response?.status(), `Language link failed: ${href}`).toBe(200);
        }
      }
    }
  });

  test('should have working breadcrumb links', async ({ page }) => {
    // Navigate to a post
    await page.goto(SAMPLE_POSTS.en[0]);

    // Find breadcrumb links
    const breadcrumbs = page.locator('.breadcrumbs a, [class*="breadcrumb"] a, nav[aria-label="Breadcrumb"] a');
    const count = await breadcrumbs.count();

    if (count > 0) {
      // Test each breadcrumb link
      for (let i = 0; i < count; i++) {
        const link = breadcrumbs.nth(i);
        const href = await link.getAttribute('href');

        if (href && href.startsWith('/')) {
          const response = await page.goto(href);
          expect(response?.status(), `Breadcrumb link failed: ${href}`).toBe(200);

          // Go back for next iteration
          await page.goBack();
        }
      }
    }
  });

  test('should have working floating menu links', async ({ page }) => {
    // Navigate to a post to trigger floating menu
    await page.goto(SAMPLE_POSTS.en[0]);

    // Scroll down to trigger floating menu
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(1000);  // Wait for floating menu to appear

    // Test floating menu links (if present)
    const floatingMenu = page.locator('.floating-menu, [class*="float"], nav[class*="sticky"]');

    if (await floatingMenu.count() > 0) {
      const menuLinks = floatingMenu.locator('a[href^="/"]');
      const count = await menuLinks.count();

      // Test first 5 links
      for (let i = 0; i < Math.min(count, 5); i++) {
        const link = menuLinks.nth(i);
        const href = await link.getAttribute('href');

        if (href) {
          const response = await page.goto(href);
          expect(response?.status(), `Floating menu link failed: ${href}`).toBe(200);
        }
      }
    }
  });

  test('should warn about broken external links (non-blocking)', async ({ page }) => {
    const warnings = [];

    // Sample 2 posts
    const samplePosts = [SAMPLE_POSTS.en[0], SAMPLE_POSTS.ko[0]];

    for (const postUrl of samplePosts) {
      await page.goto(postUrl);

      // Find external links in content
      const externalLinks = page.locator('article a[href^="http"], .content a[href^="http"]');
      const count = await externalLinks.count();

      // Test first 3 external links per post
      for (let i = 0; i < Math.min(count, 3); i++) {
        const link = externalLinks.nth(i);
        const href = await link.getAttribute('href');

        if (href) {
          try {
            const response = await page.goto(href, { timeout: 10000 });

            if (response && response.status() >= 400) {
              warnings.push({
                post: postUrl,
                externalUrl: href,
                status: response.status(),
              });
            }

            // Go back to post
            await page.goto(postUrl);
          } catch (error) {
            warnings.push({
              post: postUrl,
              externalUrl: href,
              status: 'timeout/error',
            });

            // Try to recover by going back to post
            try {
              await page.goto(postUrl);
            } catch {
              // If recovery fails, skip to next post
              break;
            }
          }
        }
      }
    }

    // Log warnings but don't fail
    if (warnings.length > 0) {
      console.warn('⚠️  External link warnings (non-blocking):');
      warnings.forEach(w => {
        console.warn(`  - Post: ${w.post}`);
        console.warn(`    External: ${w.externalUrl}`);
        console.warn(`    Status: ${w.status}`);
      });
    }
  });
});
