import type { PaperOperationDetailDto } from '../../api/types'
import { humanizeIdentifier } from '../experiments/presentation'

interface PaperExecutionFlowProps {
  data: PaperOperationDetailDto
}

function phaseLabel(phase: string): string {
  switch (phase) {
    case 'sell_to_bridge':
      return 'Sell to bridge'
    case 'buy_from_bridge':
      return 'Buy from bridge'
    default:
      return humanizeIdentifier(phase)
  }
}

export function PaperExecutionFlow({ data }: PaperExecutionFlowProps) {
  const sells = data.orders.filter((order) => order.phase === 'sell_to_bridge')
  const buys = data.orders.filter((order) => order.phase === 'buy_from_bridge')

  return (
    <section
      className="rounded-lg border border-border bg-panel p-5 md:p-6"
      aria-labelledby="execution-flow-heading"
    >
      <h2 id="execution-flow-heading" className="mb-2 text-lg font-semibold text-foreground">
        Execution flow
      </h2>
      <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
        Persisted operation legs only. A leg with no fill remains visible in the flow
        rather than disappearing into the audit table.
      </p>

      <ol className="m-0 grid list-none gap-3 p-0 lg:grid-cols-[0.8fr_1.35fr_0.9fr_1.35fr_0.8fr]">
        <li className="rounded-md border border-border bg-canvas/45 p-4">
          <p className="m-0 text-xs font-medium text-muted">1</p>
          <h3 className="mt-1 mb-0 text-sm font-semibold text-foreground">Starting portfolio</h3>
          <p className="mt-2 mb-0 text-xs text-secondary">
            {Object.keys(data.starting_holdings).length} held assets
          </p>
        </li>

        <li className="rounded-md border border-border bg-canvas/45 p-4">
          <p className="m-0 text-xs font-medium text-muted">2 · {phaseLabel('sell_to_bridge')}</p>
          <div className="mt-2 space-y-2">
            {sells.length === 0 ? (
              <p className="m-0 text-sm text-muted">No sell legs.</p>
            ) : (
              sells.map((order) => (
                <div key={`${order.phase}:${order.asset}:${order.route_id}`} className="text-sm">
                  <p className="m-0 font-medium text-foreground">{order.asset}</p>
                  <p className={`mt-1 mb-0 text-xs ${order.leg_reason ? 'text-warning' : 'text-secondary'}`}>
                    {order.leg_reason
                      ? `No fill · ${humanizeIdentifier(order.leg_reason)}`
                      : `${order.fill_ids.length} fill${order.fill_ids.length === 1 ? '' : 's'}`}
                  </p>
                </div>
              ))
            )}
          </div>
        </li>

        <li className="rounded-md border border-border-strong bg-subtle p-4">
          <p className="m-0 text-xs font-medium text-muted">3 · Bridge</p>
          <h3 className="mt-1 mb-0 text-base font-semibold text-foreground">{data.bridge}</h3>
          <p className="mt-2 mb-0 text-xs text-secondary">Intermediate execution inventory</p>
        </li>

        <li className="rounded-md border border-border bg-canvas/45 p-4">
          <p className="m-0 text-xs font-medium text-muted">4 · {phaseLabel('buy_from_bridge')}</p>
          <div className="mt-2 space-y-2">
            {buys.length === 0 ? (
              <p className="m-0 text-sm text-muted">No buy legs.</p>
            ) : (
              buys.map((order) => (
                <div key={`${order.phase}:${order.asset}:${order.route_id}`} className="text-sm">
                  <p className="m-0 font-medium text-foreground">{order.asset}</p>
                  <p className={`mt-1 mb-0 text-xs ${order.leg_reason ? 'text-warning' : 'text-secondary'}`}>
                    {order.leg_reason
                      ? `No fill · ${humanizeIdentifier(order.leg_reason)}`
                      : `${order.fill_ids.length} fill${order.fill_ids.length === 1 ? '' : 's'}`}
                  </p>
                </div>
              ))
            )}
          </div>
        </li>

        <li className="rounded-md border border-border bg-canvas/45 p-4">
          <p className="m-0 text-xs font-medium text-muted">5</p>
          <h3 className="mt-1 mb-0 text-sm font-semibold text-foreground">Ending portfolio</h3>
          <p className="mt-2 mb-0 text-xs text-secondary">
            {Object.keys(data.ending_holdings).length} held assets
          </p>
        </li>
      </ol>
    </section>
  )
}
