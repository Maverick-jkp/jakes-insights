// SEO validation helper functions for Playwright tests

/**
 * Validate Open Graph tags on a page
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<{isValid: boolean, tags: object, errors: string[]}>}
 */
export async function validateOpenGraph(page) {
  const errors = [];

  const ogTags = {
    type: await page.locator('meta[property="og:type"]').getAttribute('content'),
    url: await page.locator('meta[property="og:url"]').getAttribute('content'),
    title: await page.locator('meta[property="og:title"]').getAttribute('content'),
    description: await page.locator('meta[property="og:description"]').getAttribute('content'),
    image: await page.locator('meta[property="og:image"]').getAttribute('content'),
  };

  // Validate required fields
  if (!ogTags.type) errors.push('og:type is missing');
  if (!ogTags.url) errors.push('og:url is missing');
  if (!ogTags.title) errors.push('og:title is missing');
  if (!ogTags.description) errors.push('og:description is missing');
  if (!ogTags.image) errors.push('og:image is missing');

  // Validate image URL format
  if (ogTags.image && !/^https?:\/\/.+\.(jpg|png|svg)$/i.test(ogTags.image)) {
    errors.push(`og:image has invalid format: ${ogTags.image}`);
  }

  return {
    isValid: errors.length === 0,
    tags: ogTags,
    errors,
  };
}

/**
 * Validate Twitter Card tags on a page
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<{isValid: boolean, tags: object, errors: string[]}>}
 */
export async function validateTwitterCard(page) {
  const errors = [];

  const twitterTags = {
    card: await page.locator('meta[name="twitter:card"]').getAttribute('content'),
    title: await page.locator('meta[name="twitter:title"]').getAttribute('content'),
    description: await page.locator('meta[name="twitter:description"]').getAttribute('content'),
    image: await page.locator('meta[name="twitter:image"]').getAttribute('content'),
    creator: await page.locator('meta[name="twitter:creator"]').getAttribute('content'),
  };

  // Validate required fields
  if (!twitterTags.card) errors.push('twitter:card is missing');
  if (!twitterTags.title) errors.push('twitter:title is missing');
  if (!twitterTags.description) errors.push('twitter:description is missing');
  if (!twitterTags.image) errors.push('twitter:image is missing');

  return {
    isValid: errors.length === 0,
    tags: twitterTags,
    errors,
  };
}

/**
 * Validate JSON-LD structured data on a page
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} schemaType - Expected @type value (e.g., 'BlogPosting')
 * @returns {Promise<{isValid: boolean, data: object|null, error: string|null}>}
 */
export async function validateJSONLD(page, schemaType) {
  try {
    const scripts = await page.locator('script[type="application/ld+json"]').allTextContents();

    for (const script of scripts) {
      try {
        const data = JSON.parse(script);

        if (data['@type'] === schemaType) {
          // Validate required fields based on schema type
          if (schemaType === 'BlogPosting') {
            const requiredFields = ['headline', 'image', 'datePublished', 'author', 'publisher'];
            const missingFields = requiredFields.filter(field => !data[field]);

            if (missingFields.length > 0) {
              return {
                isValid: false,
                data,
                error: `Missing required fields: ${missingFields.join(', ')}`,
              };
            }
          }

          return { isValid: true, data, error: null };
        }
      } catch (parseError) {
        return {
          isValid: false,
          data: null,
          error: `JSON parse error: ${parseError.message}`,
        };
      }
    }

    return {
      isValid: false,
      data: null,
      error: `No ${schemaType} schema found`,
    };
  } catch (error) {
    return {
      isValid: false,
      data: null,
      error: `Failed to extract JSON-LD: ${error.message}`,
    };
  }
}

/**
 * Extract all meta tags from a page
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<{name: string, content: string}[]>}
 */
export async function extractMetaTags(page) {
  return await page.evaluate(() => {
    const metas = Array.from(document.querySelectorAll('meta'));
    return metas.map(meta => ({
      name: meta.getAttribute('name') || meta.getAttribute('property') || '',
      content: meta.getAttribute('content') || '',
    })).filter(meta => meta.name && meta.content);
  });
}

/**
 * Validate canonical URL on a page
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<{isValid: boolean, canonical: string|null, currentUrl: string, error: string|null}>}
 */
export async function validateCanonical(page) {
  const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
  const currentUrl = page.url();

  if (!canonical) {
    return {
      isValid: false,
      canonical: null,
      currentUrl,
      error: 'Canonical link tag is missing',
    };
  }

  // Check for duplicate canonical tags
  const canonicalCount = await page.locator('link[rel="canonical"]').count();
  if (canonicalCount > 1) {
    return {
      isValid: false,
      canonical,
      currentUrl,
      error: `Multiple canonical tags found (${canonicalCount})`,
    };
  }

  return {
    isValid: true,
    canonical,
    currentUrl,
    error: null,
  };
}

/**
 * Validate hreflang tags for multilingual content
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Promise<{isValid: boolean, hreflangs: Array<{lang: string, href: string}>, errors: string[]}>}
 */
export async function validateHreflang(page) {
  const errors = [];

  const hreflangs = await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll('link[rel="alternate"]'));
    return links
      .filter(link => link.getAttribute('hreflang'))
      .map(link => ({
        lang: link.getAttribute('hreflang'),
        href: link.getAttribute('href'),
      }));
  });

  if (hreflangs.length === 0) {
    // This is OK for posts that aren't translated
    return {
      isValid: true,
      hreflangs: [],
      errors: [],
    };
  }

  // Check for x-default
  const hasXDefault = hreflangs.some(h => h.lang === 'x-default');
  if (!hasXDefault && hreflangs.length > 0) {
    errors.push('Missing hreflang="x-default" tag');
  }

  // Validate language codes
  const validLangCodes = ['en-us', 'ko-kr', 'ja-jp', 'x-default'];
  hreflangs.forEach(h => {
    if (!validLangCodes.includes(h.lang.toLowerCase())) {
      errors.push(`Invalid hreflang code: ${h.lang}`);
    }
  });

  return {
    isValid: errors.length === 0,
    hreflangs,
    errors,
  };
}
