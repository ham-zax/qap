# Research Study Workspace Implementation Plan

Update context — 2026-09-24 (user rejected the resulting UX)
Trigger: the user requested a simpler experience and then a plan before further implementation.
Purpose: retain the technical work record without treating it as accepted UX.
Impact: this presentation direction is superseded by the
[proposed intuitive research experience plan](2026-09-24-intuitive-research-experience.md).
Further implementation is paused for that plan review. The verification record
below describes the first iteration only, before the provisional header/help edits.

> Historical execution instruction: infer interaction details and proceed. The
> user's subsequent plan-first instruction takes precedence for the next revision.

**Goal:** a resumable pair-research study with understandable setup and conclusions.
**Architecture:** browser-local intent/references over existing backend authority.
**Tech Stack:** existing React, TanStack Query, TypeScript, Vitest; no dependencies.
**Spec:** `docs/superpowers/specs/2026-09-24-research-study-workspace.md`.

## Global constraints

Preserve economic/identity/admission/holdout semantics. Never persist browser-computed
economics or grant approval from saved state. Use CLI only. No browser automation.
Keep handwritten modules below 500 lines where practical, always below 700.

## Review focus

Workspace identity changes; corrupt/unavailable local storage; leaving during a run;
editing the question while an older response is pending; failure of downstream
support after successful relationship analysis. Earlier attempts remain discoverable.

## Tasks

- [x] 1. Add `researchStudies.ts`, its storage/transition tests, and
  `useResearchStudies.ts`. Versioned workspace-scoped intent + operation references;
  validate unknown persisted input, preserve bad data, expose storage warnings.
- [x] 2. Add `ResearchStudyWorkspace.tsx` for selection/name/new-study/attempt history.
  Refactor `PairResearch.tsx` into a bounded controller plus `PairResearchSetup.tsx`.
  Wire persisted intent, independent study/support reads, explicit progress and resume.
- [x] 3. Add in-place public directory and quote-identity setup. Preserve explicit
  identity/admission decisions and update backend queries after each maintenance action.
- [x] 4. Add `PairExperimentPreview.tsx` for backend-declared test summaries;
  add labeled parameter controls to `RecipeAuthoringControls.tsx`/`ExperimentLab.tsx`.
- [x] 5. Reorganize `PairResearchCompletion.tsx`: conclusion and comparison first,
  chart and understandable methods, optional technical detail, resumable operation reads.
  Simplify `ResearchHome.tsx` copy and move specialist tools behind disclosure.
- [x] 6. Run focused CLI tests, frontend typecheck/build, source-size and diff checks;
  review failure/resume paths and update this ledger with actual results.

## Execution decisions

- Use a feature branch in the existing clean checkout to preserve the installed local
  environment and keep the result directly reviewable. No live workspace data writes.
- The user's execution authorization covers this accepted design and its inferred
  details. No further design/plan approval loop is needed.
- Focused CLI regression tests implement the global AGENTS verification requirement;
  historical M11 test restrictions remain historical, rather than a new testing ban.
- Human acceptance remains pending; it cannot be replaced by an agent's completion claim.
- Cross-tab changes do not replace an in-flight question. The tab warns and retains
  session-only edits until reload, preserving the other tab's saved library. This is
  conflict detection, not a multi-writer synchronization protocol.
- Experiment Lab remains a single authoring form (675 lines, below the 700-line
  limit); added numerical controls live in the separate authoring-controls module.
  Pair controller and result rendering were decomposed below 500 lines.

## Verification record

Update context — 2026-09-24
Trigger: implementation and CLI verification of the authorized correction.
Purpose: record actual checks and prevent technical completion from implying human acceptance.
Impact: no scientific/economic contract changes; existing unrelated gate failures remain explicit.
Evidence: new discovery regression tests and current-vs-HEAD test comparison.

- **Passed:** `pnpm exec vitest run src/features/discovery` — 21 tests across
  storage validation, workspace separation, explicit quote-identity confirmation,
  busy-state protection, reload/resume, delayed start after navigation, cross-tab
  conflict handling, independent relationship/support failures, parameter recheck,
  exact backend recipe launch, verdict preservation and provenance disclosure.
- **Passed:** `pnpm typecheck`; final `pnpm build` (also includes TypeScript checking).
- **Passed:** `git diff --check`; final inline source/diff inspection.
- **Failed, pre-existing:** full `pnpm exec vitest run` — 64 passed / 6 failed.
  The same six failures reproduce on an isolated unchanged HEAD (`dfaa8c2`):
  `app.test.tsx` (2), `BasketDetail`, `ExperimentList`, `OperationList`,
  `PortfolioOverview` (1 each). No unrelated tests were weakened to turn this green.
- **Failed, pre-existing:** `uv run --no-sync python scripts/check_source_size.py`
  — unchanged `src/qap/market/adapters/binance_public.py` has 758 lines on HEAD and
  this branch. Changed/new frontend modules remain below 700 lines.
- **Not run:** browser/Playwright (explicitly prohibited), real public-data research,
  backend test suite (no backend changes), MFSM experiments/tests, human acceptance.

These existing failures are not repaired by expanding this frontend correction
into unrelated work. The implementation tasks are done, not the human acceptance
gate or repository-wide green-check requirement. Changes remain uncommitted on
`feat/research-study-workspace`.
