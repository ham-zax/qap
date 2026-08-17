import { expect, test } from '@playwright/test'

const API_BASE_URL =
  process.env.QAP_E2E_API_BASE_URL ?? 'http://127.0.0.1:48765'

test('pair workbench keeps reciprocal orientation and anchor lens in URL state', async ({
  page,
  request,
}) => {
  const response = await request.get(`${API_BASE_URL}/api/experiments`)
  expect(response.ok()).toBeTruthy()
  const payload = (await response.json()) as {
    items: Array<{ artifact_status: string; run_id: string }>
  }
  const runId = payload.items.find((item) => item.artifact_status === 'valid')?.run_id
  expect(runId).toBeTruthy()
  if (!runId) throw new Error('fixture API returned no valid run')

  await page.goto(
    `/pair/${runId}/BTC/USDT?orientation=BTC%2FUSDT&anchor=none&view=ratio`,
  )
  await expect(page.getByRole('heading', { name: 'BTC / USDT' })).toBeVisible()

  await page.getByRole('button', { name: 'Show USDT / BTC' }).click()
  await expect(page.getByRole('heading', { name: 'USDT / BTC' })).toBeVisible()
  await expect(page).toHaveURL(/orientation=USDT%2FBTC/)

  const anchor = page.getByRole('combobox', { name: 'Anchor lens' })
  await anchor.selectOption('USDT')

  await expect(anchor).toHaveValue('USDT')
  await expect(page).toHaveURL(/anchor=USDT/)
  await expect(page).toHaveURL(/view=anchor/)
  await expect(page.getByRole('heading', { name: 'Anchor decomposition' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'USDT / BTC' })).toBeVisible()
  await expect(page.getByLabel('Synchronized anchor charts')).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'BTC/USDT reduced anchor path' }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'USDT log decomposition' }),
  ).toBeVisible()
})
