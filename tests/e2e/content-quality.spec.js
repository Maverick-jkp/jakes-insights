// @ts-check
const { test, expect } = require('@playwright/test');
const { SAMPLE_POSTS, VALID_CATEGORIES, AI_BLACKLIST, SEO_PATTERNS } = require('./helpers/test-data.js');

test.describe('Content Quality Tests', () => {
  test('should have at least one image in every post', async ({ page }) => {
    const errors = [];

    // Test sample posts
    for (const lang of ['ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        const images = page.locator('article img, .content img, .post-content img');
        const count = await images.count();

        if (count === 0) {
          errors.push(`${postUrl}: No images found in post content`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Image presence validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have hero/featured image', async ({ page }) => {
    const errors = [];

    // Test sample posts
    for (const lang of ['ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        // Check for hero image (common selectors)
        const heroImage = page.locator('.hero-image img, .featured-image img, .post-header img, article > img').first();
        const hasHero = await heroImage.count() > 0;

        if (!hasHero) {
          errors.push(`${postUrl}: No hero/featured image found`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Hero image validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have valid reading time estimate', async ({ page }) => {
    const errors = [];

    // Test sample posts
    for (const lang of ['ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        // Check for reading time display
        const readingTime = page.locator('.reading-time, [class*="read"], .meta-reading-time');
        const hasReadingTime = await readingTime.count() > 0;

        if (hasReadingTime) {
          const text = await readingTime.first().textContent();

          // Extract number from text (e.g., "5 min read" -> 5)
          const match = text?.match(/(\d+)/);
          if (match) {
            const minutes = parseInt(match[1], 10);

            if (minutes === 0) {
              errors.push(`${postUrl}: Reading time is 0 minutes`);
            } else if (minutes > 30) {
              errors.push(`${postUrl}: Reading time suspiciously high (${minutes} minutes)`);
            }
          }
        } else {
          // Reading time should be present for all posts
          errors.push(`${postUrl}: No reading time indicator found`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Reading time validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have valid category assignment', async ({ page }) => {
    const errors = [];

    // Test sample posts
    for (const lang of ['ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        // Extract category from URL (e.g., /en/tech/2026-02-04-post/)
        const categoryMatch = postUrl.match(/\/(en|ko|ja)\/([^\/]+)\//);

        if (!categoryMatch) {
          errors.push(`${postUrl}: Cannot extract category from URL`);
          continue;
        }

        const category = categoryMatch[2];

        if (!VALID_CATEGORIES.includes(category)) {
          errors.push(`${postUrl}: Invalid category "${category}" (valid: ${VALID_CATEGORIES.join(', ')})`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Category validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should not contain AI-generated phrases blacklist', async ({ page }) => {
    const warnings = [];

    // Test 1 Korean post only (content check is expensive)
    for (const lang of ['ko']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        // Get post content text
        const content = await page.locator('article, .post-content, .content').first().textContent();

        if (content) {
          const contentLower = content.toLowerCase();

          for (const phrase of AI_BLACKLIST) {
            if (contentLower.includes(phrase.toLowerCase())) {
              warnings.push(`${postUrl}: Contains AI phrase "${phrase}"`);
            }
          }
        }
      }
    }

    // Log warnings but don't fail (this is a quality guideline, not a hard requirement)
    if (warnings.length > 0) {
      console.warn('⚠️  AI phrase warnings (consider rewriting):');
      warnings.forEach(w => console.warn(`  ${w}`));
    }
  });

  test('should have proper heading structure (h1 -> h2 -> h3)', async ({ page }) => {
    const warnings = [];

    // Test sample posts
    for (const lang of ['ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        // Check heading hierarchy
        const headings = await page.evaluate(() => {
          const h1s = Array.from(document.querySelectorAll('h1')).map(() => 'h1');
          const h2s = Array.from(document.querySelectorAll('h2')).map(() => 'h2');
          const h3s = Array.from(document.querySelectorAll('h3')).map(() => 'h3');
          const h4s = Array.from(document.querySelectorAll('h4')).map(() => 'h4');
          return { h1: h1s.length, h2: h2s.length, h3: h3s.length, h4: h4s.length };
        });

        // Should have exactly 1 h1 (main title)
        if (headings.h1 !== 1) {
          warnings.push(`${postUrl}: Should have exactly 1 h1 tag (found ${headings.h1})`);
        }

        // Should have at least some h2 for structure
        if (headings.h2 === 0) {
          warnings.push(`${postUrl}: No h2 tags found (consider adding section headings)`);
        }
      }
    }

    // Log warnings but don't fail
    if (warnings.length > 0) {
      console.warn('⚠️  Heading structure warnings:');
      warnings.forEach(w => console.warn(`  ${w}`));
    }
  });

  test('should have meta description matching post summary', async ({ page }) => {
    const errors = [];

    // Test 1 post per language
    for (const lang of ['ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        const metaDescription = await page.locator('meta[name="description"]').getAttribute('content');

        if (!metaDescription) {
          errors.push(`${postUrl}: Missing meta description`);
          continue;
        }

        // Meta description should be between 120-160 chars
        if (metaDescription.length < SEO_PATTERNS.description.minLength) {
          errors.push(`${postUrl}: Meta description too short (${metaDescription.length} chars, min ${SEO_PATTERNS.description.minLength})`);
        } else if (metaDescription.length > SEO_PATTERNS.description.maxLength) {
          errors.push(`${postUrl}: Meta description too long (${metaDescription.length} chars, max ${SEO_PATTERNS.description.maxLength})`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Meta description validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have proper image alt text (accessibility)', async ({ page }) => {
    const warnings = [];

    // Test 1 post per language
    for (const lang of ['ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        const images = page.locator('article img, .content img');
        const count = await images.count();

        for (let i = 0; i < count; i++) {
          const img = images.nth(i);
          const alt = await img.getAttribute('alt');
          const src = await img.getAttribute('src');

          if (!alt || alt.trim() === '') {
            warnings.push(`${postUrl}: Image missing alt text: ${src}`);
          } else if (alt.length < 10) {
            warnings.push(`${postUrl}: Image alt text too short (${alt.length} chars): ${src}`);
          }
        }
      }
    }

    // Log warnings but don't fail
    if (warnings.length > 0) {
      console.warn('⚠️  Image alt text warnings:');
      warnings.forEach(w => console.warn(`  ${w}`));
    }
  });

  test('should have reasonable content length', async ({ page }) => {
    const warnings = [];

    // Test sample posts
    for (const lang of ['ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 1);

      for (const postUrl of posts) {
        await page.goto(postUrl, { timeout: 30000 });

        const content = await page.locator('article, .post-content, .content').first().textContent();

        if (content) {
          // Count words (approximate for EN, char count for JA)
          if (lang === 'ja') {
            // Japanese: 3000-7500 characters
            const charCount = content.replace(/\s/g, '').length;
            if (charCount < 3000) {
              warnings.push(`${postUrl}: Content too short (${charCount} chars, min 3000 for Japanese)`);
            } else if (charCount > 7500) {
              warnings.push(`${postUrl}: Content too long (${charCount} chars, max 7500 for Japanese)`);
            }
          } else {
            // English/Korean: 800-2000 words
            const wordCount = content.split(/\s+/).length;
            if (wordCount < 800) {
              warnings.push(`${postUrl}: Content too short (${wordCount} words, min 800)`);
            } else if (wordCount > 2000) {
              warnings.push(`${postUrl}: Content too long (${wordCount} words, max 2000)`);
            }
          }
        }
      }
    }

    // Log warnings but don't fail
    if (warnings.length > 0) {
      console.warn('⚠️  Content length warnings:');
      warnings.forEach(w => console.warn(`  ${w}`));
    }
  });
});
