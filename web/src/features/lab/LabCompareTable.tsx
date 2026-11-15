import type { LabCompareResult } from './labStudyApi'

interface LabCompareTableProps {
  compare: LabCompareResult
  onOpenStudy: (studyId: string) => void
  onClose: () => void
}

function pct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

export function LabCompareTable({ compare, onOpenStudy, onClose }: LabCompareTableProps) {
  return (
    <section className="lab-card lab-compare-panel" aria-label="Preset comparison">
      <div className="lab-card-header">
        <div>
          <h2>Preset Comparison ({compare.studies.length} candidates)</h2>
          <p className="lab-note">{compare.advisor.simple_summary}</p>
        </div>
        <button type="button" onClick={onClose}>Close comparison</button>
      </div>

      <div className="lab-audit-scroll">
        <table>
          <thead>
            <tr>
              <th>Method</th>
              <th>Hedge / Lookback</th>
              <th>vs HODL</th>
              <th>vs Control</th>
              <th>Folds</th>
              <th>Swaps</th>
              <th>Verdict</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {compare.studies.map((item) => {
              const best = item.study_id === compare.best_study_id
              const applied = item.result.applied_settings
              return (
                <tr key={item.study_id} className={best ? 'lab-compare-best' : undefined}>
                  <td>
                    <strong>{applied.method}</strong>
                    {best && <span className="lab-chip">Best</span>}
                  </td>
                  <td>{applied.hedge_method} · {applied.lookback}</td>
                  <td className={(item.result.proof.vs_hodl_pct ?? 0) > 0 ? 'lab-proof-better' : 'lab-proof-worse'}>
                    {pct(item.result.proof.vs_hodl_pct)}
                  </td>
                  <td className={(item.result.proof.vs_control_pct ?? 0) > 0 ? 'lab-proof-better' : 'lab-proof-worse'}>
                    {pct(item.result.proof.vs_control_pct)}
                  </td>
                  <td>{item.result.proof.folds_passing}/{item.result.proof.folds_total}</td>
                  <td>{item.result.proof.validation_trades}</td>
                  <td>{item.result.call.headline}</td>
                  <td>
                    <button type="button" onClick={() => onOpenStudy(item.study_id)}>
                      Inspect
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
