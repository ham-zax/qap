import { BAR_MINUTES, type LabAnalysis, type LabBar, type LabHedgeMethod, type LabSignalMethod, type LabStrategyFormSettings } from './labContract'

export const METHOD_SHORT_LABELS: Record<LabSignalMethod, string> = {
  zscore: 'Mean Reversion (Z-Score)',
  copula: 'Spread Copula',
  trend: 'Ratio Trend',
  lead_lag: 'Anchor Lead-Lag',
}

export function barSpan(bars: number, bar: LabBar): string {
  const minutes = bars * BAR_MINUTES[bar]
  if (!Number.isFinite(minutes) || minutes <= 0) return '0 bars'
  if (minutes < 60) return `${Math.round(minutes)} min`
  if (minutes < 1440) return `${(minutes / 60).toFixed(1)} h`
  return `${(minutes / 1440).toFixed(1)} days`
}

function approxTailPct(z: number): string {
  const t = 1 / (1 + 0.2316419 * Math.abs(z))
  const d = 0.3989423 * Math.exp((-z * z) / 2)
  const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
  const twoTail = Math.max(0.01, Math.min(99, 2 * p * 100))
  return twoTail >= 10 ? `${twoTail.toFixed(0)}%` : `${twoTail.toFixed(1)}%`
}

export interface StrategySelectField {
  kind: 'select'
  id: string
  label: string
  options: ReadonlyArray<{ value: string; label: string }>
  getValue: (settings: LabStrategyFormSettings) => string
  patch: (value: string) => Partial<LabStrategyFormSettings>
}

export interface StrategySliderField {
  kind: 'slider'
  id: string
  label: string
  min: number
  max: number | ((settings: LabStrategyFormSettings) => number)
  step: number
  getValue: (settings: LabStrategyFormSettings) => number
  valueText: (settings: LabStrategyFormSettings) => string
  badge?: (settings: LabStrategyFormSettings, bar: LabBar) => string
  patch: (value: number, settings: LabStrategyFormSettings) => Partial<LabStrategyFormSettings>
}

export interface StrategyNumberField {
  kind: 'number'
  id: string
  label: string
  min: number
  max: number
  step?: number
  hint?: (bar: LabBar, settings: LabStrategyFormSettings) => string
  getValue: (settings: LabStrategyFormSettings) => number
  patch: (value: number) => Partial<LabStrategyFormSettings>
}

export interface StrategyNumberPairField {
  kind: 'numberPair'
  id: string
  fields: readonly [StrategyNumberField, StrategyNumberField]
}

export interface StrategyNoteField {
  kind: 'note'
  id: string
  text: (settings: LabStrategyFormSettings) => string
}

export type StrategyFieldSpec =
  | StrategySelectField
  | StrategySliderField
  | StrategyNumberField
  | StrategyNumberPairField
  | StrategyNoteField

export interface StrategyDescriptor {
  id: LabSignalMethod
  buttonLabel: string
  badge?: string
  badgeTitle?: string
  requires1m?: boolean
  requiresAnchorMessage?: (analysis: LabAnalysis | null) => string | null
  fields: readonly StrategyFieldSpec[]
}

const LOOKBACK_SLIDER: StrategySliderField = {
  kind: 'slider',
  id: 'lookback',
  label: 'Lookback (bars)',
  min: 24,
  max: 720,
  step: 12,
  getValue: (s) => s.lookback,
  valueText: (s) => `${s.lookback}`,
  badge: (s, bar) => barSpan(s.lookback, bar),
  patch: (lookback) => ({ lookback }),
}

