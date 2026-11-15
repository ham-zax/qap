import { defineConfig } from '@playwright/test'

const webBaseUrl =
  process.env.QAP_E2E_WEB_BASE_URL ?? 'http://127.0.0.1:48766'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  reporter: 'line',
  use: {
    baseURL: webBaseUrl,
    channel: 'chrome',
    trace: 'retain-on-failure',
  },
})
