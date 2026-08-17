import type { PortfolioSnapshotDto } from '../../api/types'
import { TableScroll } from '../../components/TableScroll'

interface InventoryVsHodlTableProps {
  snapshot: PortfolioSnapshotDto
}

export function InventoryVsHodlTable({ snapshot }: InventoryVsHodlTableProps) {
  return (
    <section aria-labelledby="inventory-deltas-heading">
      <h2 id="inventory-deltas-heading">Inventory attribution</h2>
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
              <td>{delta.quantity_delta}</td>
              <td>{delta.value_delta}</td>
            </tr>
          ))}
        </tbody>
        </table>
      </TableScroll>

      {snapshot.strategy_vs_matched_contribution_terminal_deltas ? (
        <details>
          <summary>Compare with matched-contribution static HODL</summary>
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
                    <td>{delta.quantity_delta}</td>
                    <td>{delta.value_delta}</td>
                  </tr>
                ),
              )}
            </tbody>
            </table>
          </TableScroll>
        </details>
      ) : null}
    </section>
  )
}
