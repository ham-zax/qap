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
    <div className="grid items-start gap-6 xl:grid-cols-[15rem_minmax(0,1fr)]">
      <aside className="rounded-lg border border-border bg-panel p-4" aria-label="Saved research studies">
        <div className="flex items-center justify-between gap-3">
          <h2 className="m-0 text-base font-semibold text-foreground">Your studies</h2>
          <button type="button" disabled={busy} onClick={saved.create}
            className="min-h-11 rounded-md px-3 text-sm font-semibold text-accent disabled:opacity-50">New study</button>
        </div>
        <div className="mt-3 flex gap-2 overflow-x-auto xl:max-h-[28rem] xl:flex-col xl:overflow-y-auto">
          {saved.library.studies.map((item) => (
            <button key={item.id} type="button" disabled={busy} aria-pressed={item.id === study.id}
              onClick={() => saved.select(item.id)}
              className={`min-h-16 min-w-40 rounded-md border p-3 text-left disabled:opacity-50 ${item.id === study.id ? 'border-accent bg-subtle' : 'border-border'}`}>
              <span className="block break-words text-sm font-semibold text-foreground">{studyTitle(item)}</span>
              <span className="mt-1 block text-xs text-muted">{item.attempts.length ? `${item.attempts.length} saved ${item.attempts.length === 1 ? 'attempt' : 'attempts'}` : 'Draft'}</span>
            </button>
          ))}
        </div>
        <p className="mt-4 mb-0 text-xs leading-5 text-muted">
          Drafts and attempt links are saved in this browser for this workspace.
          Backtest results also remain in <a className="text-accent underline" href="/experiments/">History</a>.
        </p>
      </aside>
      <div className="min-w-0">
        {saved.warning ? <p role="alert" className="mb-4 rounded-md border border-warning/45 p-4 text-sm text-warning">{saved.warning}</p> : null}
        <label className="mb-5 block text-sm font-medium text-secondary">
          Study name
          <input value={study.name} placeholder={studyTitle(study)} maxLength={120}
            onChange={(event) => saved.update(study.id, { name: event.target.value })}
            className="mt-2 min-h-12 w-full rounded-md border border-border bg-panel px-4 text-lg font-semibold text-foreground" />
        </label>
        <PairResearch key={study.id} apiClient={apiClient} queries={queries} workspace={workspace}
          study={study} onChange={(patch) => saved.update(study.id, patch)}
          onAttempt={(id, question) => saved.recordAttempt(study.id, id, question)} onBusyChange={setBusy} />
      </div>
    </div>
  )
}
