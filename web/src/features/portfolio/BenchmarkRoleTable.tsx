import type { ExperimentDetailDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'

interface BenchmarkRoleTableProps {
  roles: ExperimentDetailDto['result']['roles']
}

export function BenchmarkRoleTable({ roles }: BenchmarkRoleTableProps) {
  return (
    <section className="min-w-0" aria-labelledby="benchmark-role-heading">
      <h2 id="benchmark-role-heading" className="mb-4 text-lg font-semibold text-foreground">
        Terminal economics by role
      </h2>
      <TableScroll label="Benchmark role terminal economics">
        <table aria-label="Benchmark role terminal economics">
          <thead>
            <tr>
              <th scope="col">Role</th>
              <th scope="col">Policy</th>
              <th scope="col">Terminal value</th>
              <th scope="col">Unitized terminal value</th>
              <th scope="col">Fills</th>
              <th scope="col">Fees</th>
              <th scope="col">Slippage</th>
              <th scope="col">Turnover</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((role) => (
              <tr key={role.role}>
                <th scope="row">{role.role}</th>
                <td>{role.policy_id}</td>
                <td><ExactNumber value={role.terminal_value} /></td>
                <td><ExactNumber value={role.unitized_terminal_value} /></td>
                <td>{role.fill_count}</td>
                <td><ExactNumber value={role.fees_value} /></td>
                <td><ExactNumber value={role.slippage_value} /></td>
                <td><ExactNumber value={role.turnover_value} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
      <p className="mt-4 mb-0 text-sm leading-6 text-secondary">
        These are persisted role-level economics. Differences between rungs are
        frozen policy comparisons, not an additive causal decomposition.
      </p>
    </section>
  )
}
