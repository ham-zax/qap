import type { LabViewMode } from './labContract'
import type { LabAdvisor, LabAdvisorSuggestion } from './labStudyApi'

interface LabAdvisorCardProps {
  advisor: LabAdvisor | null
  loading: boolean
  viewMode: LabViewMode
  disabled: boolean
  onApplyPreset: (suggestion: LabAdvisorSuggestion) => void
}

const REGIME_LABELS: Record<string, string> = {
  mean_reverting: 'Mean reverting',
  trending: 'Trending',
  mixed_or_noisy: 'Mixed / noisy',
}

export function LabAdvisorCard({
  advisor,
  loading,
  viewMode,
  disabled,
  onApplyPreset,
}: LabAdvisorCardProps) {
  return (
    <section className="lab-card lab-advisor-card" aria-label="Smart Strategy Advisor">
      <div className="lab-card-header">
        <h3>Smart Strategy Advisor</h3>
        {advisor && (
          <span className="lab-chip">
            {REGIME_LABELS[advisor.regime_label] ?? advisor.regime_label}
          </span>
        )}
      </div>

      {loading && !advisor ? (
        <p className="lab-note">Analyzing pair regime and preset fit…</p>
      ) : !advisor ? (
        <p className="lab-note">Load a pair to see regime-matched preset suggestions.</p>
      ) : (
        <>
          <p className="lab-advisor-summary">
            {viewMode === 'advanced' ? advisor.pro_summary : advisor.simple_summary}
          </p>
          {advisor.bar_warning && (
            <p className="lab-warning-banner" role="note">
              {advisor.bar_warning}
            </p>
          )}
          <div className="lab-preset-list">
            {advisor.suggestions.map((suggestion) => (
              <article key={suggestion.preset_id} className="lab-preset-card">
                <div className="lab-preset-top">
                  <strong>{suggestion.title}</strong>
                  <span className="lab-preset-meta">
                    {suggestion.recommended_bar}
                    {suggestion.recommended_anchor
                      ? ` · ${suggestion.recommended_anchor.replace('binance:', '')}`
                      : ''}
                  </span>
                </div>
                <p className="lab-note">
                  {viewMode === 'advanced' ? suggestion.pro_reason : suggestion.simple_reason}
                </p>
                <button
                  type="button"
                  className="lab-preset-apply"
                  disabled={disabled}
                  onClick={() => onApplyPreset(suggestion)}
                >
                  Apply &amp; Test
                </button>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  )
}
