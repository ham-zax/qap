import type { AnchorLensDto } from '../../api/types'
import {
  SynchronizedChartGroup,
  type SynchronizedChartSpec,
} from '../../components/charts/SynchronizedChartGroup'
import { StatusMessage } from '../../components/StatusMessage'

interface AnchorLensPanelProps {
  anchor: string
  data: AnchorLensDto | null
}

export function AnchorLensPanel({ anchor, data }: AnchorLensPanelProps) {
  if (anchor === 'none') {
    return (
      <StatusMessage title="Choose an anchor" tone="warning">
        <p>Select an anchor admitted by this run before opening the anchor lens.</p>
      </StatusMessage>
    )
  }
  if (!data) {
    return (
      <StatusMessage title="Anchor evidence unavailable" tone="error">
        <p>The requested anchor lens was not returned by the API.</p>
      </StatusMessage>
    )
  }

  const [base, quote] = data.requested_orientation.split('/')
  const anchorIsBase = data.reduction === 'anchor_is_base'
  const anchorIsQuote = data.reduction === 'anchor_is_quote'
  const identityLabel = anchorIsBase
    ? `${base}/${data.anchor}`
    : anchorIsQuote
      ? `${quote}/${data.anchor}`
      : null
  const anchorRatioSeries = anchorIsBase
    ? [
        {
          name: `${quote}/${data.anchor}`,
          unit: 'anchor ratio',
          points: data.quote_to_anchor,
        },
      ]
    : anchorIsQuote
      ? [
          {
            name: `${base}/${data.anchor}`,
            unit: 'anchor ratio',
            points: data.base_to_anchor,
          },
        ]
      : [
          {
            name: `${base}/${data.anchor}`,
            unit: 'anchor ratio',
            points: data.base_to_anchor,
          },
          {
            name: `${quote}/${data.anchor}`,
            unit: 'anchor ratio',
            points: data.quote_to_anchor,
          },
        ]
  const anchorLogSeries = anchorIsBase
    ? [
        {
          name: `${quote}/${data.anchor}`,
          unit: 'log anchor ratio',
          points: data.quote_to_anchor_log,
        },
        {
          name: data.requested_orientation,
          unit: 'pair log ratio',
          points: data.pair_log_ratio,
        },
      ]
    : anchorIsQuote
      ? [
          {
            name: `${base}/${data.anchor}`,
            unit: 'log anchor ratio',
            points: data.base_to_anchor_log,
          },
          {
            name: data.requested_orientation,
            unit: 'pair log ratio',
            points: data.pair_log_ratio,
          },
        ]
      : [
          {
            name: `${base}/${data.anchor}`,
            unit: 'log anchor ratio',
            points: data.base_to_anchor_log,
          },
          {
            name: `${quote}/${data.anchor}`,
            unit: 'log anchor ratio',
            points: data.quote_to_anchor_log,
          },
          {
            name: data.requested_orientation,
            unit: 'pair log ratio',
            points: data.pair_log_ratio,
          },
        ]
  const reducedTitle = anchorIsBase
    ? `${quote}/${data.anchor} reduced anchor path`
    : `${base}/${data.anchor} reduced anchor path`
  const charts: SynchronizedChartSpec[] = [
    {
      key: 'pair-ratio',
      title: `${data.requested_orientation} ratio`,
      description: 'Direct pair ratio from the admitted aligned dataset.',
      series: [
        {
          name: data.requested_orientation,
          unit: 'ratio',
          points: data.pair_ratio,
        },
      ],
    },
    {
      key: 'anchor-ratios',
      title: identityLabel ? reducedTitle : `${data.anchor} anchor paths`,
      description: identityLabel
        ? 'Only the non-identity anchor leg is plotted.'
        : 'Each requested leg expressed against the common anchor.',
      series: anchorRatioSeries,
    },
    {
      key: 'anchor-logs',
      title: `${data.anchor} log decomposition`,
      description: identityLabel
        ? 'The non-identity log leg and pair log ratio preserve the reduced identity.'
        : 'Log anchor legs whose difference reconstructs the pair log ratio.',
      series: anchorLogSeries,
    },
  ]

  return (
    <section aria-labelledby="anchor-lens-heading">
      <h2 id="anchor-lens-heading">Anchor decomposition</h2>
      <dl>
        <div>
          <dt>Requested orientation</dt>
          <dd>{data.requested_orientation}</dd>
        </div>
        <div>
          <dt>Anchor</dt>
          <dd>{data.anchor}</dd>
        </div>
        <div>
          <dt>Reduction</dt>
          <dd>{data.reduction}</dd>
        </div>
        <div>
          <dt>Identity coordinates</dt>
          <dd>{data.identity_coordinate_assets.join(', ') || 'none'}</dd>
        </div>
        <div>
          <dt>Maximum ratio identity error</dt>
          <dd>{data.max_ratio_decomposition_error}</dd>
        </div>
        <div>
          <dt>Maximum log identity error</dt>
          <dd>{data.max_log_decomposition_error}</dd>
        </div>
      </dl>
      <p>Anchor is context/decomposition, not portfolio target authority.</p>
      {identityLabel ? (
        <p>{identityLabel} is the identity path at 1 and is not plotted.</p>
      ) : null}
      <p>Descriptive decomposition only; no causal or tradable claim is implied.</p>
      <SynchronizedChartGroup charts={charts} label="Synchronized anchor charts" />
    </section>
  )
}
