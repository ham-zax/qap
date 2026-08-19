import { expect, test } from '@playwright/test'

import {
  fixtureState,
  operationIdFromHref,
  waitForOperation,
} from './slice4-helpers'

test('Slice 4 discovery and basket workflow stays artifact-authoritative', async ({
  page,
  request,
}) => {
  test.setTimeout(180_000)
  const fixture = await fixtureState(request)

  await page.goto('/scanner')
  await page.getByLabel('UTC as-of').fill('2023-12-31T00:00:00Z')
  await page.getByRole('checkbox', { name: 'short' }).uncheck()
  await page.getByRole('checkbox', { name: 'swing' }).check()
  await page.getByRole('button', { name: 'Run scan' }).click()

  const scanOperationLink = page.getByRole('link', { name: /^Track / })
  await expect(scanOperationLink).toBeVisible()
  const scanOperationId = operationIdFromHref(
    await scanOperationLink.getAttribute('href'),
  )
  const scanOperation = await waitForOperation(request, scanOperationId)
  const discoveredScanId = String(scanOperation.result?.scan_id ?? '')
  expect(discoveredScanId).not.toBe('')
  expect(discoveredScanId).not.toBe(fixture.baseline_scan_id)

  await page.goto(`/scanner/${discoveredScanId}`)
  await expect(
    page.getByRole('heading', { name: 'Candidate trials' }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Point-in-time universe' }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Generate momentum' }).click()

  const momentumOperationLink = page.getByRole('link', { name: /^Track / })
  await expect(momentumOperationLink).toBeVisible()
  const momentumOperationId = operationIdFromHref(
    await momentumOperationLink.getAttribute('href'),
  )
  const momentumOperation = await waitForOperation(request, momentumOperationId)
  expect(momentumOperation.result?.source_scan_id).toBe(discoveredScanId)
  expect(String(momentumOperation.result?.momentum_scan_id ?? '')).not.toBe('')

  await page.reload()
  await expect(page.getByText('Persisted', { exact: true })).toBeVisible()
  await expect(page.getByText(/28d formation/)).toBeVisible()

  await page.goto(
    `/candidate/${fixture.baseline_scan_id}/${fixture.basket_candidate_id}`,
  )
  await expect(page.getByText('Candidate lineage', { exact: true })).toBeVisible()
  await expect(page.getByText('Fixed trial:', { exact: true })).toBeVisible()

  await page.goto('/baskets')
  await page.getByLabel('Source scan').selectOption(fixture.baseline_scan_id)
  await page.getByLabel('Horizon').selectOption('swing')
  await page.getByLabel('Decision resolution').fill('1d')
  for (const asset of ['BTC', 'ETH', 'SOL']) {
    await page.getByRole('checkbox', { name: asset, exact: true }).check()
  }

  const edgeSelector = page
    .locator('label')
    .filter({ hasText: 'BTC/SOL' })
    .getByRole('combobox')
  await edgeSelector.selectOption(fixture.basket_candidate_id)
  await expect(page.getByText('Pre-run topology only')).toBeVisible()
  await expect(
    page.getByText(/Current edge opinions, resolver pressure, and final target weights/),
  ).toBeVisible()

  await page.getByRole('button', { name: 'Run basket through QAP' }).click()
  const basketOperationLink = page.getByRole('link', { name: 'Track operation' })
  await expect(basketOperationLink).toBeVisible()
  const basketOperationId = operationIdFromHref(
    await basketOperationLink.getAttribute('href'),
  )
  const basketOperation = await waitForOperation(request, basketOperationId)
  expect(basketOperation.result?.economic_gate_status).toBe(
    'basket_development_rejected',
  )
  const basketId = String(basketOperation.result?.basket_id ?? '')
  expect(basketId).not.toBe('')

  await page.goto(`/baskets/${basketId}`)
  await expect(page.getByText('basket_development_rejected')).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Latest QAP graph decision' }),
  ).toBeVisible()
  await expect(page.getByText(/React does not recompute them/)).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Benchmark ladder' }),
  ).toBeVisible()
  await expect(page.getByText('control:band-5pct-half')).toBeVisible()
  await expect(
    page.getByText('control:relative-momentum-swing', { exact: true }),
  ).toBeVisible()
  await expect(
    page.getByRole('link', { name: 'Portfolio economics' }),
  ).toBeVisible()
})
