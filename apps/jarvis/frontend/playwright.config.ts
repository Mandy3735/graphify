import { defineConfig } from '@playwright/test';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  testDir: 'tests/browser',
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  use: {
    baseURL: 'http://127.0.0.1:8765',
    headless: true,
    trace: 'off',
    launchOptions: process.env.JARVIS_CHROMIUM
      ? { executablePath: process.env.JARVIS_CHROMIUM }
      : {},
  },
  webServer: {
    command: '../../../.venv/bin/python tests/server.py',
    cwd: fileURLToPath(new URL('.', import.meta.url)),
    url: 'http://127.0.0.1:8765/health',
    reuseExistingServer: false,
    timeout: 30000,
  },
  reporter: 'list',
});
