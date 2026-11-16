import { readoutSentence, type Readout } from './labReadout'
import './LabReadout.css'

/**
 * Values under the crosshair. Pointer users see the hovered bar. Without a hovered
 * bar the strip shows the latest bar. Screen readers get one stable sentence about
 * the latest bar, so hover movement never floods a live region.
 */
export function LabReadout({ title, current, latest }: { title: string; current: Readout | null; latest: Readout | null }) {
  if (!current || !latest) return null
  return <div className="lab-readout">
    <p className="sr-only">{readoutSentence(title, latest)}</p>
    <div className="lab-readout-strip" aria-hidden="true" data-latest={current.latest}>
      <p className="lab-readout-time"><span>{current.latest ? 'Latest bar' : 'Hovered bar'}</span><time>{current.time}</time></p>
      <dl>
        {current.rows.map((row) => <div key={row.key} className={row.value === 'Unavailable' ? 'lab-readout-unavailable' : undefined}>
          <dt>{row.swatch && <i className={row.swatch.dashed ? 'lab-swatch lab-swatch-dashed' : 'lab-swatch'} style={{ color: `var(${row.swatch.token})` }} />}{row.label}</dt>
          <dd>{row.value}</dd>
        </div>)}
      </dl>
    </div>
  </div>
}
