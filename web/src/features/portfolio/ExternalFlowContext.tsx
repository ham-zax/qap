import type { ExperimentDetailDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'

interface ExternalFlowContextProps {
  experiment: ExperimentDetailDto
}

export function ExternalFlowContext({ experiment }: ExternalFlowContextProps) {
  const flows = experiment.manifest.external_flows
  if (flows.length === 0) {
    return (
      <section aria-labelledby="external-flow-heading">
        <h2 id="external-flow-heading">External-flow context</h2>
        <p>No exogenous external flows were declared for this run.</p>
      </section>
    )
  }

  return (
    <section aria-labelledby="external-flow-heading">
      <h2 id="external-flow-heading">External-flow context</h2>
      <p>
        Exogenous flows are declared once and applied identically across replay
        roles. Matched-contribution static HODL remains the accumulation control.
      </p>
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
      <details>
        <summary>Role flow-ID audit</summary>
        <ul>
          {experiment.result.roles.map((role) => (
            <li key={role.role}>
              {role.role}: {role.external_flow_ids.join(', ') || 'none'}
            </li>
          ))}
        </ul>
      </details>
    </section>
  )
}
