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

function gatePresentation(
  artifactStatus: string,
  economicGateStatus: string | null | undefined,
): {
  label: string
  tone: 'positive' | 'info' | 'negative'
  explanation: string
} {
  if (artifactStatus !== 'valid') {
    return {
      label: 'Research artifact invalid',
      tone: 'negative',
      explanation:
        'QAP could not publish a valid portfolio research artifact. The recorded error remains authoritative.',
    }
  }
  if (economicGateStatus === 'basket_development_survivor') {
    return {
      label: 'Passed basket development gates',
      tone: 'positive',
      explanation:
        'QAP completed the portfolio replay and the persisted basket development gate classified it as a survivor.',
    }
  }
  if (economicGateStatus === 'basket_development_rejected') {
    return {
      label: 'Did not pass basket development gates',
      tone: 'info',
      explanation:
        'QAP completed the portfolio replay, but the persisted basket development gate rejected it. This is completed negative research, not an application error.',
    }
  }
  return {
    label: 'Portfolio research result',
    tone: 'info',
    explanation:
      'QAP published portfolio research evidence. The exact persisted gate status is available in the audit disclosure below.',
  }
}

function roleLabel(role: string) {
  if (role === 'strategy') return 'Portfolio strategy'
  if (role === 'hodl') return 'Buy-and-hold benchmark'
  return role.replaceAll('_', ' ')
}

function relationshipLabel(edge: BasketDetailDto['selected_edges'][number]) {
  if (edge.manual_pinned) return 'Manual research relationship'
  if (edge.deep_replay_status === 'setup_failed') return 'Indirect research relationship'
  if (edge.automatic_neighbor_selected) return 'Scanner-neighbor relationship'
  return 'Selected research relationship'
}

