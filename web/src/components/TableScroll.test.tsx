import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TableScroll } from './TableScroll'

describe('TableScroll', () => {
  it('exposes a labelled keyboard-focusable horizontal scroll region', () => {
    render(
      <TableScroll label="Benchmark economics">
        <table>
          <tbody>
            <tr>
              <td>value</td>
            </tr>
          </tbody>
        </table>
      </TableScroll>,
    )

    const region = screen.getByRole('region', {
      name: 'Benchmark economics table',
    })
    expect(region).toHaveAttribute('tabindex', '0')
    expect(region).toHaveClass('table-scroll')
  })
})
