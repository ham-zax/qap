import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { OperationListDto } from '../../api/types'
import { OperationList } from './OperationList'

const data: OperationListDto = {
  schema_version: 'qap.api.operation_list.v1',
  items: [
    {
      schema_version: 'qap.api.operation.v1',
      operation_id: '11111111-1111-4111-8111-111111111111',
      kind: 'refresh_coin_directory',
      status: 'completed',
      requested_at: '2026-08-19T00:00:00Z',
      started_at: '2026-08-19T00:00:01Z',
      finished_at: '2026-08-19T00:00:03Z',
      request_summary: {},
      result: { directory_status: 'refreshed' },
      failure: null,
    },
    {
      schema_version: 'qap.api.operation.v1',
      operation_id: '22222222-2222-4222-8222-222222222222',
      kind: 'prepare_pair_rotation_data',
      status: 'failed',
      requested_at: '2026-08-19T00:00:00Z',
      started_at: '2026-08-19T00:00:01Z',
      finished_at: '2026-08-19T00:00:02Z',
      request_summary: { venue: 'binance' },
      result: null,
      failure: { code: 'market_data_unavailable', message: 'Market data is missing.', context: {} },
    },
  ],
}

describe('OperationList', () => {
  it('keeps operational completion separate from research results', () => {
    render(<OperationList data={data} />)

    expect(screen.getByText('Completed')).toBeVisible()
    expect(screen.getByText('Failed to run')).toBeVisible()
    expect(screen.getAllByText('Refresh coin directory')[0]).toBeVisible()
    expect(screen.getAllByText('Prepare pair market data')[0]).toBeVisible()
    expect(screen.getByText(/Market data is missing\./)).toBeVisible()
    expect(screen.queryByText(/positive evidence/i)).not.toBeInTheDocument()
  })

  it('links each activity record to its own detail screen only', () => {
    render(<OperationList data={data} />)

    const links = screen.getAllByRole('link', { name: 'Review activity' })
    expect(links.map((link) => link.getAttribute('href'))).toEqual([
      '/operations/11111111-1111-4111-8111-111111111111',
      '/operations/22222222-2222-4222-8222-222222222222',
    ])
  })
})
