# Phase 15 — Research Scanner and Candidate Workbench Plan

**Goal:** Add an explicit active research workflow that turns an admitted portfolio/universe and predeclared model/parameter families into bounded, auditable candidate scans, control-aware ranking, portfolio-combination analysis, and a frozen candidate manifest for the next research stage.

**Architecture:** The scanner is a research orchestration layer over existing QAP authorities, not a second backtester. It may enumerate candidate specifications and schedule bounded experiment runs, but every candidate is evaluated by the existing manifest/data-role, policy, deterministic replay, accounting, cost, benchmark, and research-family contracts. The browser owns configuration/inspection only; backend QAP code owns scan definitions, execution records, ranking inputs, and candidate-freeze artifacts.

**Tech Stack:** existing Python modular monolith, immutable experiment artifacts, FastAPI/OpenAPI read/write boundaries admitted specifically for research orchestration, React/Vite/TanStack Query/Router, PyArrow/Parquet. DuckDB/Polars may be admitted only if measured scan-data access warrants them; no database/service framework is presumed.

## Global constraints

- Primary objective remains wealth relative to the correct matched passive counterfactual; coin accumulation is secondary.
- Every relationship-alpha claim must show incremental value over the strongest applicable predeclared simple control.
- Simple/mechanical controls run before richer models.
- Search-family denominator and attempted parameter/candidate count are first-class evidence.
- Development, final-OOS, and forward-paper roles remain explicit. Scanner exploration is development evidence unless a separately frozen commitment authorizes otherwise.
- The scanner cannot consume or reveal arbitrary reserved final-OOS data during search.
- A candidate may be frozen only from persisted admitted scan evidence; freeze does not imply promotion/live deployment.
- Browser does not recalculate accounting, rerun fills, refit models, or determine research success.
- No live exchange credentials, order placement, private account access, capital authority, leverage, derivatives, borrowing, or interest-bearing mechanics.
- No open-ended “try everything” search. Every scan has predeclared dimensions and finite bounds.
- No opaque composite score that hides HODL/control performance, costs, drawdown, search denominator, or evidence boundary.
- No compatibility layer for obsolete artifact schemas.

## Product workflow

```text
portfolio / admitted-universe selection
  → candidate-set generation
  → relationship/model selection
  → parameter-family declaration
  → finite scan manifest freeze
  → bounded experiment execution
  → candidate evidence table
  → control-aware ranking / falsification
  → portfolio/candidate combination analysis
  → freeze one candidate lineage for the next research stage
```

The scanner must distinguish **completed-run browsing** from **active research generation**. Phase-14 Research Runs continues to inspect persisted outcomes; Phase 15 creates and tracks bounded scan work.

## Core domain artifacts

Introduce explicit immutable current-schema artifacts rather than deriving scan state from filenames/UI memory.

### `ScanDefinition`

At minimum records:

- `scan_id`;
- created/frozen timestamp;
- research family ID;
- parent lineage, if any;
- data role (normally development);
- admitted universe/portfolio definition;
- candidate-generation rule;
- relationship/model component IDs and versions;
- finite parameter-family axes/values;
- policy family/config axes;
- benchmark/control ladder;
- cost scenarios;
- primary metric and `success_threshold`;
- multiplicity/ranking policy when required;
- maximum attempt count and deterministic enumeration order;
- dataset IDs/fingerprints and time window;
- code/provenance fingerprint.

Once execution begins, the definition is immutable. A changed family/parameter grid is a new scan generation, not an edit of past evidence.

### `ScanAttempt`

One enumerated candidate specification with:

- stable attempt ID/index;
- exact manifest/config fingerprint;
- status: pending/running/completed/failed/invalid;
- resulting run ID or explicit failure evidence;
- family-attempt denominator position;
- no duplicated financial result fields that can drift from the run artifact.

### `ScanResult`

A read model over completed attempt artifacts containing authoritative pointers/summary values needed for ranking:

- status/data role;
- primary metric/value/threshold;
- strategy vs HODL;
- strategy vs primary control;
- matched-contribution comparison where applicable;
- costs/fill count/turnover;
- relative drawdown/time-below diagnostics;
- family attempt count;
- falsification/control notes/status;
- run ID and exact provenance reference.

### `CandidateFreeze`

Immutable evidence that a specific scan result/spec was selected for the next stage. It contains the exact source `scan_id`, attempt/run ID, candidate manifest/config fingerprint, selection timestamp/rationale fields, data role, and next permitted research role. It cannot turn development observations into final-OOS/prospective evidence retroactively.

## Section 15.1 — Scan definition and deterministic enumeration

**Files (expected):**
- Create focused scanner domain modules under `src/qap/research/` or another architecture-approved research-orchestration package after import-boundary review.
- Add schema/serialization tests under `tests/unit/research/`.

**Behavior:**

