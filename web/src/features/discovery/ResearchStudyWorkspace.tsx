import { useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { QapQueries } from '../../api/queries'
import type { WorkspaceStatusDto } from '../../api/types'
import { PairResearch } from './PairResearch'
import { studyTitle } from './researchStudies'
import { useResearchStudies } from './useResearchStudies'

export function ResearchStudyWorkspace({ apiClient, queries, workspace }: {
  apiClient: QapApiClient; queries: QapQueries; workspace: WorkspaceStatusDto
}) {
  const saved = useResearchStudies(`${workspace.workspace_mode}:${workspace.workspace_root}`)
  const [busy, setBusy] = useState(false)
  const study = saved.library.studies.find((item) => item.id === saved.library.activeId)!

  return (
    <div className="mx-auto min-w-0 max-w-[1000px]">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">Comparison</p>
          <h2 className="mt-1 mb-0 text-xl font-semibold text-foreground">{studyTitle(study)}</h2>
        </div>
        <details className="relative">
          <summary className="min-h-11 cursor-pointer rounded-md border border-border px-4 py-2 text-sm font-semibold text-secondary">
            Saved comparisons · {saved.library.studies.length}
          </summary>
          <div className="mt-2 w-full rounded-lg border border-border bg-panel p-4 sm:min-w-[22rem]">
            <div className="flex items-center justify-between gap-3">
              <p className="m-0 text-sm font-semibold text-foreground">Saved in this browser</p>
              <button type="button" disabled={busy} onClick={saved.create}
                className="min-h-11 rounded-md px-3 text-sm font-semibold text-accent disabled:opacity-50">
                New comparison
              </button>
            </div>
            <div className="mt-3 max-h-72 space-y-2 overflow-y-auto">
              {saved.library.studies.map((item) => (
                <button key={item.id} type="button" disabled={busy} aria-pressed={item.id === study.id}
                  onClick={() => saved.select(item.id)}
                  className={`min-h-14 w-full rounded-md border p-3 text-left disabled:opacity-50 ${item.id === study.id ? 'border-accent bg-subtle' : 'border-border'}`}>
                  <span className="block break-words text-sm font-semibold text-foreground">{studyTitle(item)}</span>
                  <span className="mt-1 block text-xs text-muted">{item.attempts.length ? `${item.attempts.length} ${item.attempts.length === 1 ? 'run' : 'runs'}` : 'Draft'}</span>
                </button>
              ))}
            </div>
            <label className="mt-4 block border-t border-border pt-4 text-xs font-semibold text-secondary">
              Optional name for this comparison
              <input value={study.name} placeholder={studyTitle(study)} maxLength={120}
                onChange={(event) => saved.update(study.id, { name: event.target.value })}
                className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground" />
            </label>
            <p className="mt-3 mb-0 text-xs leading-5 text-muted">
              Drafts are local to this browser. Finished backtests remain available in{' '}
              <a className="text-accent underline" href="/experiments/">History</a>.
            </p>
          </div>
        </details>
      </div>
      {saved.warning ? <p role="alert" className="mb-4 rounded-md border border-warning/45 p-4 text-sm text-warning">{saved.warning}</p> : null}
      <PairResearch key={study.id} apiClient={apiClient} queries={queries} workspace={workspace}
        study={study} onChange={(patch) => saved.update(study.id, patch)}
        onAttempt={(id, question) => saved.recordAttempt(study.id, id, question)} onBusyChange={setBusy} />
    </div>
  )
}
