import type { QueryClient } from '@tanstack/react-query'
import { Outlet, createRootRouteWithContext } from '@tanstack/react-router'

import type { QapApiClient } from '../api/client'
import type { QapQueries } from '../api/queries'
import { AppShell } from '../components/AppShell'
import { ErrorDetails } from '../components/ErrorDetails'
import { StatusMessage } from '../components/StatusMessage'

export interface QapRouterContext {
  apiClient: QapApiClient
  queryClient: QueryClient
  queries: QapQueries
}

export const Route = createRootRouteWithContext<QapRouterContext>()({
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(context.queries.workspaceStatus()),
  component: RootLayout,
  pendingComponent: () => (
    <StatusMessage title="Loading evidence">
      <p>Reading local run artifacts.</p>
    </StatusMessage>
  ),
  errorComponent: ({ error, reset }) => (
    <AppShell>
      <StatusMessage
        title="Evidence could not be loaded"
        tone="error"
        action={<button onClick={reset}>Retry</button>}
      >
        <ErrorDetails error={error} />
      </StatusMessage>
    </AppShell>
  ),
  notFoundComponent: () => (
    <StatusMessage title="Page not found" tone="warning">
      <p>The requested analytical view does not exist.</p>
    </StatusMessage>
  ),
})

function RootLayout() {
  const workspace = Route.useLoaderData()
  return (
    <AppShell workspaceMode={workspace.workspace_mode}>
      <Outlet />
    </AppShell>
  )
}
