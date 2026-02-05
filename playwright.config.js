// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright E2E Test Configuration for Jake's Tech Insights
 *
 * Tests homepage loading, image rendering, and multilingual navigation
 */
module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:1313',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: '/opt/homebrew/bin/hugo server -D --bind 0.0.0.0',
    url: 'http://localhost:1313',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
