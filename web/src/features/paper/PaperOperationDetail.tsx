import type { PaperOperationDetailDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'

interface PaperOperationDetailProps {
  data: PaperOperationDetailDto
}

function keyValueRows(values: Record<string, string>) {
  return Object.entries(values)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => (
      <tr key={key}>
        <th scope="row">{key}</th>
        <td><ExactNumber value={value} /></td>
      </tr>
    ))
}

export function PaperOperationDetail({ data }: PaperOperationDetailProps) {
  return (
    <article aria-labelledby="paper-operation-heading">
      <header>
        <p>
          Forward-paper operational dry run — not prospective candidate evidence
        </p>
        <h1 id="paper-operation-heading">{data.operation_id}</h1>
        <p>{data.reconciliation_matches ? 'Reconciled' : 'Reconciliation mismatch'}</p>
        <p>{data.source_note}</p>
      </header>

      <section aria-labelledby="research-boundary-heading">
        <h2 id="research-boundary-heading">Research boundary</h2>
        <p>{data.research_boundary.rule}</p>
        <dl>
          <div>
            <dt>Parameter selection</dt>
            <dd>
              {data.research_boundary.eligible_for_parameter_selection
                ? 'Eligible'
                : 'Not eligible'}
            </dd>
          </div>
          <div>
            <dt>Model promotion</dt>
            <dd>
              {data.research_boundary.eligible_for_model_promotion
                ? 'Eligible'
                : 'Not eligible'}
            </dd>
          </div>
          <div>
            <dt>Deployment evidence</dt>
            <dd>
              {data.research_boundary.eligible_for_deployment_evidence
                ? 'Eligible'
                : 'Not eligible'}
            </dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="operation-summary-heading">
        <h2 id="operation-summary-heading">Operation summary</h2>
        <dl>
          <div>
            <dt>Execution time</dt>
            <dd>{data.execution_timestamp}</dd>
          </div>
          <div>
            <dt>Bridge</dt>
            <dd>{data.bridge}</dd>
          </div>
          <div>
            <dt>Bridge target quantity</dt>
            <dd><ExactNumber value={data.bridge_target_quantity} /></dd>
          </div>
          <div>
            <dt>Bridge residual</dt>
            <dd><ExactNumber value={data.bridge_residual} /></dd>
          </div>
          <div>
            <dt>Total fees</dt>
            <dd><ExactNumber value={data.total_fee_quote} /></dd>
          </div>
          <div>
            <dt>Total slippage</dt>
            <dd><ExactNumber value={data.total_slippage_quote} /></dd>
          </div>
          <div>
            <dt>Input fingerprint</dt>
            <dd>{data.input_fingerprint}</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="holdings-heading">
        <h2 id="holdings-heading">Holdings and target</h2>
        <h3>Starting holdings</h3>
        <TableScroll label="Starting holdings">
          <table>
            <thead>
              <tr>
                <th scope="col">Asset</th>
                <th scope="col">Quantity</th>
              </tr>
            </thead>
            <tbody>{keyValueRows(data.starting_holdings)}</tbody>
          </table>
        </TableScroll>
        <h3>Target weights</h3>
        <TableScroll label="Target weights">
          <table>
            <thead>
              <tr>
                <th scope="col">Asset</th>
                <th scope="col">Weight</th>
              </tr>
            </thead>
            <tbody>{keyValueRows(data.target_weights)}</tbody>
          </table>
        </TableScroll>
        <h3>Ending holdings</h3>
        <TableScroll label="Ending holdings">
          <table>
            <thead>
              <tr>
                <th scope="col">Asset</th>
                <th scope="col">Quantity</th>
              </tr>
            </thead>
            <tbody>{keyValueRows(data.ending_holdings)}</tbody>
          </table>
        </TableScroll>
      </section>

      <section aria-labelledby="tracking-heading">
        <h2 id="tracking-heading">Target tracking</h2>
        <TableScroll label="Target tracking">
          <table>
            <thead>
              <tr>
                <th scope="col">Asset</th>
                <th scope="col">Target weight</th>
                <th scope="col">Actual weight</th>
                <th scope="col">Weight error</th>
                <th scope="col">Unfilled quantity</th>
                <th scope="col">Unfilled value</th>
              </tr>
            </thead>
            <tbody>
              {data.tracking_errors.map((item) => (
                <tr key={item.asset}>
                  <th scope="row">{item.asset}</th>
                  <td><ExactNumber value={item.target_weight} /></td>
                  <td><ExactNumber value={item.actual_weight} /></td>
                  <td><ExactNumber value={item.weight_error} /></td>
                  <td><ExactNumber value={item.unfilled_quantity} /></td>
                  <td><ExactNumber value={item.unfilled_value} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableScroll>
      </section>

      <section aria-labelledby="reconciliation-heading">
        <h2 id="reconciliation-heading">Independent reconciliation</h2>
        <dl>
          <div>
            <dt>Recomputed fee total</dt>
            <dd><ExactNumber value={data.reconciliation.recomputed_fee_total} /></dd>
          </div>
          <div>
            <dt>Recomputed turnover</dt>
            <dd><ExactNumber value={data.reconciliation.recomputed_turnover} /></dd>
          </div>
          <div>
            <dt>Expected terminal value</dt>
            <dd>
              {data.reconciliation.expected_terminal_value == null
                ? 'Unavailable'
                : <ExactNumber value={data.reconciliation.expected_terminal_value} />}
            </dd>
          </div>
          <div>
            <dt>Recomputed terminal value</dt>
            <dd>
              {data.reconciliation.recomputed_terminal_value == null
                ? 'Unavailable'
                : <ExactNumber value={data.reconciliation.recomputed_terminal_value} />}
            </dd>
          </div>
        </dl>
        {data.reconciliation.economic_differences.length === 0 ? (
          <p>No independent fill-economic differences detected.</p>
        ) : (
          <p>{data.reconciliation.economic_differences.length} fill-economic difference(s) detected.</p>
        )}
      </section>

      <section aria-labelledby="orders-heading">
        <h2 id="orders-heading">Execution routes and orders</h2>
        <TableScroll label="Execution routes and orders">
          <table>
            <thead>
              <tr>
                <th scope="col">Phase</th>
                <th scope="col">Asset</th>
                <th scope="col">Route</th>
                <th scope="col">Requested source quantity</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              {data.orders.map((order) => (
                <tr key={`${order.phase}:${order.asset}:${order.route_id}`}>
                  <td>{order.phase}</td>
                  <td>{order.asset}</td>
                  <td>{order.route_id}</td>
                  <td><ExactNumber value={order.requested_source_quantity} /></td>
                  <td>
                    {order.leg_reason
                      ? `No fill: ${order.leg_reason}`
                      : `${order.fill_ids.length} fill${order.fill_ids.length === 1 ? '' : 's'}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableScroll>
      </section>

      <section aria-labelledby="fills-heading">
        <h2 id="fills-heading">Realized fills</h2>
        {data.fills.length === 0 ? (
          <p>No fills were realized.</p>
        ) : (
          <TableScroll label="Realized fills">
            <table>
              <thead>
                <tr>
                  <th scope="col">Fill</th>
                  <th scope="col">Market</th>
                  <th scope="col">Side</th>
                  <th scope="col">Quantity</th>
                  <th scope="col">Execution price</th>
                  <th scope="col">Fee</th>
                  <th scope="col">Slippage</th>
                </tr>
              </thead>
              <tbody>
                {data.fills.map((fill) => (
                  <tr key={fill.fill_id}>
                    <td>{fill.fill_id}</td>
                    <td>{fill.venue_symbol}</td>
                    <td>{fill.side}</td>
                    <td><ExactNumber value={fill.base_quantity} /></td>
                    <td><ExactNumber value={fill.execution_price} /></td>
                    <td><ExactNumber value={fill.fee_quote} /></td>
                    <td><ExactNumber value={fill.slippage_quote} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableScroll>
        )}
      </section>

      <section aria-labelledby="metadata-heading">
        <h2 id="metadata-heading">Venue precision metadata</h2>
        <TableScroll label="Venue precision metadata">
          <table>
            <thead>
              <tr>
                <th scope="col">Market</th>
                <th scope="col">Tick</th>
                <th scope="col">Quantity step</th>
                <th scope="col">Minimum quantity</th>
                <th scope="col">Market maximum quantity</th>
                <th scope="col">Minimum notional</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.market_metadata)
                .sort(([left], [right]) => left.localeCompare(right))
                .map(([symbol, metadata]) => (
                  <tr key={symbol}>
                    <td>{symbol}</td>
                    <td><ExactNumber value={metadata.price_tick} /></td>
                    <td><ExactNumber value={metadata.quantity_step} /></td>
                    <td>{metadata.minimum_quantity ? <ExactNumber value={metadata.minimum_quantity} /> : 'Disabled'}</td>
                    <td>{metadata.market_maximum_quantity ? <ExactNumber value={metadata.market_maximum_quantity} /> : 'Disabled'}</td>
                    <td>{metadata.minimum_notional ? <ExactNumber value={metadata.minimum_notional} /> : 'Disabled'}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </TableScroll>
      </section>
    </article>
  )
}
