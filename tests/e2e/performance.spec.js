// @ts-check
const { test, expect } = require('@playwright/test');
const { SAMPLE_POSTS, PERFORMANCE_BUDGETS } = require('./helpers/test-data.js');

test.describe('Performance Tests (Core Web Vitals)', () => {
  test('should meet LCP (Largest Contentful Paint) budget', async ({ page }) => {
    const warnings = [];
    const failures = [];

    // Test 1 post per language
    for (const lang of ['ko', 'ja']) {
      const postUrl = SAMPLE_POSTS[lang][0];

      await page.goto(postUrl, { waitUntil: 'networkidle', timeout: 30000 });

      // Measure LCP using PerformanceObserver
      const lcp = await page.evaluate(() => {
        return new Promise((resolve) => {
          let lcpValue = 0;

          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            lcpValue = lastEntry.renderTime || lastEntry.loadTime;
          });

          observer.observe({ type: 'largest-contentful-paint', buffered: true });

          // Wait a bit for LCP to stabilize
          setTimeout(() => {
            observer.disconnect();
            resolve(lcpValue);
          }, 3000);
        });
      });

      if (lcp > PERFORMANCE_BUDGETS.lcp.needsImprovement) {
        failures.push(`${postUrl}: LCP ${lcp.toFixed(0)}ms (> ${PERFORMANCE_BUDGETS.lcp.needsImprovement}ms)`);
      } else if (lcp > PERFORMANCE_BUDGETS.lcp.good) {
        warnings.push(`${postUrl}: LCP ${lcp.toFixed(0)}ms (> ${PERFORMANCE_BUDGETS.lcp.good}ms but < ${PERFORMANCE_BUDGETS.lcp.needsImprovement}ms)`);
      }
    }

    // Log warnings
    if (warnings.length > 0) {
      console.warn('⚠️  LCP warnings (needs improvement):');
      warnings.forEach(w => console.warn(`  ${w}`));
    }

    // Fail on critical issues
    if (failures.length > 0) {
      throw new Error(`LCP budget exceeded:\n${failures.join('\n')}`);
    }
  });

  test('should meet FCP (First Contentful Paint) budget', async ({ page }) => {
    const warnings = [];
    const failures = [];

    // Test 1 post per language
    for (const lang of ['en', 'ko', 'ja']) {
      const postUrl = SAMPLE_POSTS[lang][0];

      await page.goto(postUrl, { waitUntil: 'domcontentloaded' });

      // Measure FCP
      const fcp = await page.evaluate(() => {
        const fcpEntry = performance.getEntriesByType('paint')
          .find(entry => entry.name === 'first-contentful-paint');
        return fcpEntry ? fcpEntry.startTime : 0;
      });

      if (fcp > PERFORMANCE_BUDGETS.fcp.needsImprovement) {
        failures.push(`${postUrl}: FCP ${fcp.toFixed(0)}ms (> ${PERFORMANCE_BUDGETS.fcp.needsImprovement}ms)`);
      } else if (fcp > PERFORMANCE_BUDGETS.fcp.good) {
        warnings.push(`${postUrl}: FCP ${fcp.toFixed(0)}ms (> ${PERFORMANCE_BUDGETS.fcp.good}ms but < ${PERFORMANCE_BUDGETS.fcp.needsImprovement}ms)`);
      }
    }

    // Log warnings
    if (warnings.length > 0) {
      console.warn('⚠️  FCP warnings (needs improvement):');
      warnings.forEach(w => console.warn(`  ${w}`));
    }

    // Fail on critical issues
    if (failures.length > 0) {
      throw new Error(`FCP budget exceeded:\n${failures.join('\n')}`);
    }
  });

  test('should meet CLS (Cumulative Layout Shift) budget', async ({ page }) => {
    const warnings = [];
    const failures = [];

    // Test 1 post per language
    for (const lang of ['ko', 'ja']) {
      const postUrl = SAMPLE_POSTS[lang][0];

      await page.goto(postUrl, { waitUntil: 'networkidle', timeout: 30000 });

      // Measure CLS
      const cls = await page.evaluate(() => {
        return new Promise((resolve) => {
          let clsValue = 0;

          const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (!entry.hadRecentInput) {
                clsValue += entry.value;
              }
            }
          });

          observer.observe({ type: 'layout-shift', buffered: true });

          // Wait for layout shifts to settle
          setTimeout(() => {
            observer.disconnect();
            resolve(clsValue);
          }, 3000);
        });
      });

      if (cls > PERFORMANCE_BUDGETS.cls.needsImprovement) {
        failures.push(`${postUrl}: CLS ${cls.toFixed(3)} (> ${PERFORMANCE_BUDGETS.cls.needsImprovement})`);
      } else if (cls > PERFORMANCE_BUDGETS.cls.good) {
        warnings.push(`${postUrl}: CLS ${cls.toFixed(3)} (> ${PERFORMANCE_BUDGETS.cls.good} but < ${PERFORMANCE_BUDGETS.cls.needsImprovement})`);
      }
    }

    // Log warnings
    if (warnings.length > 0) {
      console.warn('⚠️  CLS warnings (needs improvement):');
      warnings.forEach(w => console.warn(`  ${w}`));
    }

    // Fail on critical issues
    if (failures.length > 0) {
      throw new Error(`CLS budget exceeded:\n${failures.join('\n')}`);
    }
  });

  test('should be interactive within 5 seconds', async ({ page }) => {
    const failures = [];

    // Test 1 post per language
    for (const lang of ['en', 'ko', 'ja']) {
      const postUrl = SAMPLE_POSTS[lang][0];

      const startTime = Date.now();
      await page.goto(postUrl, { waitUntil: 'domcontentloaded' });

      // Wait for page to be interactive (can click links)
      await page.waitForSelector('a', { state: 'visible', timeout: 5000 });

      const interactiveTime = Date.now() - startTime;

      if (interactiveTime > 5000) {
        failures.push(`${postUrl}: TTI ${interactiveTime}ms (> 5000ms)`);
      }
    }

    if (failures.length > 0) {
      throw new Error(`Time to Interactive exceeded:\n${failures.join('\n')}`);
    }
  });

  test('should load images efficiently', async ({ page }) => {
    const warnings = [];

    // Test 1 post per language
    for (const lang of ['en', 'ko', 'ja']) {
      const postUrl = SAMPLE_POSTS[lang][0];

      await page.goto(postUrl);

      // Check for lazy loading on images
      const images = page.locator('article img, .content img');
      const count = await images.count();

      if (count > 0) {
        for (let i = 0; i < Math.min(count, 5); i++) {
          const img = images.nth(i);
          const loading = await img.getAttribute('loading');

          // Images should have loading="lazy" for performance
          if (!loading || loading !== 'lazy') {
            const src = await img.getAttribute('src');
            warnings.push(`${postUrl}: Image without lazy loading: ${src}`);
          }
        }
      }
    }

    // Log warnings but don't fail
    if (warnings.length > 0) {
      console.warn('⚠️  Image loading warnings:');
      warnings.forEach(w => console.warn(`  ${w}`));
    }
  });

  test('should have reasonable page weight', async ({ page }) => {
    const warnings = [];

    // Test 1 post per language
    for (const lang of ['en', 'ko', 'ja']) {
      const postUrl = SAMPLE_POSTS[lang][0];

      // Track all network requests
      const resourceSizes = {
        total: 0,
        images: 0,
        scripts: 0,
        styles: 0,
      };

      page.on('response', async (response) => {
        const contentType = response.headers()['content-type'] || '';
        const contentLength = parseInt(response.headers()['content-length'] || '0', 10);

        resourceSizes.total += contentLength;

        if (contentType.includes('image/')) {
          resourceSizes.images += contentLength;
        } else if (contentType.includes('javascript')) {
          resourceSizes.scripts += contentLength;
        } else if (contentType.includes('css')) {
          resourceSizes.styles += contentLength;
        }
      });

      await page.goto(postUrl, { waitUntil: 'networkidle' });

      // Warn if total page weight > 3MB
      if (resourceSizes.total > 3 * 1024 * 1024) {
        warnings.push(`${postUrl}: Page weight ${(resourceSizes.total / 1024 / 1024).toFixed(2)}MB (> 3MB)`);
      }

      // Warn if images > 2MB
      if (resourceSizes.images > 2 * 1024 * 1024) {
        warnings.push(`${postUrl}: Images ${(resourceSizes.images / 1024 / 1024).toFixed(2)}MB (> 2MB)`);
      }
    }

    // Log warnings but don't fail
    if (warnings.length > 0) {
      console.warn('⚠️  Page weight warnings:');
      warnings.forEach(w => console.warn(`  ${w}`));
    }
  });
});
