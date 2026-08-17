import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PaperOperationSummaryDto } from '../../api/types'
import { PaperOperationList } from './PaperOperationList'

const item = {
  schema_version: 'qap.api.paper_operation_summary.v1',
  operation_id: 'forward-paper-1',
  data_role: 'forward_paper',
  execution_timestamp: '2026-08-17T11:11:00Z',
  reconciliation_matches: true,
  fill_count: 3,
  total_fee_quote: '0.42',
  total_slippage_quote: '0.21',
  bridge_residual: '0.003',
  route_ids: ['direct:ETH>USDT', 'direct:USDT>BTC'],
} satisfies PaperOperationSummaryDto

describe('PaperOperationList', () => {
  it('surfaces reconciled forward-paper evidence without execution controls', () => {
    render(<PaperOperationList items={[item]} />)

    expect(screen.getByRole('heading', { name: 'Forward-paper operations' })).toBeVisible()
    expect(screen.getByText('Reconciled')).toBeVisible()
    expect(screen.getByText('0.42')).toBeVisible()
    expect(screen.getByRole('link', { name: 'Inspect paper operation' })).toHaveAttribute(
      'href',
      '/paper-operations/forward-paper-1',
    )
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('shows readable financial values while preserving their exact strings', () => {
    const exact = '43877.03679286245537776080139063222484512761661829455060919175'
    render(
      <PaperOperationList items={[{ ...item, total_fee_quote: exact }]} />,
    )

    const displayed = screen.getByText('43,877.037')
    expect(displayed).toHaveAttribute('data-exact', exact)
    expect(displayed).toHaveAttribute('title', `Exact: ${exact}`)
  })
})
