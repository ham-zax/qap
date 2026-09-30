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
      kind: 'run_basket',
      status: 'completed',
      requested_at: '2026-08-19T00:00:00Z',
      started_at: '2026-08-19T00:00:01Z',
      finished_at: '2026-08-19T00:00:03Z',
      request_summary: { scan_id: 'a'.repeat(64) },
      result: {
        basket_id: 'b'.repeat(64),
        qap_run_id: 'run-negative-basket',
        economic_gate_status: 'basket_development_rejected',
      },
      failure: null,
    },
  ],
}

describe('OperationList', () => {
  it('keeps operational completion separate from research result references', () => {
    render(<OperationList data={data} />)

    expect(screen.getByText('Completed')).toBeVisible()
    expect(screen.getAllByText('Analyze portfolio')[0]).toBeVisible()
    expect(screen.getByRole('link', { name: 'Portfolio result' })).toHaveAttribute(
      'href',
      `/baskets/${'b'.repeat(64)}`,
    )
    expect(screen.getByRole('link', { name: 'Research run' })).toHaveAttribute(
      'href',
      '/experiments/run-negative-basket',
    )
    expect(screen.queryByText(/positive evidence/i)).not.toBeInTheDocument()
  })
})
