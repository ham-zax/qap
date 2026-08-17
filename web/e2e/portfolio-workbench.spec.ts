import { expect, test } from '@playwright/test'

const API_BASE_URL =
  process.env.QAP_E2E_API_BASE_URL ?? 'http://127.0.0.1:48765'

test('known run portfolio preserves HODL-relative evidence and reaches pair workbench', async ({
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

  await page.goto(`/experiments/${runId}`)
  await page.getByRole('link', { name: 'Portfolio economics' }).click()

  await expect(page).toHaveURL(new RegExp(`/portfolio/${runId}`))
  await expect(page.getByRole('heading', { name: 'Portfolio economics' })).toBeVisible()
  await expect(page.getByText('vs strict inventory HODL', { exact: true }).first()).toBeVisible()
  await expect(
    page.getByRole('heading', {
      name: 'Relative wealth through time',
      exact: true,
    }),
  ).toBeVisible()

  await page.getByRole('link', { name: 'Pair workbench' }).click()
  await expect(page).toHaveURL(new RegExp(`/pair/${runId}/`))
  await expect(page.getByText('Pair workbench', { exact: true })).toBeVisible()
})
