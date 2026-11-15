import { useState } from 'react'
import type { LabAnalysis } from './labContract'
import type { LabStudy } from './labStudyApi'

interface LabTradeDrawerProps {
  analysis: LabAnalysis
  study: LabStudy | null
}

type DrawerTab = 'trades' | 'folds' | 'provenance'

export function LabTradeDrawer({ analysis, study }: LabTradeDrawerProps) {
  const [selectedTab, setSelectedTab] = useState<DrawerTab | null>(null)
  const trades = study?.result.trades ?? []
  const folds = study?.result.folds ?? []
  const activeTab: DrawerTab = selectedTab ?? (study ? 'trades' : 'provenance')

  return (
    <details className="lab-audit" aria-label="Trade and audit drawer">
      <summary>
        Where the data comes from &amp; audit trail
        <span className="lab-note">
          {analysis.bars_used.toLocaleString()} bars through {new Date(analysis.data_through).toLocaleString()}
          {study ? ` · ${trades.length} swaps · ${folds.length} folds` : ''}
        </span>
      </summary>

      <div className="lab-drawer-tabs" role="tablist" aria-label="Audit views">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'trades'}
          onClick={() => setSelectedTab('trades')}
        >
          Simulated Swaps ({trades.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'folds'}
          onClick={() => setSelectedTab('folds')}
        >
          Walk-Forward Folds ({folds.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'provenance'}
          onClick={() => setSelectedTab('provenance')}
        >
          Dataset Provenance ({analysis.datasets.length})
        </button>
      </div>

      {activeTab === 'trades' && (
        <div className="lab-audit-scroll" role="tabpanel">
          {trades.length === 0 ? (
            <p className="lab-note">No simulated swaps in the active study.</p>
          ) : (
            <table>
              <caption>Simulated validation swaps</caption>
              <thead>
                <tr>
                  <th>Time (UTC)</th>
                  <th>Direction</th>
                  <th>Route</th>
                  <th>Fees (USDT)</th>
                  <th>Slippage (USDT)</th>
                  <th>Fills</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade, index) => (
                  <tr key={`${trade.fill_index}-${index}`}>
                    <td>{new Date(trade.time).toISOString().slice(0, 16).replace('T', ' ')}</td>
                    <td>{trade.direction}</td>
                    <td>{trade.route}</td>
                    <td>{Number(trade.fees_usdt).toFixed(4)}</td>
                    <td>{Number(trade.slippage_usdt).toFixed(4)}</td>
                    <td>{trade.fills.length} leg(s)</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'folds' && (
        <div className="lab-audit-scroll" role="tabpanel">
          {folds.length === 0 ? (
            <p className="lab-note">Run a strategy test to inspect walk-forward validation folds.</p>
          ) : (
            <table>
              <caption>Walk-forward validation folds</caption>
              <thead>
                <tr>
                  <th>Fold</th>
                  <th>Test Window</th>
                  <th>Strategy Return</th>
                  <th>Control Return</th>
                  <th>Passed</th>
                </tr>
              </thead>
              <tbody>
                {folds.map((fold, index) => {
                  const row = fold as Record<string, unknown>
                  const stratRet = typeof row.strategy_return_pct === 'number'
                    ? row.strategy_return_pct
                    : typeof row.vs_hodl_pct === 'number'
                      ? row.vs_hodl_pct
                      : null
                  const ctrlRet = typeof row.control_return_pct === 'number'
                    ? row.control_return_pct
                    : typeof row.vs_control_pct === 'number'
                      ? row.vs_control_pct
                      : null
                  const startRaw = row.test_start ?? row.start
                  const endRaw = row.test_end ?? row.end
                  const windowText = startRaw && endRaw
                    ? `${String(startRaw).slice(0, 10)} → ${String(endRaw).slice(0, 10)}`
                    : `Fold ${index + 1}`
                  const passedVal = typeof row.passes === 'boolean'
                    ? row.passes
                    : typeof row.passed === 'boolean'
                      ? row.passed
                      : null
                  return (
                    <tr key={index}>
                      <td>{String(row.fold ?? index + 1)}</td>
                      <td>{windowText}</td>
                      <td>{stratRet !== null ? `${stratRet >= 0 ? '+' : ''}${stratRet.toFixed(2)}%` : '—'}</td>
                      <td>{ctrlRet !== null ? `${ctrlRet >= 0 ? '+' : ''}${ctrlRet.toFixed(2)}%` : '—'}</td>
                      <td>{passedVal === true ? 'Yes' : passedVal === false ? 'No' : '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'provenance' && (
        <div role="tabpanel">
          <p className="lab-note">
            Read from immutable market data.
            {study && (
              <>
                {' '}Execution route: <strong>{study.result.execution_route}</strong> · Code fingerprint:{' '}
                <code>{study.result.code_fingerprint.slice(0, 12)}</code>
              </>
            )}
          </p>
          <div className="lab-audit-scroll">
            <table>
              <caption>Exact dataset versions</caption>
              <thead>
                <tr>
                  <th>Market</th>
                  <th>Interval</th>
                  <th>Fingerprint</th>
                  <th>Data through</th>
                </tr>
              </thead>
              <tbody>
                {analysis.datasets.map((dataset) => (
                  <tr key={dataset.dataset_id}>
                    <td>{dataset.venue_symbol}</td>
                    <td>{dataset.interval}</td>
                    <td><code>{dataset.semantic_fingerprint}</code></td>
                    <td>{dataset.cutoff}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </details>
  )
}
