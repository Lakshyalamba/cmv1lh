import { expect, test } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
const out = resolve(process.env.WIND_SCREENSHOT_DIR ?? '../docs/screenshots');
const fmt = (n: number | null, signed = false) => n === null ? '—' : `${signed && n > 0 ? '+' : ''}${new Intl.NumberFormat('en-GB', { maximumFractionDigits: 1 }).format(n)}`;

test('all 31 decision selections match real backend metrics, observations and chart coverage', async ({ page, request }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByTestId('metric-mae')).toBeVisible();
  const dates = (await (await request.get('/api/decisions')).json()).decisions;
  expect(dates).toHaveLength(31);
  for (const d of dates) {
    const day = d.decision_date;
    await page.getByLabel('Decision date', { exact: true }).selectOption(day);
    await expect(page.getByRole('region', { name: 'Selected decision context' })).toContainText(new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/London' }).format(new Date(day + 'T12:00:00Z')));
    await expect(page.getByTestId('metric-mae')).toBeVisible();
    const metrics = await (await request.get(`/api/decisions/${day}/metrics`)).json();
    for (const [label, key, signed] of [['mae', 'mae_mw', false], ['rmse', 'rmse_mw', false], ['bias', 'bias_mw', true]] as const) {
      await expect(page.getByTestId(`metric-${label}`)).toHaveText(`${fmt(metrics.accuracy[key], signed)} MW`);
    }
    await expect(page.getByTestId('metric-count')).toHaveText(`${metrics.accuracy.observation_count} / ${metrics.coverage.expected_hourly_targets}`);
    await expect(page.locator('.generation-panel .recharts-line-dots .recharts-dot')).toHaveCount(metrics.coverage.forecast_observations);
    await page.getByRole('button', { name: 'View observations +' }).click();
    const comparisons = await (await request.get(`/api/decisions/${day}/comparisons`)).json();
    const table = await page.locator('tbody tr').evaluateAll(rows => rows.map(r => Array.from(r.querySelectorAll('td')).slice(0, 3).map(c => c.textContent)));
    expect(table).toEqual(comparisons.observations.map((r: { forecast_mw: number | null; actual_mw: number | null; error_mw: number | null }) => [fmt(r.forecast_mw), fmt(r.actual_mw), fmt(r.error_mw, true)]));
  }
  expect(errors).toEqual([]);
});

test('desktop and mobile render real charts without page overflow, with keyboard and tooltip access', async ({ page }) => {
  await mkdir(out, { recursive: true });
  await page.goto('/');
  await expect(page.getByTestId('metric-mae')).toBeVisible();
  await expect(page.locator('.generation-panel svg.recharts-surface[role="application"]')).toBeVisible();
  await page.screenshot({ path: `${out}/dashboard-desktop.png`, fullPage: true });
  await page.locator('.generation-panel .recharts-line-dots .recharts-dot').first().hover();
  await expect(page.locator('.chart-tooltip')).toContainText('18,781');
  await page.getByLabel('Decision date', { exact: true }).focus();
  await expect(page.getByLabel('Decision date', { exact: true })).toBeFocused();
  await page.getByRole('button', { name: 'Next decision date' }).click();
  await expect(page.getByLabel('Decision date', { exact: true })).toHaveValue('2026-01-02');
  await expect(page.getByTestId('metric-mae')).toBeVisible();
  await page.getByRole('button', { name: 'Previous decision date' }).click();
  await expect(page.getByTestId('metric-mae')).toHaveText('3,070.4 MW');
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('.generation-panel svg.recharts-surface[role="application"]')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `${out}/dashboard-mobile.png`, fullPage: true });
  await page.getByRole('button', { name: 'View observations +' }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.getByRole('table')).toBeVisible();
  await page.setViewportSize({ width: 320, height: 700 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('loading, backend failure, retry, and empty states', async ({ page }) => {
  await page.route('**/api/**', async route => {
    await new Promise(resolve => setTimeout(resolve, 350));
    await route.fulfill({ status: 503, json: { error: { code: 'data_unavailable', message: 'Validated data is unavailable.' } } });
  });
  await page.goto('/');
  await expect(page.getByRole('status', { name: 'Loading dashboard' })).toBeVisible();
  await expect(page.getByRole('alert')).toContainText('Validated data is unavailable.');
  await expect(page.getByTestId('metric-mae')).toHaveCount(0);
  await page.unroute('**/api/**');
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.getByTestId('metric-mae')).toBeVisible();
  await page.route('**/api/decisions', async route => {
    const response = await route.fetch();
    const body = await response.json();
    await route.fulfill({ json: { ...body, decisions: [] } });
  });
  await page.reload();
  await expect(page.getByText('No decision data available', { exact: true })).toBeVisible();
});

test('rapid selection cannot replace the newest date with an older response', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('metric-mae')).toBeVisible();
  await page.route('**/api/decisions/2026-01-02/**', async route => {
    await new Promise(resolve => setTimeout(resolve, 500));
    await route.continue().catch(() => {});
  });
  await page.getByLabel('Decision date', { exact: true }).selectOption('2026-01-02');
  await page.getByLabel('Decision date', { exact: true }).selectOption('2026-01-31');
  await expect(page.getByRole('region', { name: 'Selected decision context' })).toContainText('31 January 2026');
  await page.getByRole('button', { name: 'View observations +' }).click();
  await expect(page.getByRole('table')).toContainText('1 February 2026');
  await expect(page.getByRole('button', { name: 'Next decision date' })).toBeDisabled();
});
