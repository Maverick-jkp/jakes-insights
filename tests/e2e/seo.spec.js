// @ts-check
const { test, expect } = require('@playwright/test');
const { SAMPLE_POSTS, SEO_PATTERNS } = require('./helpers/test-data.js');
const {
  validateOpenGraph,
  validateTwitterCard,
  validateJSONLD,
  validateCanonical,
  validateHreflang,
  extractMetaTags,
} = require('./helpers/seo-validator.js');

test.describe('SEO Validation Tests', () => {
  test('should have valid meta description tags', async ({ page }) => {
    const errors = [];

    // Test 2 posts per language
    for (const lang of ['en', 'ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 2);

      for (const postUrl of posts) {
        await page.goto(postUrl);

        const description = await page.locator('meta[name="description"]').getAttribute('content');

        if (!description) {
          errors.push(`${postUrl}: Missing meta description`);
        } else if (description.length < SEO_PATTERNS.description.minLength) {
          errors.push(`${postUrl}: Description too short (${description.length} chars, min ${SEO_PATTERNS.description.minLength})`);
        } else if (description.length > SEO_PATTERNS.description.maxLength) {
          errors.push(`${postUrl}: Description too long (${description.length} chars, max ${SEO_PATTERNS.description.maxLength})`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Meta description issues found:\n${errors.join('\n')}`);
    }
  });

  test('should have valid Open Graph tags', async ({ page }) => {
    const errors = [];

    // Test 2 posts per language
    for (const lang of ['en', 'ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 2);

      for (const postUrl of posts) {
        await page.goto(postUrl);

        const ogValidation = await validateOpenGraph(page);

        if (!ogValidation.isValid) {
          errors.push(`${postUrl}:\n  ${ogValidation.errors.join('\n  ')}`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Open Graph validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have valid Twitter Card tags', async ({ page }) => {
    const errors = [];

    // Test 2 posts per language
    for (const lang of ['en', 'ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 2);

      for (const postUrl of posts) {
        await page.goto(postUrl);

        const twitterValidation = await validateTwitterCard(page);

        if (!twitterValidation.isValid) {
          errors.push(`${postUrl}:\n  ${twitterValidation.errors.join('\n  ')}`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Twitter Card validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have valid JSON-LD structured data (BlogPosting)', async ({ page }) => {
    const errors = [];

    // Test 2 posts per language
    for (const lang of ['en', 'ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 2);

      for (const postUrl of posts) {
        await page.goto(postUrl);

        const jsonldValidation = await validateJSONLD(page, 'BlogPosting');

        if (!jsonldValidation.isValid) {
          errors.push(`${postUrl}: ${jsonldValidation.error}`);
        } else {
          // Verify BlogPosting has required fields
          const data = jsonldValidation.data;
          if (!data.headline) errors.push(`${postUrl}: Missing headline in BlogPosting`);
          if (!data.image) errors.push(`${postUrl}: Missing image in BlogPosting`);
          if (!data.datePublished) errors.push(`${postUrl}: Missing datePublished in BlogPosting`);
          if (!data.author) errors.push(`${postUrl}: Missing author in BlogPosting`);
          if (!data.publisher) errors.push(`${postUrl}: Missing publisher in BlogPosting`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`JSON-LD validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have valid canonical URLs', async ({ page }) => {
    const errors = [];

    // Test 2 posts per language
    for (const lang of ['en', 'ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 2);

      for (const postUrl of posts) {
        await page.goto(postUrl);

        const canonicalValidation = await validateCanonical(page);

        if (!canonicalValidation.isValid) {
          errors.push(`${postUrl}: ${canonicalValidation.error}`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Canonical URL validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have valid hreflang tags for multilingual content', async ({ page }) => {
    const errors = [];

    // Test 2 posts per language
    for (const lang of ['en', 'ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 2);

      for (const postUrl of posts) {
        await page.goto(postUrl);

        const hreflangValidation = await validateHreflang(page);

        if (!hreflangValidation.isValid) {
          errors.push(`${postUrl}:\n  ${hreflangValidation.errors.join('\n  ')}`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Hreflang validation failed:\n${errors.join('\n')}`);
    }
  });

  test('should have author meta tag', async ({ page }) => {
    const errors = [];

    // Test 2 posts per language
    for (const lang of ['en', 'ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 2);

      for (const postUrl of posts) {
        await page.goto(postUrl);

        const author = await page.locator('meta[name="author"]').getAttribute('content');

        if (!author) {
          errors.push(`${postUrl}: Missing author meta tag`);
        } else if (author !== 'Jake Park') {
          errors.push(`${postUrl}: Author should be "Jake Park", got "${author}"`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Author meta tag issues:\n${errors.join('\n')}`);
    }
  });

  test('should have valid title tags', async ({ page }) => {
    const errors = [];

    // Test 2 posts per language
    for (const lang of ['en', 'ko', 'ja']) {
      const posts = SAMPLE_POSTS[lang].slice(0, 2);

      for (const postUrl of posts) {
        await page.goto(postUrl);

        const title = await page.title();

        if (!title) {
          errors.push(`${postUrl}: Missing title tag`);
        } else if (title.length < SEO_PATTERNS.title.minLength) {
          errors.push(`${postUrl}: Title too short (${title.length} chars, min ${SEO_PATTERNS.title.minLength})`);
        } else if (title.length > SEO_PATTERNS.title.maxLength) {
          errors.push(`${postUrl}: Title too long (${title.length} chars, max ${SEO_PATTERNS.title.maxLength})`);
        }
      }
    }

    if (errors.length > 0) {
      throw new Error(`Title tag issues:\n${errors.join('\n')}`);
    }
  });

  test('should extract and validate all meta tags', async ({ page }) => {
    // Test one post per language
    for (const lang of ['en', 'ko', 'ja']) {
      const postUrl = SAMPLE_POSTS[lang][0];
      await page.goto(postUrl);

      const metaTags = await extractMetaTags(page);

      // Should have at least these essential meta tags
      const requiredMetaNames = ['description', 'author', 'twitter:card', 'twitter:title'];
      const requiredProperties = ['og:type', 'og:url', 'og:title', 'og:description', 'og:image'];

      const metaNames = metaTags.map(m => m.name);

      for (const required of requiredMetaNames) {
        expect(metaNames, `Missing meta tag: ${required} in ${postUrl}`).toContain(required);
      }

      for (const required of requiredProperties) {
        expect(metaNames, `Missing meta property: ${required} in ${postUrl}`).toContain(required);
      }
    }
  });
});
