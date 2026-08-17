import { describe, expect, it } from 'vitest'

import { createApiClient } from './client'
import { createQapQueries } from './queries'

const client = createApiClient({
  baseUrl: 'http://127.0.0.1:8000',
  fetchImpl: async () => new Response('{}', { status: 200 }),
})

describe('QAP query keys', () => {
  it('includes every authoritative pair and anchor URL input', () => {
    const queries = createQapQueries(client)

    expect(
      queries.pairSeries({
        runId: 'run-a',
        assetX: 'ETH',
        assetY: 'BTC',
        orientation: 'ETH/BTC',
      }).queryKey,
    ).toEqual(['pair-series', 'run-a', 'ETH', 'BTC', 'ETH/BTC'])
    expect(queries.paperOperations().queryKey).toEqual(['paper-operations'])
    expect(queries.paperOperation('paper-a').queryKey).toEqual([
      'paper-operation',
      'paper-a',
    ])
    expect(
      queries.pairEvidence({
        runId: 'run-a',
        assetX: 'ETH',
        assetY: 'BTC',
        orientation: 'BTC/ETH',
      }).queryKey,
    ).toEqual(['pair-evidence', 'run-a', 'ETH', 'BTC', 'BTC/ETH'])
    expect(
      queries.anchorLens({
        runId: 'run-a',
        assetX: 'ETH',
        assetY: 'BTC',
        anchor: 'USDT',
        orientation: 'BTC/ETH',
      }).queryKey,
    ).toEqual(['anchor-lens', 'run-a', 'ETH', 'BTC', 'USDT', 'BTC/ETH'])
  })

  it('keeps experiment and portfolio identities scoped to run ID', () => {
    const queries = createQapQueries(client)

    expect(queries.experiments().queryKey).toEqual(['experiments'])
    expect(queries.experiment('run-a').queryKey).toEqual(['experiment', 'run-a'])
    expect(queries.portfolio('run-a').queryKey).toEqual(['portfolio', 'run-a'])
    expect(queries.performance('run-a').queryKey).toEqual([
      'portfolio-performance',
      'run-a',
    ])
  })
})
