import { describe, expect, it, vi } from 'vitest'

import { QapApiError, createApiClient } from './client'

describe('QAP API client', () => {
  it('returns the generated experiment-list DTO without changing exact values', async () => {
    const payload = {
      schema_version: 'qap.api.experiment_list.v1',
      items: [
        {
          artifact_status: 'valid',
          run_id: 'run-0123456789abcdef01234567',
          experiment_name: 'negative fixture',
          research_family_id: 'family-a',
          parent_run_id: null,
          universe_mode: 'declared_fixed_basket',
          data_role: 'development',
          final_oos_consumed: false,
          status: 'negative',
          primary_metric: 'primary_control_relative_terminal_wealth',
          primary_metric_value: '-0.0179',
          primary_incremental_benchmark: 'periodic-2',
          incremental_vs_primary_control: '-0.0179',
          incremental_vs_matched_contribution: '-0.0180',
          created_timestamp: '2026-08-17T06:00:00Z',
          git_dirty: true,
          family_attempt_count: 2,
          error: null,
        },
      ],
    }
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    const client = createApiClient({
      baseUrl: 'http://127.0.0.1:8000/',
      fetchImpl: fetchMock,
    })

    const result = await client.listExperiments()

    expect(result).toEqual(payload)
    expect(result.items[0]?.primary_metric_value).toBe('-0.0179')
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/experiments',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it.each([
    {
      label: 'portfolio',
      call: (client: ReturnType<typeof createApiClient>) =>
        client.getPortfolio('run-0123456789abcdef01234567'),
      expected:
        'http://127.0.0.1:8000/api/portfolios/run-0123456789abcdef01234567',
    },
    {
      label: 'portfolio performance',
      call: (client: ReturnType<typeof createApiClient>) =>
        client.getPortfolioPerformance('run-0123456789abcdef01234567'),
      expected:
        'http://127.0.0.1:8000/api/portfolios/run-0123456789abcdef01234567/performance',
    },
    {
      label: 'pair series',
      call: (client: ReturnType<typeof createApiClient>) =>
        client.getPairSeries({
          runId: 'run-0123456789abcdef01234567',
          assetX: 'ETH',
          assetY: 'BTC',
          orientation: 'ETH/BTC',
        }),
      expected:
        'http://127.0.0.1:8000/api/pairs/ETH/BTC/series?run_id=run-0123456789abcdef01234567&orientation=ETH%2FBTC',
    },
    {
      label: 'paper operations',
      call: (client: ReturnType<typeof createApiClient>) =>
        client.listPaperOperations(),
      expected: 'http://127.0.0.1:8000/api/paper-operations',
    },
    {
      label: 'paper operation detail',
      call: (client: ReturnType<typeof createApiClient>) =>
        client.getPaperOperation('forward-paper/unsafe'),
      expected:
        'http://127.0.0.1:8000/api/paper-operations/forward-paper%2Funsafe',
    },
    {
      label: 'pair evidence',
      call: (client: ReturnType<typeof createApiClient>) =>
        client.getPairEvidence({
          runId: 'run-0123456789abcdef01234567',
          assetX: 'ETH',
          assetY: 'BTC',
          orientation: 'ETH/BTC',
        }),
      expected:
        'http://127.0.0.1:8000/api/pairs/ETH/BTC/evidence?run_id=run-0123456789abcdef01234567&orientation=ETH%2FBTC',
    },
    {
      label: 'anchor lens',
      call: (client: ReturnType<typeof createApiClient>) =>
        client.getAnchorLens({
          runId: 'run-0123456789abcdef01234567',
          assetX: 'ETH',
          assetY: 'BTC',
          anchor: 'USDT',
          orientation: 'BTC/ETH',
        }),
      expected:
        'http://127.0.0.1:8000/api/pairs/ETH/BTC/anchor?run_id=run-0123456789abcdef01234567&anchor=USDT&orientation=BTC%2FETH',
    },
  ])('builds the authoritative $label request URL', async ({ call, expected }) => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response('{}', { status: 200 }))
    const client = createApiClient({
      baseUrl: 'http://127.0.0.1:8000',
      fetchImpl: fetchMock,
    })

    await call(client)

    expect(fetchMock).toHaveBeenCalledWith(
      expected,
      expect.objectContaining({ headers: { Accept: 'application/json' } }),
    )
  })

  it('maps the stable API error envelope to a typed frontend error', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: 'run_not_found',
            message: 'Run was not found.',
            context: { run_id: 'run-deadbeefdeadbeefdeadbeef' },
          },
        }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    const client = createApiClient({
      baseUrl: 'http://127.0.0.1:8000',
      fetchImpl: fetchMock,
    })

    await expect(
      client.getExperiment('run-deadbeefdeadbeefdeadbeef'),
    ).rejects.toMatchObject({
      code: 'run_not_found',
      status: 404,
      context: { run_id: 'run-deadbeefdeadbeefdeadbeef' },
    })
  })
})
