import type { RebalanceDecisionAuditDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'

interface RebalanceDecisionAuditProps {
  decisions: RebalanceDecisionAuditDto[]
}

function WeightList({ weights }: { weights: Record<string, string> | null }) {
  if (!weights) return <p>Not available.</p>
  return (
    <ul>
      {Object.entries(weights).map(([asset, weight]) => (
        <li key={asset}>
          {asset}: <ExactNumber value={weight} />
        </li>
      ))}
    </ul>
  )
}

export function RebalanceDecisionAudit({ decisions }: RebalanceDecisionAuditProps) {
  if (decisions.length === 0) {
    return (
      <section aria-labelledby="rebalance-audit-heading">
        <h2 id="rebalance-audit-heading">Rebalance decision audit</h2>
        <p>No persisted rebalance decisions are available.</p>
      </section>
    )
  }

  return (
    <section aria-labelledby="rebalance-audit-heading">
      <h2 id="rebalance-audit-heading">Rebalance decision audit</h2>
      {decisions.map((decision) => (
        <details key={decision.decision_id}>
          <summary>
            {decision.decision_time} - {decision.selected ? 'selected' : 'not selected'}
          </summary>
          <p>{decision.reason}</p>
          <p>
            Modeled cost: fee {decision.modeled_fee_bps} bps; slippage{' '}
            {decision.modeled_slippage_bps} bps
          </p>
          <p>
            Evidence: {decision.evidence_ids.length > 0 ? decision.evidence_ids.join(', ') : 'none'}
          </p>
          <div className="audit-grid">
            <div>
              <h3>Current weights</h3>
              <WeightList weights={decision.current_weights} />
            </div>
            <div>
              <h3>Baseline target</h3>
              <WeightList weights={decision.baseline_target_weights} />
            </div>
            <div>
              <h3>QAP target</h3>
              <WeightList weights={decision.target_weights} />
            </div>
          </div>
          {decision.requested_quantity_deltas ? (
            <div>
              <h3>Requested quantity deltas</h3>
              <ul>
                {Object.entries(decision.requested_quantity_deltas).map(
                  ([asset, quantity]) => (
                    <li key={asset}>
                      {asset}: <ExactNumber value={quantity} />
                    </li>
                  ),
                )}
              </ul>
            </div>
          ) : null}
          {decision.fills.length > 0 ? (
            <TableScroll label={`Fills for ${decision.decision_id}`}>
              <table aria-label={`Fills for ${decision.decision_id}`}>
              <thead>
                <tr>
                  <th scope="col">Side</th>
                  <th scope="col">Market</th>
                  <th scope="col">Quantity</th>
                  <th scope="col">Execution price</th>
                  <th scope="col">Fee</th>
                </tr>
              </thead>
              <tbody>
                {decision.fills.map((fill) => (
                  <tr key={fill.fill_id}>
                    <td>{fill.side}</td>
                    <td>
                      {fill.base}/{fill.quote}
                    </td>
                    <td><ExactNumber value={fill.base_quantity} /></td>
                    <td><ExactNumber value={fill.execution_price} /></td>
                    <td>
                      <ExactNumber value={fill.fee_amount} /> {fill.fee_asset}
                    </td>
                  </tr>
                ))}
              </tbody>
              </table>
            </TableScroll>
          ) : (
            <p>No fill was applied for this decision.</p>
          )}
          <TableScroll label={`Post-fill holdings for ${decision.decision_id}`}>
            <table aria-label={`Post-fill holdings for ${decision.decision_id}`}>
              <thead>
                <tr>
                  <th scope="col">Asset</th>
                  <th scope="col">Quantity</th>
                  <th scope="col">Value</th>
                  <th scope="col">Weight</th>
                </tr>
              </thead>
              <tbody>
                {decision.post_fill_holdings.map((holding) => (
                  <tr key={holding.asset}>
                    <th scope="row">{holding.asset}</th>
                    <td><ExactNumber value={holding.quantity} /></td>
                    <td><ExactNumber value={holding.value} /></td>
                    <td><ExactNumber value={holding.weight} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableScroll>
        </details>
      ))}
    </section>
  )
}