- Accept only finite explicit candidate/model/parameter axes.
- Canonically sort/enumerate so identical definitions yield identical attempt IDs/order.
- Reject duplicate semantic configurations within one scan.
- Reject zero/negative attempt budgets and definitions whose Cartesian product exceeds the declared budget.
- Persist the true family attempt count, including failed/invalid attempts where they represent search effort.
- Bind exact data/code/config fingerprints before execution.
- Prevent reserved final-OOS data from being selected by an ordinary development scan.

**Acceptance:** repeated enumeration of the same definition is byte/identity reproducible and its denominator equals the actual attempted search family.

## Section 15.2 — Candidate-set generation

Candidate generation must be explicit rather than hidden in UI loops.

Support bounded generators needed by current QAP research, beginning with:

- fixed basket pair combinations from an admitted basket;
- point-in-time admitted universe pair/candidate sets when that universe mode already supplies authoritative eligible assets;
- asset-level/cross-sectional candidate sets for pair-blind/common-mode controls.

Do not introduce topology optimization, arbitrary graph search, broad venue discovery, or a generic strategy DSL. Candidate generators output IDs/specs; they do not evaluate alpha.

## Section 15.3 — Bounded scan executor

Build one deterministic local orchestration path that:

1. loads one frozen `ScanDefinition`;
2. materializes each exact current-schema experiment manifest from the enumerated attempt;
3. invokes the existing experiment/artifact runner;
4. records completed/failed attempt linkage atomically;
5. resumes safely without rerunning already completed attempt identities;
6. never modifies a completed run artifact;
7. enforces the declared maximum attempt count.

Execution may initially be synchronous/command-driven. Do **not** add Celery, distributed workers, queues, databases, schedulers, or asynchronous web jobs unless measured local scan runtime creates a concrete requirement and a separate architecture decision admits it.

A CLI is the first operator path. Browser-triggered scan mutation is admitted only after the backend scan command/state contract is proven and must use an explicit bounded API, not client-side loops that POST arbitrary experiments.

## Section 15.4 — Control-aware candidate evidence and ranking

Ranking must not become a single seductive score.

Default candidate table exposes separate sortable columns for:

- research status / threshold pass;
- vs HODL;
- vs primary simple control;
- matched-contribution comparison when applicable;
- maximum relative drawdown;
- modeled costs/turnover/fill count;
- family attempt count/search denominator;
- model/policy/parameter identity;
- falsification/control flags;
- data role and time window.

A default ordering may be defined only by an explicit research rule. For example, filter first to candidates that pass all mandatory economic gates, then sort survivors by the declared primary metric with deterministic tie-breakers. Do not rank a candidate that fails HODL/primary-control gates above a passing candidate merely because another secondary metric is attractive.

When broad search warrants multiplicity correction under the existing research constitution, show the adjusted evidence/decision separately rather than folding it into an opaque score.

## Section 15.5 — Falsification and robustness views

For a candidate to become freeze-eligible, the workbench must make applicable falsification evidence inspectable:

- pair-blind/common-mode control comparison;
- nearby parameter behavior where predeclared;
- delay/timing perturbation where predeclared;
- adverse cost scenarios;
- relationship versus mechanical/contribution-aware control ladder;
- family-level attempt/search context.

The scanner orchestrates/links these experiments; it does not invent new economic formulas in the UI.

## Section 15.6 — Portfolio/candidate combination analysis

Where multiple individually admissible candidates survive, provide bounded combination analysis without creating a new portfolio accounting owner.

Initial scope:

- select a finite subset of persisted survivor run/candidate IDs;
- compare overlapping assets/exposure directions and evidence periods;
- construct candidate target proposals only through existing allocation contracts;
- replay/evaluate any combined policy through the normal QAP experiment engine;
- compare combined candidates against the same required controls/costs.

Do not combine terminal returns algebraically in the browser as a substitute for replay. No mean-variance/optimizer library is added until a concrete combination question requires it and its output can be expressed as candidate target weights that still pass through QAP replay.

## Section 15.7 — Candidate freeze and next-stage boundary

The Candidate Workbench offers `Freeze candidate` only when backend evidence says the attempt is freeze-eligible under the declared scan rule.

Freeze must:

- reference the immutable scan/attempt/run identity;
- copy or fingerprint the exact manifest/config rather than allowing edits during freeze;
- record the family attempt count and selection rule used;
- record the candidate's development evidence window/fingerprints;
- set the next permitted stage explicitly;
- not read/consume the reserved final-OOS window;
- not grant deployment/live authority.

Changing model/parameters after freeze creates a new development generation and invalidates use of the old freeze for a fresh final-OOS claim.

## Section 15.8 — API boundary

After the domain/CLI contracts are proven, add minimal scanner endpoints. Expected shape:

Read-only:

- list/get scan definitions/status;
- list/get attempts/results;
- get candidate-freeze artifact.

Explicit mutations if admitted:

- create/freeze a new bounded scan definition;
- start/resume execution of that specific frozen definition;
- freeze one eligible candidate.

Mutation DTOs accept declarative current-schema inputs, not arbitrary Python/component execution. API errors are typed and fail closed for invalid role, excessive search size, stale/changed definition fingerprint, duplicate execution, or ineligible freeze.

