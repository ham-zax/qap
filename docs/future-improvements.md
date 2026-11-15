# Future improvements

Proposals from the 2026-10-23 M3 session. These entries authorize no implementation.

- **Route generation before type checks.** The first build rejected a new route
  because TypeScript ran before Vite generated the route tree. Consider an explicit
  generation step in the existing web build command. Keep the version check.
- **Recorded browser fixture.** Cached failed module imports and a live registry
  refresh delayed browser checks. Consider a development server that serves sealed
  recorded market data through the real API. Keep sample and market labels explicit.
  Reload the browser after correcting a failed module import.
- **Statistical calibration.** Hurst estimates can misclassify short random walks.
  Lead-lag peak selection also needs significance and overlap calibration. Add
  simulation-based calibration before interpreting either as a signal or proof.
- **M3 coverage.** Add non-flat anchor ranking, unequal history, missing shared bars
  and first-open bootstrap failure/retry cases. Current tests cover exact data,
  mutation refusal, finite degeneracies, eligibility, saved settings and stale results.
- **Chart layout regression.** A page overflow check missed a clipped third-party
  chart table. Add a browser check that compares the chart table width with its
  container. The session fixes the global style collision, but no new CI gate is added.

Proposals from the 2026-10-27 session. These entries authorize no implementation.

- **Launcher restarts.** `start_workbench.sh` stops every service when the API
  exits, and it does not reload Python. A stale API served old measurements, and
  a manual restart stopped another session's collector. Consider a reload flag
  for the API alone.
- **Screenshot tooling.** Windows Chrome cannot write screenshots to WSL paths.
  One four-view screenshot round took 13 min, because each fresh page prepares
  data again. Consider a warm fixture route for visual checks.
