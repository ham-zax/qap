import type { RebalanceDecisionAuditDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'
import {
  CompositionBars,
  type CompositionItem,
} from '../../components/visuals/CompositionBars'
import { formatResearchTimestamp } from '../../lib/format'
import { humanizeIdentifier } from '../experiments/presentation'

interface RebalanceDecisionAuditProps {
  decisions: RebalanceDecisionAuditDto[]
  selectedDecisionId?: string | null
  onSelectDecision?: (decisionId: string) => void
}

function weightItems(weights: Record<string, string> | null): CompositionItem[] {
  if (!weights) return []
  return Object.entries(weights).map(([asset, weight]) => ({ asset, weight }))
}

function WeightPanel({
  title,
  weights,
}: {
  title: string
  weights: Record<string, string> | null
}) {
  const items = weightItems(weights)
  return (
    <div className="min-w-0 rounded-md border border-border bg-canvas/45 p-4">
      <h4 className="mb-3 text-sm font-semibold text-foreground">{title}</h4>
      {items.length > 0 ? (
        <CompositionBars label={title} items={items} />
      ) : (
        <p className="m-0 text-sm text-muted">Not available.</p>
      )}
    </div>
  )
}

export function RebalanceDecisionAudit({
  decisions,
  selectedDecisionId,
  onSelectDecision,
}: RebalanceDecisionAuditProps) {
  if (decisions.length === 0) {
    return (
      <section
        className="rounded-lg border border-border bg-panel p-5 md:p-6"
        aria-labelledby="rebalance-audit-heading"
      >
        <h2 id="rebalance-audit-heading" className="mb-2 text-lg font-semibold text-foreground">
          Rebalance decisions
        </h2>
        <p className="m-0 text-sm text-secondary">No persisted rebalance decisions are available.</p>
      </section>
    )
  }

  const selectedIndex = Math.max(
    0,
    decisions.findIndex((decision) => decision.decision_id === selectedDecisionId),
  )
  const decision = decisions[selectedIndex] ?? decisions[0]
  const previous = decisions[selectedIndex - 1]
  const next = decisions[selectedIndex + 1]

  return (
    <section
      className="rounded-lg border border-border bg-panel p-5 md:p-6"
      aria-labelledby="rebalance-audit-heading"
    >
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="rebalance-audit-heading" className="mb-1 text-lg font-semibold text-foreground">
            Rebalance decisions
          </h2>
          <p className="m-0 text-sm text-secondary">
            Inspect one persisted decision at a time; exact execution evidence stays on demand.
          </p>
        </div>
        <span className="text-sm tabular-nums text-muted">{decisions.length} decisions</span>
      </div>

      <div className="grid min-w-0 gap-5 md:grid-cols-[minmax(13rem,0.72fr)_minmax(0,2fr)]">
        <nav className="hidden min-w-0 md:block" aria-label="Rebalance decision timeline">
          <ol className="m-0 list-none space-y-2 p-0">
            {decisions.map((item, index) => {
              const current = item.decision_id === decision.decision_id
              return (
                <li key={item.decision_id}>
                  <button
                    type="button"
                    className={`w-full rounded-md border px-3 py-3 text-left text-sm ${current ? 'border-accent bg-subtle text-foreground' : 'border-border bg-canvas/30 text-secondary hover:border-border-strong'}`}
                    aria-current={current ? 'true' : undefined}
                    onClick={() => onSelectDecision?.(item.decision_id)}
                  >
                    <span className="block font-semibold">Decision {index + 1}</span>
                    <span className="mt-1 block text-xs text-muted">
                      {formatResearchTimestamp(item.decision_time)}
                    </span>
                    <span className="mt-1 block text-xs">
                      {item.selected ? 'Selected for execution' : 'No action selected'}
                    </span>
                  </button>
                </li>
              )
            })}
          </ol>
        </nav>

        <div className="min-w-0">
          <div className="mb-4 flex items-center justify-between gap-3 md:hidden">
            <button
              type="button"
              className="min-h-11 rounded-md border border-border bg-subtle px-3 text-sm font-semibold text-foreground disabled:opacity-40"
              disabled={!previous}
              onClick={() => previous && onSelectDecision?.(previous.decision_id)}
            >
              Previous
            </button>
            <span className="text-sm tabular-nums text-muted">
              {selectedIndex + 1} / {decisions.length}
            </span>
            <button
              type="button"
              className="min-h-11 rounded-md border border-border bg-subtle px-3 text-sm font-semibold text-foreground disabled:opacity-40"
              disabled={!next}
              onClick={() => next && onSelectDecision?.(next.decision_id)}
            >
              Next
            </button>
          </div>

          <div className="mb-5 border-b border-border pb-5">
            <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              {formatResearchTimestamp(decision.decision_time)}
            </p>
            <h3 className="mb-2 text-lg font-semibold text-foreground">
              Rebalance {selectedIndex + 1} of {decisions.length}
            </h3>
            <p className="m-0 text-sm leading-6 text-secondary">
              {humanizeIdentifier(decision.reason)}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-md border border-border bg-canvas/45 p-3">
              <p className="m-0 text-xs text-muted">Decision</p>
              <p className="mt-1 mb-0 text-sm font-semibold text-foreground">
                {decision.selected ? 'Selected' : 'No action'}
              </p>
            </div>
            <div className="rounded-md border border-border bg-canvas/45 p-3">
              <p className="m-0 text-xs text-muted">Modeled fee</p>
              <p className="mt-1 mb-0 text-sm font-semibold tabular-nums text-foreground">
                {decision.modeled_fee_bps} bp
              </p>
            </div>
            <div className="rounded-md border border-border bg-canvas/45 p-3">
              <p className="m-0 text-xs text-muted">Modeled slippage</p>
              <p className="mt-1 mb-0 text-sm font-semibold tabular-nums text-foreground">
                {decision.modeled_slippage_bps} bp
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 lg:grid-cols-3">
            <WeightPanel title="Before" weights={decision.current_weights} />
            <WeightPanel title="Baseline target" weights={decision.baseline_target_weights} />
            <WeightPanel title="QAP target" weights={decision.target_weights} />
          </div>

          <details className="mt-5 rounded-md border border-border bg-canvas/35 p-4">
            <summary className="cursor-pointer font-semibold text-foreground">
              Exact decision evidence
            </summary>
            <div className="mt-5 space-y-5">
              <div>
                <h4 className="mb-2 text-sm font-semibold text-foreground">Evidence references</h4>
                {decision.evidence_ids.length > 0 ? (
                  <ul className="m-0 space-y-2 pl-5 text-sm text-secondary">
                    {decision.evidence_ids.map((id) => (
                      <li key={id} className="break-all font-mono text-xs">{id}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="m-0 text-sm text-muted">No evidence IDs recorded.</p>
                )}
              </div>

              {decision.requested_quantity_deltas ? (
                <div>
                  <h4 className="mb-2 text-sm font-semibold text-foreground">Requested quantity deltas</h4>
                  <ul className="m-0 space-y-1 pl-5 text-sm text-secondary">
                    {Object.entries(decision.requested_quantity_deltas).map(([asset, quantity]) => (
                      <li key={asset}>
                        {asset}: <ExactNumber value={quantity} />
                      </li>
                    ))}
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
                          <td>{fill.base}/{fill.quote}</td>
                          <td><ExactNumber value={fill.base_quantity} /></td>
                          <td><ExactNumber value={fill.execution_price} /></td>
                          <td><ExactNumber value={fill.fee_amount} /> {fill.fee_asset}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </TableScroll>
              ) : (
                <p className="m-0 text-sm text-muted">No fill was applied for this decision.</p>
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
            </div>
          </details>
        </div>
      </div>
    </section>
  )
}