export function BasketDetail({ basket, experiment, portfolio }: BasketDetailProps) {
  const summary = basket.summary
  const graphAudits = (portfolio?.rebalance_audit ?? []).filter((audit) =>
    audit.evidence_ids.some((id) => id.startsWith('basket-')),
  )
  const lastGraphAudit = graphAudits.at(-1) ?? null
  const bridgeHoldings =
    portfolio?.terminal.holdings.filter(
      (holding) => !summary.economic_assets.includes(holding.asset),
    ) ?? []
  const graphEdges = basket.selected_edges.map((edge) => ({
    pair: edge.pair_id,
    label: relationshipLabel(edge),
  }))
  const verdict = gatePresentation(summary.artifact_status, summary.economic_gate_status)

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Portfolio research result
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {summary.economic_assets.join(' · ') || `Portfolio ${shortId(summary.basket_id)}`}
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Read the persisted economic verdict first, compare the authoritative QAP
          benchmark roles, then inspect the graph decision and execution evidence.
        </p>
      </header>

      <LineageTrail
        items={[
          ...(summary.source_scan_id
            ? [
                {
                  label: 'historical research',
                  value: summary.source_scan_id,
                  href: `/scanner/${summary.source_scan_id}`,
                },
              ]
            : []),
          { label: 'portfolio research', value: summary.basket_id },
          ...(summary.qap_run_id
            ? [
                {
                  label: 'QAP result',
                  value: summary.qap_run_id,
                  href: `/experiments/${summary.qap_run_id}`,
                },
              ]
            : []),
        ]}
      />

      <article className="mt-6 rounded-lg border border-border bg-panel p-5">
        <div className="flex flex-wrap gap-2">
          <Badge tone={verdict.tone}>{verdict.label}</Badge>
          {summary.forensic ? <Badge tone="warning">Forensic research</Badge> : null}
        </div>
        <h2 className="mt-4 mb-2 text-xl font-semibold text-foreground">
          Research verdict
        </h2>
        <p className="m-0 max-w-4xl text-sm leading-6 text-secondary">
          {verdict.explanation}
        </p>
        {summary.error ? (
          <p className="mt-3 mb-0 text-sm text-negative">{summary.error.message}</p>
        ) : null}
        <p className="mt-4 mb-0 text-xs leading-5 text-muted">
          Research result only — QAP does not place or authorize live trades.
        </p>
      </article>

      <section className="mt-8" aria-labelledby="benchmark-heading">
        <div className="max-w-3xl">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Authoritative QAP comparison
          </p>
          <h2 id="benchmark-heading" className="mt-2 text-xl font-semibold text-foreground">
            Benchmark comparison
          </h2>
          <p className="text-sm leading-6 text-secondary">
            These terminal values and modeled costs come directly from persisted QAP
            result roles. The browser does not calculate a substitute portfolio score.
          </p>
        </div>
        {experiment ? (
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {experiment.result.roles.map((role) => (
              <article key={role.role} className="rounded-lg border border-border bg-panel p-4">
                <p className="m-0 text-sm font-semibold text-foreground">
                  {roleLabel(role.role)}
                </p>
                <p className="mt-1 mb-0 font-mono text-[11px] text-muted">{role.role}</p>
                <p className="mt-3 mb-0 text-lg font-semibold tabular-nums text-foreground">
                  {role.terminal_value}
                </p>
                <p className="mt-1 mb-0 text-xs leading-5 text-secondary">
                  fees {role.fees_value} · slippage {role.slippage_value} · fills{' '}
                  {role.fill_count}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-secondary">The authoritative QAP experiment is unavailable.</p>
        )}
      </section>

      <section className="mt-8" aria-labelledby="decision-heading">
        <h2 id="decision-heading" className="text-xl font-semibold text-foreground">
          Why QAP chose this portfolio state
        </h2>
        <div className="mt-4 grid gap-6 xl:grid-cols-[minmax(20rem,0.9fr)_minmax(0,1.1fr)]">
          <article className="rounded-lg border border-border bg-panel p-5">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Authoritative graph decision
            </p>
            {lastGraphAudit ? (
              <>
                <p className="mt-3 text-sm leading-6 text-secondary">
                  {lastGraphAudit.reason}
                </p>
                <h3 className="mt-5 text-sm font-semibold text-foreground">
                  Persisted target weights
                </h3>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  {Object.entries(lastGraphAudit.target_weights ?? {}).map(([asset, weight]) => (
                    <div key={asset} className="rounded-md border border-border p-3">
                      <p className="m-0 text-xs text-muted">{asset}</p>
                      <p className="mt-1 mb-0 font-semibold tabular-nums text-foreground">
                        {weight}
                      </p>
                    </div>
                  ))}
                </div>
                <p className="mt-4 mb-0 text-xs leading-5 text-muted">
                  Resolver opinion and targets are shown only after ordinary QAP replay.
                  React does not recompute them.
                </p>
              </>
            ) : (
              <p className="text-sm text-secondary">
                No graph decision audit is available for this terminal run.
              </p>
            )}
          </article>

          <article className="rounded-lg border border-border bg-panel p-5">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Relationships used
            </p>
            <BasketGraph assets={[...summary.economic_assets]} edges={graphEdges} />
            <div className="mt-4 space-y-3">
              {basket.selected_edges.map((edge) => (
                <details key={edge.candidate_id} className="rounded-md border border-border p-3">
                  <summary className="cursor-pointer text-sm font-semibold text-foreground">
                    {edge.pair_id} · {relationshipLabel(edge)}
                  </summary>
                  <p className="mt-3 mb-0 text-xs leading-5 text-secondary">
                    Exact rule: <span className="font-mono">{edge.model_family}</span> ·{' '}
                    <span className="font-mono">{edge.template_id}</span> · orientation{' '}
                    <span className="font-mono">{edge.candidate_orientation}</span>
                    {edge.manual_pinned ? ' · manual pin' : ''}
                    {edge.deep_replay_status === 'setup_failed'
                      ? ' · indirect/scout-only'
                      : ''}
                  </p>
                  <a
                    className="mt-2 inline-flex text-xs font-semibold text-accent"
                    href={`/candidate/${summary.source_scan_id}/${edge.candidate_id}`}
                  >
                    Open relationship evidence
                  </a>
                </details>
              ))}
            </div>
          </article>
        </div>
      </section>

      {bridgeHoldings.length ? (
        <section
          className="mt-8 rounded-lg border border-border bg-panel p-5"
          aria-labelledby="bridge-heading"
        >
          <h2 id="bridge-heading" className="mt-0 text-lg font-semibold text-foreground">
            Execution-only bridge residue
          </h2>
          <p className="text-sm text-secondary">
            Bridge holdings remain separate from the declared economic portfolio.
          </p>
          {bridgeHoldings.map((holding) => (
            <p key={holding.asset} className="mb-0 text-sm text-secondary">
              <strong className="text-foreground">{holding.asset}</strong> · quantity{' '}
              {holding.quantity} · value {holding.value}
            </p>
          ))}
        </section>
      ) : null}

      <details className="mt-8 rounded-lg border border-border bg-panel p-5">
        <summary className="cursor-pointer font-semibold text-foreground">
          Exact research and execution audit
        </summary>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-xs text-muted">Source research</dt>
            <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
              {summary.source_scan_id ?? 'unknown'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Scope</dt>
            <dd className="m-0 mt-1 text-secondary">
              {summary.venue ?? '—'} · {summary.horizon ?? '—'} ·{' '}
              {summary.decision_resolution ?? '—'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Exact economic gate</dt>
            <dd className="m-0 mt-1 font-mono text-xs text-secondary">
              {summary.economic_gate_status ?? 'none'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Attempt status</dt>
            <dd className="m-0 mt-1 font-mono text-xs text-secondary">
              {summary.attempt_status ?? 'none'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">QAP run</dt>
            <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
              {summary.qap_run_id ?? 'none'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Basket ID</dt>
            <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
              {summary.basket_id}
            </dd>
          </div>
        </dl>
        {lastGraphAudit ? (
          <div className="mt-5 border-t border-border pt-4">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Decision evidence IDs
            </p>
            <ul className="mt-2 space-y-1 pl-5 text-xs text-secondary">
              {lastGraphAudit.evidence_ids
                .filter((id) => id.startsWith('basket-'))
                .map((id) => (
                  <li key={id} className="break-all font-mono">
                    {id}
                  </li>
                ))}
            </ul>
          </div>
        ) : null}
      </details>

      {summary.qap_run_id ? (
        <nav className="mt-8 flex flex-wrap gap-3" aria-label="Portfolio evidence links">
          <a
            className="inline-flex min-h-11 items-center rounded-md bg-accent px-4 font-semibold text-canvas"
            href={`/experiments/${summary.qap_run_id}`}
          >
            Full research result
          </a>
          <a
            className="inline-flex min-h-11 items-center rounded-md border border-border px-4 font-semibold text-accent"
            href={`/portfolio/${summary.qap_run_id}`}
          >
            Portfolio economics
          </a>
        </nav>
      ) : null}
    </section>
  )
}
