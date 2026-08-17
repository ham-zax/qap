import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { QapApiError } from '../api/client'
import { ErrorDetails } from './ErrorDetails'

describe('ErrorDetails', () => {
  it('renders the typed API reason and recovery context', () => {
    render(
      <ErrorDetails
        error={
          new QapApiError({
            code: 'anchor_unavailable',
            message: 'Anchor series is unavailable for this run.',
            status: 404,
            context: { run_id: 'run-a', anchor: 'SOL' },
          })
        }
      />,
    )

    expect(screen.getByText('anchor_unavailable')).toBeInTheDocument()
    expect(
      screen.getByText('Anchor series is unavailable for this run.'),
    ).toBeInTheDocument()
    expect(screen.getByText('anchor: SOL')).toBeInTheDocument()
    expect(screen.getByText('run_id: run-a')).toBeInTheDocument()
  })

  it('renders an ordinary error without inventing API metadata', () => {
    render(<ErrorDetails error={new Error('local rendering failed')} />)

    expect(screen.getByText('local rendering failed')).toBeInTheDocument()
    expect(screen.queryByText('API error code')).not.toBeInTheDocument()
  })
})
