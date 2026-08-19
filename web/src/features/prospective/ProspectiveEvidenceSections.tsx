import { useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type {
  CapturePublicEvidenceRequestDto,
  CaptureReadinessDto,
  ForwardCohortDetailDto,
  OperationRefDto,
} from '../../api/types'
import { formatResearchTimestamp } from '../../lib/format'

interface ProspectiveEvidenceSectionsProps {
  apiClient: QapApiClient
  data: ForwardCohortDetailDto
  currentReadiness?: CaptureReadinessDto
  onCaptureStarted: (operation: OperationRefDto) => void
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

export function ProspectiveEvidenceSections({
  apiClient,
  data,
  currentReadiness,
  onCaptureStarted,
}: ProspectiveEvidenceSectionsProps) {
  const firstFreeze = data.freezes[0]
  const automatic = useMemo(
    () => data.freezes.filter((item) => item.automatic_selected),
    [data.freezes],
  )
  const manual = useMemo(
    () =>
      data.freezes.filter(
        (item) => item.manual_selected && !item.automatic_selected,
      ),
    [data.freezes],
  )
  const [manualCapture, setManualCapture] =
    useState<CapturePublicEvidenceRequestDto>({
      venue: firstFreeze?.venue === 'gate' ? 'gate' : 'binance',
      venue_symbol: '',
      base_asset: '',
      quote_asset: '',
      kind: 'l1',
    })
  const capture = useMutation({
    mutationFn: (command: CapturePublicEvidenceRequestDto) =>
      apiClient.capturePublicEvidence(command),
    onSuccess: onCaptureStarted,
  })

  return (
    <>
      <section className="mt-8" aria-labelledby="ideas-heading">
        <h2 id="ideas-heading" className="text-xl font-semibold text-foreground">
          Frozen research ideas
        </h2>
        <p className="text-sm text-secondary">
          Automatic scanner selections remain separate from manual or pinned research.
        </p>
        <div className="mt-4 grid gap-5 lg:grid-cols-2">
          <ResearchIdeaGroup title="Automatic selections" items={automatic} />
          <ResearchIdeaGroup title="Manual-only selections" items={manual} />
        </div>
      </section>

      <details className="mt-8 rounded-lg border border-border bg-panel p-5">
        <summary className="cursor-pointer font-semibold text-foreground">
          Advanced research and exact forward evidence
        </summary>
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <section aria-labelledby="manual-capture-heading">
            <h3
              id="manual-capture-heading"
              className="text-base font-semibold text-foreground"
            >
              Manual public evidence capture
            </h3>
            <p className="text-sm text-secondary">
              Use raw venue mechanics only for deliberate expert intervention. The normal
              path uses backend-returned instrument identity.
            </p>
            <div className="grid gap-2">
              <select
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
                value={manualCapture.kind}
                onChange={(event) =>
                  setManualCapture({
                    ...manualCapture,
                    kind: event.target.value as CapturePublicEvidenceRequestDto['kind'],
                  })
                }
                aria-label="Manual capture kind"
              >
                <option value="l1">L1 / book ticker</option>
                <option value="depth">Shallow depth</option>
                <option value="metadata">Market metadata</option>
              </select>
              <select
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
                value={manualCapture.venue}
                onChange={(event) =>
                  setManualCapture({
                    ...manualCapture,
                    venue: event.target.value as 'binance' | 'gate',
                  })
                }
                aria-label="Manual capture venue"
              >
                <option value="binance">binance</option>
                <option value="gate">gate</option>
              </select>
              <input
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                value={manualCapture.venue_symbol}
                onChange={(event) =>
                  setManualCapture({
                    ...manualCapture,
                    venue_symbol: event.target.value,
                  })
                }
                placeholder="Venue symbol"
                aria-label="Manual venue symbol"
              />
              <div className="grid grid-cols-2 gap-2">
                <input
                  className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                  value={manualCapture.base_asset}
                  onChange={(event) =>
                    setManualCapture({
                      ...manualCapture,
                      base_asset: event.target.value.toUpperCase(),
                    })
                  }
                  placeholder="Base"
                  aria-label="Manual base asset"
                />
                <input
                  className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                  value={manualCapture.quote_asset}
                  onChange={(event) =>
                    setManualCapture({
                      ...manualCapture,
                      quote_asset: event.target.value.toUpperCase(),
                    })
                  }
                  placeholder="Quote"
                  aria-label="Manual quote asset"
                />
              </div>
            </div>
            <button
              type="button"
              className="mt-3 min-h-11 rounded-md border border-border px-4 font-semibold text-foreground disabled:opacity-50"
              disabled={
                !manualCapture.venue_symbol ||
                !manualCapture.base_asset ||
                !manualCapture.quote_asset ||
                capture.isPending
              }
              onClick={() => capture.mutate(manualCapture)}
            >
              {capture.isPending ? 'Starting…' : 'Capture one manual observation'}
            </button>
            {capture.isError ? (
              <p className="text-sm text-negative">{capture.error.message}</p>
            ) : null}
          </section>

          <section aria-labelledby="readiness-exact-heading">
            <h3
              id="readiness-exact-heading"
              className="text-base font-semibold text-foreground"
            >
              Exact current-evidence contract
            </h3>
            {currentReadiness ? (
              <dl className="grid gap-3 text-sm">
                <div>
                  <dt className="text-xs text-muted">Instrument</dt>
                  <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
                    {currentReadiness.venue} · {currentReadiness.venue_symbol} ·{' '}
                    {currentReadiness.base_asset}/{currentReadiness.quote_asset}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Capture window</dt>
                  <dd className="m-0 mt-1 text-secondary">
                    {formatResearchTimestamp(currentReadiness.window_start)} →{' '}
                    {formatResearchTimestamp(currentReadiness.window_end)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Backend coverage</dt>
                  <dd className="m-0 mt-1 font-mono text-xs text-secondary">
                    L1 {currentReadiness.l1_overall_coverage} · depth{' '}
                    {currentReadiness.depth_overall_coverage}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Checkpoint</dt>
                  <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
                    {currentReadiness.checkpoint_id}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="text-sm text-secondary">
                Check current market evidence first to expose the exact backend-owned
                capture contract.
              </p>
            )}
          </section>
        </div>

        <h3 className="mt-6 text-base font-semibold text-foreground">
          Exact forward checkpoints
        </h3>
        {data.checkpoints.length === 0 ? (
          <p className="text-secondary">No completed forward checkpoint yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border bg-canvas/35">
            <table className="w-full min-w-[52rem] text-left text-sm">
              <thead className="bg-subtle text-xs uppercase tracking-[0.06em] text-muted">
                <tr>
                  <th className="px-4 py-3">Candidate</th>
                  <th className="px-4 py-3">Checkpoint</th>
                  <th className="px-4 py-3">Outcome</th>
                  <th className="px-4 py-3">Economic gates</th>
                  <th className="px-4 py-3">QAP</th>
                </tr>
              </thead>
              <tbody>
                {data.checkpoints.map((checkpoint) => (
                  <tr key={checkpoint.checkpoint_id} className="border-t border-border">
                    <td className="px-4 py-3 font-medium text-foreground">
                      {shortId(checkpoint.candidate_id)}
                    </td>
                    <td className="px-4 py-3 text-secondary">
                      #{checkpoint.checkpoint_index} ·{' '}
                      {formatResearchTimestamp(checkpoint.information_end)}
                    </td>
                    <td className="px-4 py-3 text-secondary">
                      {checkpoint.outcome_status}
                    </td>
                    <td className="px-4 py-3 text-secondary">
                      baseline {String(checkpoint.baseline_economic_gates_passed ?? '—')} · adverse{' '}
                      {String(checkpoint.adverse_economic_gates_passed ?? '—')}
                    </td>
                    <td className="px-4 py-3">
                      {checkpoint.qap_run_id ? (
                        <a
                          className="text-accent"
                          href={`/experiments/${checkpoint.qap_run_id}`}
                        >
                          Experiment
                        </a>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </details>
    </>
  )
}

function ResearchIdeaGroup({
  title,
  items,
}: {
  title: string
  items: ForwardCohortDetailDto['freezes']
}) {
  return (
    <article className="rounded-lg border border-border bg-panel p-5">
      <h3 className="mt-0 text-base font-semibold text-foreground">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-secondary">None.</p>
      ) : (
        <ul className="space-y-3 pl-5 text-sm text-secondary">
          {items.map((freeze) => (
            <li key={freeze.freeze_id}>
              <a
                className="font-semibold text-accent"
                href={`/candidate/${freeze.source_scan_id}/${freeze.candidate_id}`}
              >
                {freeze.pair_id}
              </a>{' '}
              · {freeze.resolution} · {formatResearchTimestamp(freeze.forward_start)} →{' '}
              {formatResearchTimestamp(freeze.forward_end)}
            </li>
          ))}
        </ul>
      )}
    </article>
  )
}
