import type { PaperOperationDetailDto } from '../../api/types'

interface PaperOperationDetailProps {
  data: PaperOperationDetailDto
}

function keyValueRows(values: Record<string, string>) {
  return Object.entries(values)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => (
      <tr key={key}>
        <th scope="row">{key}</th>
        <td>{value}</td>
      </tr>
    ))
}

export function PaperOperationDetail({ data }: PaperOperationDetailProps) {
  return (
    <article aria-labelledby="paper-operation-heading">
      <header>
        <p>Forward paper</p>
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
            <dd>{data.bridge_target_quantity}</dd>
          </div>
          <div>
            <dt>Bridge residual</dt>
            <dd>{data.bridge_residual}</dd>
          </div>
          <div>
            <dt>Total fees</dt>
            <dd>{data.total_fee_quote}</dd>
          </div>
          <div>
            <dt>Total slippage</dt>
            <dd>{data.total_slippage_quote}</dd>
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
        <table>
          <thead>
            <tr>
              <th scope="col">Asset</th>
              <th scope="col">Quantity</th>
            </tr>
          </thead>
          <tbody>{keyValueRows(data.starting_holdings)}</tbody>
        </table>
        <h3>Target weights</h3>
        <table>
          <thead>
            <tr>
              <th scope="col">Asset</th>
              <th scope="col">Weight</th>
            </tr>
          </thead>
          <tbody>{keyValueRows(data.target_weights)}</tbody>
        </table>
        <h3>Ending holdings</h3>
        <table>
          <thead>
            <tr>
              <th scope="col">Asset</th>
              <th scope="col">Quantity</th>
            </tr>
          </thead>
          <tbody>{keyValueRows(data.ending_holdings)}</tbody>
        </table>
      </section>

      <section aria-labelledby="orders-heading">
        <h2 id="orders-heading">Execution routes and orders</h2>
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
                <td>{order.requested_source_quantity}</td>
                <td>
                  {order.leg_reason
                    ? `No fill: ${order.leg_reason}`
                    : `${order.fill_ids.length} fill${order.fill_ids.length === 1 ? '' : 's'}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section aria-labelledby="fills-heading">
        <h2 id="fills-heading">Realized fills</h2>
        {data.fills.length === 0 ? (
          <p>No fills were realized.</p>
        ) : (
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
                  <td>{fill.base_quantity}</td>
                  <td>{fill.execution_price}</td>
                  <td>{fill.fee_quote}</td>
                  <td>{fill.slippage_quote}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section aria-labelledby="metadata-heading">
        <h2 id="metadata-heading">Venue precision metadata</h2>
        <table>
          <thead>
            <tr>
              <th scope="col">Market</th>
              <th scope="col">Tick</th>
              <th scope="col">Quantity step</th>
              <th scope="col">Minimum quantity</th>
              <th scope="col">Minimum notional</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.market_metadata)
              .sort(([left], [right]) => left.localeCompare(right))
              .map(([symbol, metadata]) => (
                <tr key={symbol}>
                  <td>{symbol}</td>
                  <td>{metadata.price_tick}</td>
                  <td>{metadata.quantity_step}</td>
                  <td>{metadata.minimum_quantity ?? 'Disabled'}</td>
                  <td>{metadata.minimum_notional ?? 'Disabled'}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>
    </article>
  )
}
