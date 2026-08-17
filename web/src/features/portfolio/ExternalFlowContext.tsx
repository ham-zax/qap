import type { ExperimentDetailDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'
import { formatSignedDecimal, formatResearchTimestamp } from '../../lib/format'

interface ExternalFlowContextProps {
  experiment: ExperimentDetailDto
}

export function ExternalFlowContext({ experiment }: ExternalFlowContextProps) {
  const flows = experiment.manifest.external_flows
  if (flows.length === 0) {
    return (
      <section
        className="rounded-lg border border-border bg-panel p-5 md:p-6"
        aria-labelledby="external-flow-heading"
      >
        <h2 id="external-flow-heading" className="mb-2 text-lg font-semibold text-foreground">
          External flows
        </h2>
        <p className="m-0 text-sm text-secondary">No exogenous external flows were declared for this run.</p>
      </section>
    )
  }

  return (
    <section
      className="rounded-lg border border-border bg-panel p-5 md:p-6"
      aria-labelledby="external-flow-heading"
    >
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="external-flow-heading" className="mb-1 text-lg font-semibold text-foreground">
            External flows
          </h2>
          <p className="m-0 max-w-3xl text-sm leading-6 text-secondary">
            The same exogenous flow stream is applied across compared roles;
            matched-contribution static HODL remains the accumulation control.
          </p>
        </div>
        <span className="text-sm tabular-nums text-muted">{flows.length} declared</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {flows.slice(0, 4).map((flow) => {
          const quantity = formatSignedDecimal(flow.quantity_delta, 4)
          return (
            <div key={flow.flow_id} className="rounded-md border border-border bg-canvas/35 p-3">
              <p className="m-0 text-xs text-muted">{formatResearchTimestamp(flow.effective_time)}</p>
              <p className="mt-1 mb-0 font-medium text-foreground">
                {flow.asset}{' '}
                <span className="tabular-nums" data-exact={quantity.exact}>{quantity.display}</span>
              </p>
            </div>
          )
        })}
      </div>

      <details className="mt-4 rounded-md border border-border bg-canvas/35 p-4">
        <summary className="cursor-pointer font-semibold text-foreground">Flow audit</summary>
        <div className="mt-4 space-y-4">
          <TableScroll label="Declared exogenous flows">
            <table aria-label="Declared exogenous flows">
              <thead>
                <tr>
                  <th scope="col">Flow ID</th>
                  <th scope="col">Effective time</th>
                  <th scope="col">Asset</th>
                  <th scope="col">Quantity delta</th>
                </tr>
              </thead>
              <tbody>
                {flows.map((flow) => (
                  <tr key={flow.flow_id}>
                    <th scope="row">{flow.flow_id}</th>
                    <td>{flow.effective_time}</td>
                    <td>{flow.asset}</td>
                    <td><ExactNumber value={flow.quantity_delta} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableScroll>
          <div>
            <h3 className="mb-2 text-sm font-semibold text-foreground">Role flow-ID audit</h3>
            <ul className="m-0 space-y-1 pl-5 text-sm text-secondary">
              {experiment.result.roles.map((role) => (
                <li key={role.role}>
                  {role.role}: {role.external_flow_ids.join(', ') || 'none'}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </details>
    </section>
  )
}
