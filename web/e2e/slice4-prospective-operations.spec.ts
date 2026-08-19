import { expect, test } from '@playwright/test'

import {
  API_BASE_URL,
  fixtureState,
  operationIdFromHref,
  waitForOperation,
} from './slice4-helpers'

test('Slice 4 prospective workflow preserves causal evidence and operation failures', async ({
  page,
  request,
}) => {
  test.setTimeout(180_000)
  const fixture = await fixtureState(request)

  await page.goto(
    `/candidate/${fixture.manual_scan_id}/${fixture.manual_candidate_id}`,
  )
  await expect(page.getByText('deep_replay_survivor')).toBeVisible()
  await expect(page.getByText('manual / pinned lineage')).toBeVisible()
  await page.getByLabel('Freeze UTC').fill(fixture.freeze_at)
  await page.getByRole('button', { name: 'Freeze cohort' }).click()

  const freezeOperationLink = page.getByRole('link', { name: /^Track / })
  await expect(freezeOperationLink).toBeVisible()
  const freezeOperation = await waitForOperation(
    request,
    operationIdFromHref(await freezeOperationLink.getAttribute('href')),
  )
  const cohortId = String(freezeOperation.result?.cohort_id ?? '')
  expect(cohortId).not.toBe('')

  await page.goto(`/prospective/${cohortId}`)
  await expect(page.getByRole('heading', { name: 'swing evidence' })).toBeVisible()
  await expect(page.getByText('1 manual')).toBeVisible()
  await page.getByLabel('Through UTC').fill(fixture.advance_through)
  await page.getByRole('button', { name: 'Advance cohort' }).click()

  const advanceOperationLink = page.getByRole('link', { name: /^Track / })
  await expect(advanceOperationLink).toBeVisible()
  const advanceOperation = await waitForOperation(
    request,
    operationIdFromHref(await advanceOperationLink.getAttribute('href')),
  )
  const checkpointIds = advanceOperation.result?.checkpoint_ids
  expect(Array.isArray(checkpointIds)).toBeTruthy()
  const checkpointId = String((checkpointIds as unknown[])[0] ?? '')
  expect(checkpointId).not.toBe('')

  await page.reload()
  await expect(page.getByText('partial', { exact: true })).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'One-shot public capture' }),
  ).toBeVisible()
  await page.getByLabel('Capture kind').selectOption('metadata')
  await page.getByLabel('Venue symbol').fill('BTCETH')
  await page.getByLabel('Base asset').fill('BTC')
  await page.getByLabel('Quote asset').fill('ETH')
  await page.getByRole('button', { name: 'Capture now' }).click()

  const captureOperationLink = page.getByRole('link', { name: /^Track / })
  await expect(captureOperationLink).toBeVisible()
  const captureOperationId = operationIdFromHref(
    await captureOperationLink.getAttribute('href'),
  )
  const captureOperation = await waitForOperation(request, captureOperationId)
  expect(captureOperation.result?.kind).toBe('metadata')

  await page.getByLabel('Qualification checkpoint').selectOption(checkpointId)
  await page.getByLabel('Qualification as-of').fill(fixture.qualification_as_of)
  await page.getByLabel('Requested capital').fill('10')
  await page.getByRole('button', { name: 'Qualify' }).click()

  const qualifyOperationLink = page.getByRole('link', { name: /^Track / })
  await expect(qualifyOperationLink).not.toHaveAttribute(
    'href',
    `/operations/${captureOperationId}`,
  )
  await waitForOperation(
    request,
    operationIdFromHref(await qualifyOperationLink.getAttribute('href')),
  )

  await page.reload()
  await expect(page.getByText('research_only', { exact: true })).toBeVisible()
  await expect(page.getByText('capture complete', { exact: true })).toBeVisible()
  await expect(page.getByText('economic_gates_failed', { exact: true })).toBeVisible()

  const failedResponse = await request.post(
    `${API_BASE_URL}/api/scans/${'f'.repeat(64)}/momentum-generations`,
    { data: { venue: 'binance', horizon: 'swing' } },
  )
  expect(failedResponse.status()).toBe(202)
  const failedRef = (await failedResponse.json()) as { operation_id: string }
  const failed = await waitForOperation(request, failedRef.operation_id, 'failed')
  expect(failed.failure?.code).toBeTruthy()

  await page.goto(`/operations/${failedRef.operation_id}`)
  await expect(
    page.getByRole('heading', { name: 'Generate Asset Momentum' }),
  ).toBeVisible()
  await expect(page.getByText('failed', { exact: true })).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Operational failure' }),
  ).toBeVisible()
  await expect(
    page.getByText(/Scientific evidence is not inferred from this operational failure/),
  ).toBeVisible()
})
