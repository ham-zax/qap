import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TimeSeriesChart } from './TimeSeriesChart'

describe('TimeSeriesChart accessibility shell', () => {
  it('does not hide the container that receives the focusable attribution link', () => {
    const { container } = render(
      <TimeSeriesChart
        title="Evidence curve"
        description="A backend-produced series."
        series={[
          {
            name: 'QAP vs HODL',
            unit: 'relative wealth',
            points: [
              { timestamp: '2025-01-01T00:00:00Z', value: 0 },
              { timestamp: '2025-01-01T01:00:00Z', value: -0.01 },
            ],
          },
        ]}
      />,
    )

    expect(screen.getByRole('figure', { name: 'Evidence curve' })).toBeInTheDocument()
    expect(container.querySelector('.chart-canvas')).not.toHaveAttribute(
      'aria-hidden',
    )
  })
})