Do not add generic task/job infrastructure. If synchronous HTTP execution is operationally poor, keep execution CLI-only until a separate local-job architecture is approved.

## Section 15.9 — Candidate Workbench UI

Create a dedicated route separate from `/experiments`, for example `/scanner` / `/research/scans` according to existing route conventions.

Primary workflow:

1. choose admitted portfolio/universe;
2. choose candidate generator;
3. choose allowed model(s);
4. declare finite parameter family/policy controls;
5. review exact scan size and research/data boundary **before** launch;
6. create/freeze scan;
7. inspect progress/results;
8. filter mandatory passes/failures;
9. inspect candidate detail/falsification;
10. run/inspect combination experiments where applicable;
11. freeze one candidate for the next research stage.

UI requirements:

- show exact attempted/maximum scan count before execution;
- make data role/window/final-OOS exclusion visible;
- show mandatory HODL/primary-control/threshold gates prominently;
- distinguish failed/invalid attempts from economically negative completed attempts;
- preserve raw run/scan/config fingerprints behind audit disclosure;
- no client-side financial recomputation;
- no “Run everything” without a finite predeclared definition;
- no live/deploy button.

## Section 15.10 — Research-run integration

Phase-14 `/experiments` remains the immutable evidence archive. Add navigation between:

- Scan -> Attempt -> persisted Experiment Detail;
- Experiment Detail -> originating scan/attempt when lineage exists;
- Candidate Freeze -> exact source run and scan evidence.

Do not rename completed-run filtering as scanning. The scanner owns active research generation; Research Runs owns inspection.

## Section 15.11 — Reproducibility and recovery

- Same frozen scan definition + code/data inputs enumerates the same attempts.
- Completed attempt/run artifacts are immutable.
- Interrupted execution can resume by comparing persisted attempt identities, not by guessing from display state.
- Failures remain part of family-attempt accounting where they consumed an intended attempt.
- A rerun under changed code/data requires a new scan definition/fingerprint rather than silently overwriting previous evidence.

## Testing strategy

Use high-value contracts rather than combinatorial UI tests.

Backend tests:

- deterministic scan enumeration/IDs;
- duplicate parameter semantic rejection;
- attempt-budget cap;
- correct family-attempt denominator including failed attempts;
- final-OOS exclusion in development scans;
- resume does not duplicate completed runs;
- ranking mandatory gates cannot be bypassed by secondary metrics;
- freeze rejects ineligible/changed attempts;
- candidate freeze preserves exact lineage.

Property-based testing is appropriate for deterministic parameter-grid enumeration/deduplication if invariants provide materially stronger coverage than examples.

Frontend tests only for serious semantics such as scan-count/boundary confirmation, negative/failed distinction, and freeze eligibility state. Use Agent Browser/Playwright for workflow/layout/integration.

## Verification

Phase verification includes the normal repository gates plus focused scanner tests, generated API drift checks, and rendered workflow QA. Required browser acceptance should cover:

```text
create finite development scan
 -> see exact attempt denominator and final-OOS exclusion
 -> execute deterministic fixture scan
 -> inspect negative and passing/threshold states
 -> open originating Experiment evidence
 -> return to candidate table
 -> freeze an eligible fixture candidate
 -> inspect immutable freeze lineage
```

A negative research family with zero freeze-eligible survivors is a valid successful scanner run; the UI must support ending with no candidate rather than encouraging threshold weakening.

## Exit criteria

- [ ] Active scanner workflow exists separately from completed-run browsing.
- [ ] Scan definitions/attempts are finite, deterministic, immutable, and reproducible.
- [ ] Search-family attempt accounting is exact and visible.
- [ ] Existing QAP experiment/replay/accounting/benchmark/cost contracts remain the only financial authority.
- [ ] Simple controls and mandatory HODL/primary-control/threshold gates precede richer candidate ranking.
- [ ] Reserved final-OOS evidence cannot be searched or consumed by ordinary development scanning.
- [ ] Candidate ranking exposes separate economics/risk/cost/search metrics rather than an opaque score.
- [ ] Combination experiments go back through QAP replay rather than browser arithmetic.
- [ ] Candidate freeze records exact lineage and does not grant deployment/live authority.
- [ ] Browser/CLI workflow is reproducible and fails closed on invalid or oversized definitions.
- [ ] Required backend/frontend/E2E/accessibility gates are green.

## Stop conditions

Stop for design review before introducing:

- a second backtest/accounting engine;
- unbounded/adaptive automated search that changes the family without a new frozen definition;
- automatic final-OOS consumption during search;
- Bayesian/AutoML/LLM strategy generation or optimizer-driven broad search without a separately approved research protocol;
- databases/distributed queues/cloud schedulers merely for convenience;
- generic plugin/strategy DSL infrastructure;
- live/private exchange API or capital deployment;
- a ranking score that replaces the declared economic gates;
- any change to QAP's protected objective, action space, research-role, benchmark, timing, fill/cost, or final-OOS semantics.
