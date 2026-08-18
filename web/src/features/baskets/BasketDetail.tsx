import type {
  BasketDetailDto,
  ExperimentDetailDto,
  PortfolioSnapshotDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { LineageTrail } from '../lineage/LineageTrail'
import { BasketGraph } from './BasketGraph'

interface BasketDetailProps {
  basket: BasketDetailDto
  experiment: ExperimentDetailDto | null
  portfolio: PortfolioSnapshotDto | null
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

export function BasketDetail({ basket, experiment, portfolio }: BasketDetailProps) {
  const summary = basket.summary
  const graphAudits = (portfolio?.rebalance_audit ?? []).filter((audit) =>
    audit.evidence_ids.some((id) => id.startsWith('basket-')),
  )
  const lastGraphAudit = graphAudits.at(-1) ?? null
  const bridgeHoldings = portfolio?.terminal.holdings.filter(
    (holding) => !summary.economic_assets.includes(holding.asset),
  ) ?? []
  const edges = basket.selected_edges.map((edge) => ({
    pair: edge.pair_id,
    label: `${edge.model_family} · ${edge.template_id} · ${edge.candidate_orientation}`,
  }))

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Terminal basket evidence
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {summary.economic_assets.join(' · ') || `Basket ${shortId(summary.basket_id)}`}
        </h1>
        <div className="flex flex-wrap gap-2">
          <Badge tone={summary.artifact_status === 'valid' ? 'positive' : 'negative'}>
            {summary.artifact_status}
          </Badge>
          {summary.economic_gate_status ? (
            <Badge
              tone={summary.economic_gate_status.includes('survivor') ? 'positive' : 'warning'}
            >
              {summary.economic_gate_status}
            </Badge>
          ) : null}
          {summary.forensic ? <Badge tone="warning">forensic basket</Badge> : null}
        </div>
        <p className="mt-3 mb-0 text-sm text-secondary">
          {summary.venue} / {summary.horizon} · {summary.decision_resolution} · source scan{' '}
          <a className="text-accent" href={`/scanner/${summary.source_scan_id}`}>
            {summary.source_scan_id ? shortId(summary.source_scan_id) : 'unknown'}
          </a>
        </p>
      </header>

      <LineageTrail
        items={[
          ...(summary.source_scan_id
            ? [
                {
                  label: 'scan',
                  value: summary.source_scan_id,
                  href: `/scanner/${summary.source_scan_id}`,
                },
              ]
            : []),
          { label: 'basket', value: summary.basket_id },
          ...(summary.qap_run_id
            ? [
                {
                  label: 'QAP',
                  value: summary.qap_run_id,
                  href: `/experiments/${summary.qap_run_id}`,
                },
              ]
            : []),
        ]}
      />

      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(20rem,0.8fr)_minmax(0,1.2fr)]">
        <article className="rounded-lg border border-border bg-panel p-5">
          <h2 className="mt-0 text-lg font-semibold text-foreground">Relationship graph</h2>
          <BasketGraph assets={[...summary.economic_assets]} edges={edges} />
          <ul className="mt-4 space-y-3 pl-5 text-sm text-secondary">
            {basket.selected_edges.map((edge) => (
              <li key={edge.candidate_id}>
                <a
                  className="font-semibold text-accent"
                  href={`/candidate/${summary.source_scan_id}/${edge.candidate_id}`}
                >
                  {edge.pair_id}
                </a>{' '}
                · {edge.model_family} / {edge.template_id} · {edge.candidate_orientation}
                {edge.manual_pinned ? ' · manual pin' : ''}
                {edge.deep_replay_status === 'setup_failed' ? ' · scout-only indirect' : ''}
              </li>
            ))}
          </ul>
        </article>

        <article className="rounded-lg border border-border bg-panel p-5">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Authoritative resolver state
          </p>
          <h2 className="mt-2 text-lg font-semibold text-foreground">Latest QAP graph decision</h2>
          {lastGraphAudit ? (
            <>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {Object.entries(lastGraphAudit.target_weights ?? {}).map(([asset, weight]) => (
                  <div key={asset} className="rounded-md border border-border p-3">
                    <p className="m-0 text-xs text-muted">{asset} target</p>
                    <p className="mt-1 mb-0 font-semibold tabular-nums text-foreground">{weight}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-md border border-border bg-subtle p-4">
                <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">Decision evidence</p>
                <ul className="mt-2 space-y-1 pl-5 text-xs text-secondary">
                  {lastGraphAudit.evidence_ids.filter((id) => id.startsWith('basket-')).map((id) => (
                    <li key={id} className="break-all">{id}</li>
                  ))}
                </ul>
              </div>
              <p className="mt-4 mb-0 text-xs text-muted">
                These opinions/resolver inputs/targets are read from the authoritative QAP decision event. React does not recompute them.
              </p>
            </>
          ) : (
            <p className="text-sm text-secondary">
              No graph decision audit is available for this terminal run.
            </p>
          )}
        </article>
      </div>

      <section className="mt-8" aria-labelledby="benchmark-heading">
        <h2 id="benchmark-heading" className="text-xl font-semibold text-foreground">Benchmark ladder</h2>
        {experiment ? (
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {experiment.result.roles.map((role) => (
              <article key={role.role} className="rounded-lg border border-border bg-panel p-4">
                <p className="m-0 text-xs text-muted">{role.role}</p>
                <p className="mt-2 mb-0 text-lg font-semibold tabular-nums text-foreground">{role.terminal_value}</p>
                <p className="mt-1 mb-0 text-xs text-secondary">fees {role.fees_value} · slippage {role.slippage_value} · fills {role.fill_count}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-secondary">The authoritative QAP experiment is unavailable.</p>
        )}
      </section>

      {bridgeHoldings.length ? (
        <section className="mt-8 rounded-lg border border-border bg-panel p-5" aria-labelledby="bridge-heading">
          <h2 id="bridge-heading" className="mt-0 text-lg font-semibold text-foreground">Execution-only bridge residue</h2>
          <p className="text-sm text-secondary">Bridge holdings are shown separately from the declared economic basket.</p>
          {bridgeHoldings.map((holding) => (
            <p key={holding.asset} className="mb-0 text-sm text-secondary">
              <strong className="text-foreground">{holding.asset}</strong> · quantity {holding.quantity} · value {holding.value}
            </p>
          ))}
        </section>
      ) : null}

      {summary.qap_run_id ? (
        <nav className="mt-8 flex flex-wrap gap-3" aria-label="Basket evidence links">
          <a className="inline-flex min-h-11 items-center rounded-md bg-accent px-4 font-semibold text-canvas" href={`/experiments/${summary.qap_run_id}`}>Experiment detail</a>
          <a className="inline-flex min-h-11 items-center rounded-md border border-border px-4 font-semibold text-accent" href={`/portfolio/${summary.qap_run_id}`}>Portfolio economics</a>
        </nav>
      ) : null}
    </section>
  )
}
