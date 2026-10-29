import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, timeout: 90_000,
  reporter: [['list']], use: { channel: process.env.PLAYWRIGHT_CHANNEL ?? 'chrome', baseURL: 'http://127.0.0.1:5173', viewport: { width: 1440, height: 1000 } },
  webServer: [
    { command: '../.venv/bin/python -m uvicorn backend.main:app --app-dir .. --host 127.0.0.1 --port 8000', url: 'http://127.0.0.1:8000/openapi.json', reuseExistingServer: true },
    { command: 'npm run dev', url: 'http://127.0.0.1:5173', reuseExistingServer: true },
  ],
});
