import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ChartAttribution } from './ChartAttribution'

describe('ChartAttribution', () => {
  it('credits TradingView and identifies the chart library', () => {
    render(<ChartAttribution />)

    const link = screen.getByRole('link', { name: /TradingView/i })
    expect(link).toHaveAttribute('href', 'https://www.tradingview.com/')
    expect(screen.getByText(/Lightweight Charts/)).toBeInTheDocument()
    expect(screen.getByText(/Apache-2.0/)).toBeInTheDocument()
  })
})
