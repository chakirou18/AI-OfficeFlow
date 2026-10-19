import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  workers: 1,
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://127.0.0.1:8080',
    browserName: 'chromium',
    // Use an installed Edge if configured; otherwise Playwright Chromium.
    channel: process.env.BROWSER_CHANNEL,
    headless: true,
    screenshot: 'only-on-failure',
  },
})
