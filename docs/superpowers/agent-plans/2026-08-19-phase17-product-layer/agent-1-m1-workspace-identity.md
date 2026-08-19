# Agent 1 — M1 Workspace Identity and Clean Zero-State

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m1-workspace`
**Branch:** `phase17-m1-workspace`
**Isolation reason:** this mission is the only writable autonomous process in its worktree while `main` remains the stable integration/read-only base
**Can start:** immediately
**Depends on:** Phase-17 M0 design freeze at `1bb6e78`; no Wave-1 mission dependency
**Execution lifetime:** `persistent-agent-loop` required
**Wake strategy:** use bounded commands normally; if a server/watch/smoke process must persist, use Terminal + the matching event wait rather than Bash polling/sleep
**Developer visibility:** headless by default; passive presentation only if the user asks to watch a persistent process

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md` — Wave-1 ownership, integration and testing policy
- `docs/research/2026-08-19-qap-product-layer-investigation.md` — evidence that exposed the sample/real-workspace and launcher problems
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md` — frozen Product Layer authority and workspace semantics
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M1 exit criteria and downstream dependency order
- `implementation_prompt.md` — protected QAP mission/economic/action-space boundaries

Before the first repository mutation, follow the project implementation gate: `causal-coding -> ponytail -> mcp-harness-router -> mcp-harness-local`. Use `persistent-agent-loop` for mission continuity and completion gating.

## Objective

Complete Phase 17 Milestone 1 so a clean local QAP installation and an already-running QAP process are unambiguous to a nontechnical user.

The system must have a backend-owned workspace mode/identity/status, an honest `local_market` zero-state, a persistent visible Sample Workspace marker for `sample` mode, and launcher behavior that verifies the intended workspace rather than treating any QAP-looking listener or port occupancy as sufficient.

Do this without introducing M2 market-directory/admission behavior, a generic process manager, Product-maintenance persistence that M1 does not yet require, or any change to research/economic authority.

## Current state

Verified at the coordination base:

- `ApiSettings` owns operational run/data/repository/capture roots but has no workspace mode/identity.
- `/api/health` proves only that a QAP API is responding.
- `scripts/start_workbench.sh` currently declares the workbench "already running" when `/api/health` and the Vite title match, regardless of which QAP workspace the API serves.
- The current Home route loads experiments, operations and forward cohorts; it has no backend workspace-status read.
- A temporary Playwright/QA QAP process can therefore be mistaken for the intended local workspace.
- Phase 17 M2 will later own current market directory and explicit asset admission. Do not implement that here.

## Ownership

You own the complete M1 vertical behavior:

- minimal backend operational settings/state required to distinguish `sample` from `local_market` and identify the intended local workspace stably;
- the smallest read-only API contract that exposes the M1 workspace/status information required by launcher and web UI;
- any checked-in OpenAPI/client/query synchronization required by that public API change;
- local launcher comparison/error behavior for intended QAP workspace, different/sample QAP workspace, unrelated port occupancy, API/web partial state, and clean not-running state;
- primary-product presentation needed to make a clean `local_market` zero-state truthful and to keep `sample` mode visibly marked;
- focused documentation updates required to explain the resulting normal startup behavior.

Agent 2 owns only read-only reconnaissance for M2. Do not absorb current market-directory discovery, asset admission persistence, OHLCV acquisition, SQLite collector state, current-approved scanner policy, or M5 navigation restructuring.

## Coordination contract

- Workspace identity is Product operational identity only; it must not become a research/economic fingerprint or change immutable evidence identity.
- Do not derive identity from port occupancy.
- `sample` and `local_market` are the only frozen workspace modes.
- The launcher must compare the running backend's own workspace status to the workspace it intends to launch.
- A different valid QAP workspace must be distinguished from an unrelated process and from a partially running API/web pair.
- M1 may report market-data readiness as a bounded summary/zero-state using existing local evidence; it must not invent M2 market-directory or admission semantics.
- Keep existing specialist routes and research operations functional. The frozen future primary IA (`Home | Research | Portfolios | History`) is M5 work, not M1.
- If the smallest correct M1 contract would materially constrain M2 state ownership, call that out in the finish report rather than pre-building M2.

## Success conditions

- Backend owns and exposes workspace mode plus a stable workspace identity/root sufficient for launcher/UI comparison.
- A clean `local_market` workspace visibly tells the user that assets must be approved and public market data prepared before research; it does not present sample/fixture evidence as real market state.
- `sample` mode has a persistent visible Sample Workspace marker on primary product surfaces reached through the normal shell.
- `scripts/start_workbench.sh` correctly distinguishes:
  - intended QAP workspace already running;
  - another/sample QAP workspace on the expected ports;
  - unrelated process occupying API or web port;
  - only one of API/web running;
  - clean not-running state.
- The launcher still starts/stops its own backend/frontend process groups cleanly and does not become a generic process manager.
- Any public API/OpenAPI/frontend type contract changed by M1 is synchronized.
- Existing scientific/economic contracts and the seven-command mutation vocabulary are unchanged.
- The mission ends on one or more focused commits on `phase17-m1-workspace`, with the worktree clean.

## Verification intent

Testing is not authorized for this mission unless the user separately requests it or an independently authoritative repository rule mandates it.

Use direct evidence and the smallest relevant non-test checks to catch real M1 failures, for example:

- inspect/exercise workspace-status responses for both modes and differing roots;
- shell syntax and focused launcher smoke behavior against controlled port/workspace states where practical;
- focused Python type/static/OpenAPI export consistency for the changed backend contract;
- frontend typecheck/build only to the extent needed to prove the changed workspace-status/UI contract compiles and renders through the normal application boundary;
- final `git diff --check`, scoped diff inspection, branch/status evidence.

Do not run broad/full test suites or add/modify test files merely because M1 changes executable behavior.

## Out of scope

- M2 current Binance/Gate market directory.
- operator asset admission persistence/UI beyond the zero-state explanation that approval is required.
- market-data download/refresh.
- immutable market-data generation/provenance implementation.
- current-approved retrospective scanner policy/readiness.
- current-liquidity collector/SQLite persistence.
- primary IA migration to `Home | Research | Portfolios | History`.
- desktop packaging or live/private exchange capability.

## Working style

Own M1 end to end. Inspect the current code before deciding the exact API shape; prefer the smallest existing/native composition and avoid speculative Product abstractions. Preserve all unrelated work. Do not merge, rebase, reset, or switch `main` from this worktree.

Status/progress questions or compatible steering do not terminate the mission. Checkpoint meaningful state and continue until the M1 success conditions are verified, the user explicitly stops/replaces the mission, or continuation becomes unsafe/impossible.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree and commit(s);
3. resulting workspace API/launcher/UI behavior and any public contract changes;
4. checks actually run, results, and why they were relevant;
5. anything M2/integration needs to know about workspace/state ownership;
6. unresolved risks, deviations, or decisions needed.
