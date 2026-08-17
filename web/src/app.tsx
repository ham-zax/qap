import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  RouterProvider,
  createRouter,
  type RouterHistory,
} from '@tanstack/react-router'

import { createApiClient } from './api/client'
import { createQapQueries } from './api/queries'
import { routeTree } from './routeTree.gen'

interface CreateQapAppOptions {
  baseUrl?: string
  fetchImpl?: typeof fetch
  history?: RouterHistory
}

export function createQapApp(options: CreateQapAppOptions = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        staleTime: 30_000,
      },
    },
  })
  const apiClient = createApiClient({
    baseUrl: options.baseUrl ?? '',
    ...(options.fetchImpl ? { fetchImpl: options.fetchImpl } : {}),
  })
  const queries = createQapQueries(apiClient)
  const router = createRouter({
    routeTree,
    ...(options.history ? { history: options.history } : {}),
    context: { queryClient, queries },
    defaultPreload: 'intent',
  })

  return { queryClient, router }
}

export type QapRouter = ReturnType<typeof createQapApp>['router']

declare module '@tanstack/react-router' {
  interface Register {
    router: QapRouter
  }
}

export function App({
  queryClient,
  router,
}: ReturnType<typeof createQapApp>) {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
