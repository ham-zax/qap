import type { QueryClient } from '@tanstack/react-query'
import { Outlet, createRootRouteWithContext } from '@tanstack/react-router'

import type { QapQueries } from '../api/queries'
import { AppShell } from '../components/AppShell'
import { ErrorDetails } from '../components/ErrorDetails'
import { StatusMessage } from '../components/StatusMessage'

export interface QapRouterContext {
  queryClient: QueryClient
  queries: QapQueries
}

export const Route = createRootRouteWithContext<QapRouterContext>()({
  component: RootLayout,
  pendingComponent: () => (
    <StatusMessage title="Loading evidence">
      <p>Reading local run artifacts.</p>
    </StatusMessage>
  ),
  errorComponent: ({ error, reset }) => (
    <StatusMessage
      title="Evidence could not be loaded"
      tone="error"
      action={<button onClick={reset}>Retry</button>}
    >
      <ErrorDetails error={error} />
    </StatusMessage>
  ),
  notFoundComponent: () => (
    <StatusMessage title="Page not found" tone="warning">
      <p>The requested analytical view does not exist.</p>
    </StatusMessage>
  ),
})

function RootLayout() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}
