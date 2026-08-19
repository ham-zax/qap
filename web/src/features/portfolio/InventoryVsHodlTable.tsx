import type { PortfolioSnapshotDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'
import { formatSignedDecimal } from '../../lib/format'

interface InventoryVsHodlTableProps {
  snapshot: PortfolioSnapshotDto
  valueUnit?: string
}

export function InventoryVsHodlTable({
  snapshot,
  valueUnit,
}: InventoryVsHodlTableProps) {
  const maxMagnitude = Math.max(
    ...snapshot.strategy_vs_hodl_terminal_deltas
      .map((delta) => Math.abs(Number(delta.value_delta)))
      .filter((value) => Number.isFinite(value)),
    0,
  )

  return (
    <section
      className="rounded-lg border border-border bg-panel p-5 md:p-6"
      aria-labelledby="inventory-deltas-heading"
    >
      <h2 id="inventory-deltas-heading" className="mb-2 text-lg font-semibold text-foreground">
        Terminal holdings differences vs HODL
      </h2>
      <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
        Same-mark value deltas are comparable across assets. Raw coin-unit deltas stay
        in the audit table because heterogeneous quantities are not additive. These are
        terminal holdings/value differences, not causal asset-level profit attribution.
      </p>

      <div className="space-y-4">
        {snapshot.strategy_vs_hodl_terminal_deltas.map((delta) => {
          const numeric = Number(delta.value_delta)
          const negative = Number.isFinite(numeric) && numeric < 0
          const width =
            maxMagnitude > 0 && Number.isFinite(numeric)
              ? Math.min(100, (Math.abs(numeric) / maxMagnitude) * 100)
              : 0
          const formatted = formatSignedDecimal(delta.value_delta)
          return (
            <div key={delta.asset} className="min-w-0">
              <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-medium text-foreground">{delta.asset}</span>
                <span className="text-sm text-secondary">
                  <span
                    className="font-semibold tabular-nums text-foreground"
                    data-exact={formatted.exact}
                  >
                    {formatted.display}
                  </span>{' '}
                  {valueUnit ?? 'value units'}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-subtle" aria-hidden="true">
                <span
                  className={`block h-full rounded-full ${negative ? 'bg-negative' : 'bg-positive'}`}
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <details className="mt-5 rounded-md border border-border bg-canvas/35 p-4">
        <summary className="cursor-pointer font-semibold text-foreground">
          Exact terminal HODL differences
        </summary>
        <div className="mt-4">
          <TableScroll label="Strategy versus HODL terminal deltas">
            <table aria-label="Strategy versus HODL terminal deltas">
              <thead>
                <tr>
                  <th scope="col">Asset</th>
                  <th scope="col">Quantity delta</th>
                  <th scope="col">Same-mark value delta</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.strategy_vs_hodl_terminal_deltas.map((delta) => (
                  <tr key={delta.asset}>
                    <th scope="row">{delta.asset}</th>
                    <td><ExactNumber value={delta.quantity_delta} /></td>
                    <td><ExactNumber value={delta.value_delta} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableScroll>
        </div>
      </details>

      {snapshot.strategy_vs_matched_contribution_terminal_deltas ? (
        <details className="mt-3 rounded-md border border-border bg-canvas/35 p-4">
          <summary className="cursor-pointer font-semibold text-foreground">
            Compare with matched-contribution static HODL
          </summary>
          <div className="mt-4">
            <TableScroll label="Strategy versus matched-contribution terminal deltas">
              <table aria-label="Strategy versus matched-contribution terminal deltas">
                <thead>
                  <tr>
                    <th scope="col">Asset</th>
                    <th scope="col">Quantity delta</th>
                    <th scope="col">Same-mark value delta</th>
                  </tr>
                </thead>
                <tbody>
                  {snapshot.strategy_vs_matched_contribution_terminal_deltas.map(
                    (delta) => (
                      <tr key={delta.asset}>
                        <th scope="row">{delta.asset}</th>
                        <td><ExactNumber value={delta.quantity_delta} /></td>
                        <td><ExactNumber value={delta.value_delta} /></td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </TableScroll>
          </div>
        </details>
      ) : null}
    </section>
  )
}