export const STRATEGY_REGISTRY: Record<LabSignalMethod, StrategyDescriptor> = {
  zscore: {
    id: 'zscore',
    buttonLabel: 'Z-Score',
    fields: [
      {
        kind: 'select',
        id: 'hedge_method',
        label: 'Regression',
        options: [
          { value: 'ratio', label: 'Direct Ratio (1:1)' },
          { value: 'ols', label: 'Rolling OLS (non-stationary possible)' },
          { value: 'tls', label: 'Rolling TLS (non-stationary possible)' },
          { value: 'kalman', label: 'Adaptive Kalman β' },
        ],
        getValue: (s) => s.hedge_method,
        patch: (value) => ({ hedge_method: value as LabHedgeMethod }),
      },
      LOOKBACK_SLIDER,
      {
        kind: 'slider',
        id: 'entry',
        label: 'Entry (σ)',
        min: 0.5,
        max: 4.5,
        step: 0.1,
        getValue: (s) => s.entry,
        valueText: (s) => `${s.entry.toFixed(1)}σ`,
        badge: (s) => `~${approxTailPct(s.entry)} tail`,
        patch: (entry, s) => ({
          entry,
          exit: s.exit >= entry ? Math.max(0, Number((entry - 0.1).toFixed(1))) : s.exit,
        }),
      },
      {
        kind: 'slider',
        id: 'exit',
        label: 'Exit (σ)',
        min: 0,
        max: (s) => Math.max(0, Math.min(2.5, Number((s.entry - 0.1).toFixed(1)))),
        step: 0.1,
        getValue: (s) => {
          const exitMax = Math.max(0, Math.min(2.5, Number((s.entry - 0.1).toFixed(1))))
          return Math.min(s.exit, exitMax)
        },
        valueText: (s) => `${s.exit.toFixed(1)}σ`,
        badge: (s) => `< ${s.entry.toFixed(1)}σ`,
        patch: (exit) => ({ exit }),
      },
    ],
  },
  copula: {
    id: 'copula',
    buttonLabel: 'Spread Copula',
    fields: [
      LOOKBACK_SLIDER,
      {
        kind: 'slider',
        id: 'copula_probability',
        label: 'Tail Entry Rank',
        min: 0.01,
        max: 0.25,
        step: 0.01,
        getValue: (s) => s.copula_probability,
        valueText: (s) => `${Math.round(s.copula_probability * 100)}%`,
        patch: (copula_probability, s) => ({
          copula_probability,
          copula_exit_band: Math.min(
            s.copula_exit_band,
            Math.max(0.05, Number((0.49 - copula_probability).toFixed(2))),
          ),
        }),
      },
      {
        kind: 'slider',
        id: 'copula_exit_band',
        label: 'Neutral Rank Band',
        min: 0.05,
        max: (s) => Math.max(0.05, Math.min(0.35, Number((0.49 - s.copula_probability).toFixed(2)))),
        step: 0.01,
        getValue: (s) => {
          const max = Math.max(0.05, Math.min(0.35, Number((0.49 - s.copula_probability).toFixed(2))))
          return Math.min(s.copula_exit_band, max)
        },
        valueText: (s) => `${Math.round(s.copula_exit_band * 100)}%`,
        patch: (copula_exit_band) => ({ copula_exit_band }),
      },
      {
        kind: 'note',
        id: 'copula_hint',
        text: (s) => {
          const entry = Math.round(s.copula_probability * 100)
          const band = Math.round(s.copula_exit_band * 100)
          return `Conditional rank only (not a recovery probability): enter below ${entry}% / above ${100 - entry}%, exit between ${50 - band}%–${50 + band}%.`
        },
      },
    ],
  },
  trend: {
    id: 'trend',
    buttonLabel: 'Ratio Trend',
    fields: [
      {
        kind: 'numberPair',
        id: 'trend_windows',
        fields: [
          {
            kind: 'number',
            id: 'fast_window',
            label: 'Fast MA (bars)',
            min: 2,
            max: 1000,
            hint: (bar, s) => barSpan(s.fast_window, bar),
            getValue: (s) => s.fast_window,
            patch: (fast_window) => ({ fast_window }),
          },
          {
            kind: 'number',
            id: 'slow_window',
            label: 'Slow MA (bars)',
            min: 3,
            max: 10000,
            hint: (bar, s) => barSpan(s.slow_window, bar),
            getValue: (s) => s.slow_window,
            patch: (slow_window) => ({ slow_window }),
          },
        ],
      },
      {
        kind: 'number',
        id: 'trend_deadband',
        label: 'Deadband',
        min: 0,
        max: 0.5,
        step: 0.0005,
        getValue: (s) => s.trend_deadband,
        patch: (trend_deadband) => ({ trend_deadband }),
      },
    ],
  },
  lead_lag: {
    id: 'lead_lag',
    buttonLabel: 'Anchor Lead-Lag',
    badge: '1m',
    badgeTitle: 'Requires 1m candles',
    requires1m: true,
    requiresAnchorMessage: (analysis) =>
      analysis && !analysis.anchor
        ? 'No auto-detected benchmark covers this full window. Select a Benchmark in the top bar for Anchor Lead-Lag.'
        : null,
    fields: [
      LOOKBACK_SLIDER,
      {
        kind: 'number',
        id: 'anchor_threshold',
        label: 'Benchmark Jump Threshold',
        min: 0.0001,
        max: 0.5,
        step: 0.0005,
        getValue: (s) => s.anchor_threshold,
        patch: (anchor_threshold) => ({ anchor_threshold }),
      },
    ],
  },
}

export const STRATEGY_METHODS: readonly StrategyDescriptor[] = [
  STRATEGY_REGISTRY.zscore,
  STRATEGY_REGISTRY.copula,
  STRATEGY_REGISTRY.trend,
  STRATEGY_REGISTRY.lead_lag,
]
