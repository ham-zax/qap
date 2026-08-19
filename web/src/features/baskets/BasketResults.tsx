import type { BasketListDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'

interface BasketResultsProps {
  baskets: BasketListDto
}

function gatePresentation(status: string | null | undefined): {
  label: string
  tone: 'positive' | 'info'
} {
  if (status === 'basket_development_survivor') {
    return { label: 'Passed basket development gates', tone: 'positive' }
  }
  if (status === 'basket_development_rejected') {
    return { label: 'Did not pass basket development gates', tone: 'info' }
  }
  return { label: 'Completed research', tone: 'info' }
}

function horizonLabel(horizon: string | null | undefined) {
  if (horizon === 'short') return 'Short horizon'
  if (horizon === 'medium') return 'Medium horizon'
  if (horizon === 'swing') return 'Swing horizon'
  return 'Horizon unavailable'
}

export function BasketResults({ baskets }: BasketResultsProps) {
  return (
    <section className="mt-8" aria-labelledby="completed-baskets-heading">
      <h2 id="completed-baskets-heading" className="text-xl font-semibold text-foreground">
        Portfolio research results
      </h2>
      {baskets.items.length === 0 ? (
        <p className="text-sm text-secondary">No completed portfolio research yet.</p>
      ) : (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {baskets.items.map((basket) => {
            const gate = gatePresentation(basket.economic_gate_status)
            const productSource =
              basket.source_claim?.kind === 'current_approved_retrospective'
            return (
              <article
                key={basket.basket_id}
                className="rounded-lg border border-border bg-panel p-5"
              >
                <div className="flex flex-wrap gap-2">
                  {basket.artifact_status === 'valid' ? (
                    <Badge tone={gate.tone}>{gate.label}</Badge>
                  ) : (
                    <Badge tone="negative">Research artifact invalid</Badge>
                  )}
                  {basket.forensic ? <Badge tone="warning">Forensic research</Badge> : null}
                  {basket.source_claim ? (
                    <Badge tone={productSource ? 'positive' : 'neutral'}>
                      {basket.source_claim.label}
                    </Badge>
                  ) : null}
                </div>
                <h3 className="mt-4 mb-2 text-base font-semibold text-foreground">
                  {basket.economic_assets.join(' · ') || basket.basket_id.slice(0, 12)}
                </h3>
                <p className="m-0 text-sm text-secondary">
                  {horizonLabel(basket.horizon)} ·{' '}
                  {basket.decision_resolution ?? 'resolution unavailable'}
                </p>
                {basket.source_as_of ? (
                  <p className="mt-2 mb-0 text-xs text-muted">
                    {productSource ? 'Data through' : 'Historical universe as of'}{' '}
                    {formatResearchTimestamp(basket.source_as_of)}
                  </p>
                ) : null}
                {basket.error ? (
                  <p className="mt-2 text-sm text-negative">{basket.error.message}</p>
                ) : null}
                {basket.economic_gate_status ? (
                  <details className="mt-3 text-xs text-muted">
                    <summary className="cursor-pointer font-semibold">
                      Exact research status
                    </summary>
                    <p className="mb-0 font-mono">{basket.economic_gate_status}</p>
                  </details>
                ) : null}
                <a
                  className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
                  href={`/baskets/${basket.basket_id}`}
                >
                  Review portfolio result
                </a>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
