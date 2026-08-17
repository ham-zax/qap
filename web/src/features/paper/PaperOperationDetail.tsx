import type { PaperOperationDetailDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'
import { Badge } from '../../components/ui/Badge'
import { CompositionBars } from '../../components/visuals/CompositionBars'
import {
  formatDecimal,
  formatPercent,
  formatResearchTimestamp,
  formatSignedDecimal,
} from '../../lib/format'
import { humanizeIdentifier } from '../experiments/presentation'
import { PaperExecutionFlow } from './PaperExecutionFlow'

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

function Metric({
  label,
  value,
  exact,
}: {
  label: string
  value: string
  exact?: string
}) {
  return (
    <div className="rounded-md border border-border bg-canvas/45 p-4">
      <p className="m-0 text-xs font-medium text-muted">{label}</p>
      <p
        className="mt-1 mb-0 text-xl font-semibold tabular-nums text-foreground"
        data-exact={exact}
      >
        {value}
      </p>
    </div>
  )
}

function HoldingsSnapshot({
  label,
  holdings,
}: {
  label: string
  holdings: Record<string, string>
}) {
  return (
    <div className="rounded-md border border-border bg-canvas/35 p-4">
      <h3 className="mb-3 text-sm font-semibold text-foreground">{label}</h3>
      <ul className="m-0 grid list-none gap-2 p-0 text-sm sm:grid-cols-2">
        {Object.entries(holdings)
          .sort(([left], [right]) => left.localeCompare(right))
          .map(([asset, quantity]) => {
            const formatted = formatDecimal(quantity, 8)
            return (
              <li key={asset} className="flex min-w-0 justify-between gap-3">
                <span className="font-medium text-secondary">{asset}</span>
                <span
                  className="min-w-0 truncate font-medium tabular-nums text-foreground"
                  data-exact={formatted.exact}
                  title={`Exact: ${formatted.exact}`}
                >
                  {formatted.display}
                </span>
              </li>
            )
          })}
      </ul>
    </div>
  )
}

export function PaperOperationDetail({ data }: PaperOperationDetailProps) {
  const noFillOrders = data.orders.filter((order) => order.leg_reason !== null)
  const fee = formatDecimal(data.total_fee_quote, 6)
  const slippage = formatDecimal(data.total_slippage_quote, 6)
  const residual = formatDecimal(data.bridge_residual, 6)
  const reconciled = data.reconciliation_matches

  return (
    <article className="min-w-0" aria-labelledby="paper-operation-heading">
      <div className="mb-4">
        <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-sm text-muted">
          <a className="font-medium text-secondary" href="/paper-operations">Paper operations</a>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Paper rebalance</span>
        </nav>
      </div>

      <header
        className={`rounded-lg border bg-panel p-5 md:p-6 ${reconciled ? 'border-positive/45' : 'border-negative/45'}`}
      >
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge tone={reconciled ? 'positive' : 'negative'}>
            {reconciled ? 'Reconciled' : 'Reconciliation mismatch'}
          </Badge>
          <Badge tone="info">Forward paper · operational dry run</Badge>
        </div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-muted">
          Operational result
        </p>
        <h1
          id="paper-operation-heading"
          className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl"
        >
          Paper rebalance
        </h1>
        <p className="m-0 max-w-4xl text-xl font-semibold leading-tight text-foreground md:text-2xl">
          {reconciled
            ? noFillOrders.length > 0
              ? `Reconciled with ${data.fills.length} fills; ${noFillOrders.length} leg${noFillOrders.length === 1 ? '' : 's'} did not fill.`
              : `Reconciled with ${data.fills.length} fills and no rejected or no-fill legs.`
            : 'Independent reconciliation found a mismatch in the recorded operation.'}
        </p>
        <p className="mt-3 mb-0 max-w-3xl text-sm leading-6 text-secondary">
          {formatResearchTimestamp(data.execution_timestamp)} · Bridge {data.bridge} · {data.source_note}
        </p>

        <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Metric
            label="Execution legs"
            value={`${data.fills.length} fills · ${noFillOrders.length} no-fill`}
          />
          <Metric label="Fees" value={fee.display} exact={fee.exact} />
          <Metric label="Slippage" value={slippage.display} exact={slippage.exact} />
          <Metric label="Bridge residual" value={residual.display} exact={residual.exact} />
        </div>
      </header>

      <div className="mt-6 space-y-6">
        <section
          className="rounded-lg border border-warning/45 bg-panel p-5 md:p-6"
          aria-labelledby="research-boundary-heading"
        >
          <h2 id="research-boundary-heading" className="mb-2 text-lg font-semibold text-foreground">
            Research boundary
          </h2>
          <p className="mt-0 mb-3 font-semibold text-warning">
            Forward paper only — not valid for parameter selection, model promotion, or deployment evidence.
          </p>
          <p className="m-0 max-w-4xl text-sm leading-6 text-secondary">
            {data.research_boundary.rule}
          </p>
        </section>

        <PaperExecutionFlow data={data} />

        {noFillOrders.length > 0 || data.fills.length === 0 ? (
          <section
            className="rounded-lg border border-warning/45 bg-panel p-5 md:p-6"
            aria-labelledby="execution-exceptions-heading"
          >
            <h2 id="execution-exceptions-heading" className="mb-3 text-lg font-semibold text-foreground">
              Execution exceptions
            </h2>
            {data.fills.length === 0 ? (
              <p className="mt-0 mb-4 text-sm text-secondary">No fills were realized.</p>
            ) : null}
            <div className="space-y-3">
              {noFillOrders.map((order) => (
                <div
                  key={`${order.phase}:${order.asset}:${order.route_id}`}
                  className="rounded-md border border-warning/35 bg-canvas/35 p-4"
                >
                  <p className="m-0 font-semibold text-warning">
                    No fill · {order.asset} · {humanizeIdentifier(order.leg_reason ?? 'unknown reason')}
                  </p>
                  <p className="mt-2 mb-0 text-xs text-secondary">
                    {humanizeIdentifier(order.phase)} · requested source quantity{' '}
                    <ExactNumber value={order.requested_source_quantity} />
                  </p>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <section
          className="rounded-lg border border-border bg-panel p-5 md:p-6"
          aria-labelledby="holdings-heading"
        >
          <h2 id="holdings-heading" className="mb-2 text-lg font-semibold text-foreground">
            Holdings and target
          </h2>
          <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
            Starting and ending holdings are persisted quantities. Only the target
            composition is plotted because the artifact does not provide starting or
            ending weights.
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            <HoldingsSnapshot label="Starting holdings" holdings={data.starting_holdings} />
            <HoldingsSnapshot label="Ending holdings" holdings={data.ending_holdings} />
          </div>
          <div className="mt-4 rounded-md border border-border bg-canvas/35 p-4">
            <h3 className="mb-3 text-sm font-semibold text-foreground">Target allocation</h3>
            <CompositionBars
              label="Target allocation"
              items={Object.entries(data.target_weights).map(([asset, weight]) => ({
                asset,
                weight,
              }))}
            />
          </div>
        </section>

        <section
          className="rounded-lg border border-border bg-panel p-5 md:p-6"
          aria-labelledby="tracking-heading"
        >
          <h2 id="tracking-heading" className="mb-2 text-lg font-semibold text-foreground">
            Target tracking
          </h2>
          <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
            Persisted target-versus-actual differences make precision and unfilled
            inventory effects visible without reading the full execution tables.
          </p>
          <div className="grid gap-3 lg:grid-cols-2">
            {data.tracking_errors.map((item) => {
              const target = formatPercent(item.target_weight)
              const actual = formatPercent(item.actual_weight)
              const weightError = formatSignedDecimal(item.weight_error, 4)
              const unfilled = formatSignedDecimal(item.unfilled_value, 4)
              return (
                <article key={item.asset} className="rounded-md border border-border bg-canvas/35 p-4">
                  <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                    <h3 className="m-0 text-base font-semibold text-foreground">{item.asset}</h3>
                    <span
                      className="text-sm font-semibold tabular-nums text-foreground"
                      data-exact={weightError.exact}
                    >
                      {weightError.display} weight error
                    </span>
                  </div>
                  <dl className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <dt className="text-xs text-muted">Target</dt>
                      <dd className="mt-1 mb-0 font-medium tabular-nums text-foreground" data-exact={target.exact}>
                        {target.display}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Actual</dt>
                      <dd className="mt-1 mb-0 font-medium tabular-nums text-foreground" data-exact={actual.exact}>
                        {actual.display}
                      </dd>
                    </div>
                    <div className="col-span-2">
                      <dt className="text-xs text-muted">Unfilled value</dt>
                      <dd className="mt-1 mb-0 font-medium tabular-nums text-foreground" data-exact={unfilled.exact}>
                        {unfilled.display}
                      </dd>
                    </div>
                  </dl>
                </article>
              )
            })}
          </div>
        </section>

        <section
          className={`rounded-lg border bg-panel p-5 md:p-6 ${data.reconciliation.matches ? 'border-positive/45' : 'border-negative/45'}`}
          aria-labelledby="reconciliation-heading"
        >
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <h2 id="reconciliation-heading" className="m-0 text-lg font-semibold text-foreground">
              Independent reconciliation
            </h2>
            <Badge tone={data.reconciliation.matches ? 'positive' : 'negative'}>
              {data.reconciliation.matches ? 'Matches' : 'Mismatch'}
            </Badge>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric
              label="Recomputed fees"
              value={formatDecimal(data.reconciliation.recomputed_fee_total, 6).display}
              exact={data.reconciliation.recomputed_fee_total}
            />
            <Metric
              label="Recomputed turnover"
              value={formatDecimal(data.reconciliation.recomputed_turnover, 6).display}
              exact={data.reconciliation.recomputed_turnover}
            />
            <Metric
              label="Expected terminal value"
              value={
                data.reconciliation.expected_terminal_value == null
                  ? 'Unavailable'
                  : formatDecimal(data.reconciliation.expected_terminal_value, 6).display
              }
              exact={data.reconciliation.expected_terminal_value ?? undefined}
            />
            <Metric
              label="Recomputed terminal value"
              value={
                data.reconciliation.recomputed_terminal_value == null
                  ? 'Unavailable'
                  : formatDecimal(data.reconciliation.recomputed_terminal_value, 6).display
              }
              exact={data.reconciliation.recomputed_terminal_value ?? undefined}
            />
          </div>
          <p className="mt-4 mb-0 text-sm text-secondary">
            {data.reconciliation.economic_differences.length === 0
              ? 'No independent fill-economic differences detected.'
              : `${data.reconciliation.economic_differences.length} fill-economic difference(s) detected.`}
          </p>
        </section>

        <details className="rounded-lg border border-border bg-panel p-5 md:p-6">
          <summary className="cursor-pointer font-semibold text-foreground">Execution audit</summary>
          <div className="mt-5 space-y-5">
            <TableScroll label="Execution routes and orders">
              <table aria-label="Execution routes and orders">
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

            {data.fills.length > 0 ? (
              <TableScroll label="Realized fills">
                <table aria-label="Realized fills">
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
            ) : null}
          </div>
        </details>

        <details className="rounded-lg border border-border bg-panel p-5 md:p-6">
          <summary className="cursor-pointer font-semibold text-foreground">
            Technical execution details
          </summary>
          <div className="mt-5 space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="min-w-0">
                <p className="m-0 text-xs text-muted">Operation ID</p>
                <code className="mt-1 block overflow-x-auto rounded-md bg-canvas px-2 py-1 font-mono text-xs text-secondary" tabIndex={0}>
                  {data.operation_id}
                </code>
              </div>
              <div className="min-w-0">
                <p className="m-0 text-xs text-muted">Input fingerprint</p>
                <code className="mt-1 block overflow-x-auto rounded-md bg-canvas px-2 py-1 font-mono text-xs text-secondary" tabIndex={0}>
                  {data.input_fingerprint}
                </code>
              </div>
              <div className="min-w-0">
                <p className="m-0 text-xs text-muted">Code fingerprint</p>
                <code className="mt-1 block overflow-x-auto rounded-md bg-canvas px-2 py-1 font-mono text-xs text-secondary" tabIndex={0}>
                  {data.code_fingerprint}
                </code>
              </div>
              <div className="min-w-0 text-sm text-secondary">
                <p className="m-0">Fee model · {data.fee_bps} bps</p>
                <p className="mt-1 mb-0">Slippage model · {data.slippage_bps} bps</p>
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              <TableScroll label="Starting holdings">
                <table aria-label="Starting holdings">
                  <thead><tr><th scope="col">Asset</th><th scope="col">Quantity</th></tr></thead>
                  <tbody>{keyValueRows(data.starting_holdings)}</tbody>
                </table>
              </TableScroll>
              <TableScroll label="Target weights">
                <table aria-label="Target weights">
                  <thead><tr><th scope="col">Asset</th><th scope="col">Weight</th></tr></thead>
                  <tbody>{keyValueRows(data.target_weights)}</tbody>
                </table>
              </TableScroll>
              <TableScroll label="Ending holdings">
                <table aria-label="Ending holdings">
                  <thead><tr><th scope="col">Asset</th><th scope="col">Quantity</th></tr></thead>
                  <tbody>{keyValueRows(data.ending_holdings)}</tbody>
                </table>
              </TableScroll>
            </div>

            <TableScroll label="Venue precision metadata">
              <table aria-label="Venue precision metadata">
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

            <details className="rounded-md border border-border bg-canvas/35 p-4">
              <summary className="cursor-pointer text-sm font-semibold text-foreground">
                Valuation and reference prices
              </summary>
              <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <TableScroll label="Valuation prices">
                  <table aria-label="Valuation prices">
                    <thead><tr><th scope="col">Asset</th><th scope="col">Price</th></tr></thead>
                    <tbody>{keyValueRows(data.valuation_prices)}</tbody>
                  </table>
                </TableScroll>
                <TableScroll label="Reference prices">
                  <table aria-label="Reference prices">
                    <thead><tr><th scope="col">Market</th><th scope="col">Price</th></tr></thead>
                    <tbody>{keyValueRows(data.reference_prices)}</tbody>
                  </table>
                </TableScroll>
                <TableScroll label="MARKET notional-filter reference prices">
                  <table aria-label="MARKET notional-filter reference prices">
                    <thead><tr><th scope="col">Market</th><th scope="col">Price</th></tr></thead>
                    <tbody>{keyValueRows(data.market_notional_reference_prices)}</tbody>
                  </table>
                </TableScroll>
              </div>
            </details>
          </div>
        </details>
      </div>
    </article>
  )
}
