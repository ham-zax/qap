import type { LabSavedSummary } from './labStudyApi'

interface LabSavedRunsProps {
  studies: readonly LabSavedSummary[]
  activeStudyId: string | null
  loading: boolean
  onSelect: (studyId: string) => void
  onTogglePin: (studyId: string, pinned: boolean) => void
}

export function LabSavedRuns({
  studies,
  activeStudyId,
  loading,
  onSelect,
  onTogglePin,
}: LabSavedRunsProps) {
  return (
    <section className="lab-card lab-saved-card" aria-label="Saved and pinned studies">
      <div className="lab-card-header">
        <h3>Saved &amp; Pinned Studies</h3>
        {studies.length > 0 && <span className="lab-chip">{studies.length}</span>}
      </div>

      {loading && studies.length === 0 ? (
        <p className="lab-note">Loading saved studies…</p>
      ) : studies.length === 0 ? (
        <p className="lab-note">No saved studies yet. Run a test to record it here.</p>
      ) : (
        <ul className="lab-saved-list">
          {studies.map((row) => {
            const active = row.study_id === activeStudyId
            return (
              <li key={row.study_id} className={active ? 'lab-saved-item lab-saved-active' : 'lab-saved-item'}>
                <button
                  type="button"
                  className="lab-saved-open"
                  onClick={() => onSelect(row.study_id)}
                >
                  <span className="lab-saved-pair">
                    {row.coin_a.code}/{row.coin_b.code} · {row.method}
                  </span>
                  <span className="lab-saved-headline">{row.headline}</span>
                </button>
                <button
                  type="button"
                  className="lab-saved-pin"
                  aria-label={row.pinned ? `Unpin ${row.coin_a.code}/${row.coin_b.code}` : `Pin ${row.coin_a.code}/${row.coin_b.code}`}
                  aria-pressed={row.pinned}
                  onClick={() => onTogglePin(row.study_id, !row.pinned)}
                >
                  {row.pinned ? 'Pinned' : 'Pin'}
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
