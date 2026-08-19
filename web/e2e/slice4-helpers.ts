import { expect, type APIRequestContext } from '@playwright/test'

export const API_BASE_URL =
  process.env.QAP_E2E_API_BASE_URL ?? 'http://127.0.0.1:48765'

export interface Slice4FixtureState {
  baseline_scan_id: string
  manual_scan_id: string
  manual_candidate_id: string
  basket_candidate_id: string
  momentum_scan_id: string
  scan_as_of: string
  freeze_at: string
  advance_through: string
  qualification_as_of: string
}

export interface OperationPayload {
  operation_id: string
  status: 'running' | 'completed' | 'failed' | 'interrupted'
  result: Record<string, unknown> | null
  failure: { code: string; message: string } | null
}

export async function fixtureState(
  request: APIRequestContext,
): Promise<Slice4FixtureState> {
  const response = await request.get(`${API_BASE_URL}/__fixture/state`)
  expect(response.ok()).toBeTruthy()
  return (await response.json()) as Slice4FixtureState
}

export async function waitForOperation(
  request: APIRequestContext,
  operationId: string,
  expected: OperationPayload['status'] = 'completed',
): Promise<OperationPayload> {
  await expect
    .poll(
      async () => {
        const response = await request.get(
          `${API_BASE_URL}/api/operations/${operationId}`,
        )
        expect(response.ok()).toBeTruthy()
        const payload = (await response.json()) as OperationPayload
        return payload.status === 'running' ? 'running' : 'terminal'
      },
      { timeout: 180_000 },
    )
    .toBe('terminal')

  const response = await request.get(
    `${API_BASE_URL}/api/operations/${operationId}`,
  )
  expect(response.ok()).toBeTruthy()
  const terminal = (await response.json()) as OperationPayload
  expect(terminal.status).toBe(expected)
  return terminal
}

export function operationIdFromHref(href: string | null): string {
  if (!href) throw new Error('operation link is missing')
  const value = href.split('/').filter(Boolean).at(-1)
  if (!value) throw new Error(`operation link is malformed: ${href}`)
  return value
}
