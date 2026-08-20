# Agent A — Phase 17 M10-D Pair Research UX Remediation

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed Product UX / minimal application orchestration
**Can start:** immediately after this coordination base is committed
**Depends on:** M10-A `12ed08a`, M10-B `f39b4b4`, M10-C `3e07878`, observed M10-D representative-user evidence
**Execution lifetime:** use Persistent Agent Loop

## Mission

Make ordinary Pair Research feel like research rather than workspace administration.

The representative-user acceptance walkthrough attempted a simple task: research `W / PIXEL`, inspect z-score/residual-style experiments and other backend-supported methods, and see the resulting values. The Product instead exposed quote-identity administration and repeated market-data setup/navigation before research could begin.

Close that UX failure with the smallest complete Product change while preserving all existing scientific, identity, admission, provenance, final-OOS, scanner, and live-capital boundaries.

## Observed acceptance evidence

The live integrated Product at `main @ d30c60f` showed:

- exact-first asset selection works: exact `W` is ranked first;
- `W` and `PIXEL` can be selected and the pair/timeframe draft is held locally;
- Pair Research then surfaces `Prepare data for this research`, but ordinary setup can push the operator into Research Universe;
- the operator had to expand identity administration, review venue `USDT`, enter canonical `USDT`, enter an identity version, confirm it, and navigate back before current venue paths became usable;
- before that setup, Research reported 3 approved assets, 0 ready assets, and no ready venue paths;
- after quote-identity confirmation, `W` and `PIXEL` exposed current Gate paths (`W_USDT`, `PIXEL_USDT`);
- the user explicitly rejected the workflow as too complicated and expected pair selection -> preparation/check -> experiments/results;
- the live workspace also displayed a suspicious `BTC` card associated with Binance `WUSDT`; treat that as a state-correctness warning. Diagnose whether it is stale/bad workspace identity state or a Product binding defect before using that path, but do not broaden this mission into unrelated identity architecture.

This is a M10-D `UX REMEDIATION REQUIRED` outcome, not a scientific-contract failure.

## Product target

For an ordinary pair such as `W / PIXEL`, the primary flow should be approximately:

```text
Research a pair
  W + PIXEL
  Medium-term
        |
        v
Prepare & check research
        |
        +-- QAP reuses already-known identity/admission state
        +-- QAP prepares all required admitted data for the selected pair/timeframe
        +-- QAP freezes exact Product inputs
        +-- QAP runs backend Check support
        |
        v
Supported experiments / reasons
        |
        v
Run supported research
        |
        v
Immediate experiment values + exact run links
```

The operator should not need to understand quote coordinates, generation fingerprints, dataset IDs, recipe hashes, or compiler lineage to get from a pair question to research results.

## Ownership and implementation boundaries

### Pair Research owns the continuous interaction

Prefer the existing M10-B `PairResearch` composition and existing API/client/query helpers. Reuse current identity/admission/market-data mutations and M10-A support/run endpoints rather than building another workflow engine.

Prefer client-side orchestration of existing bounded operations when it can safely express the flow. Add a new backend operation/endpoint only if repository evidence proves existing APIs cannot preserve the required authority/atomicity.

### Setup must be just-in-time and inline

When selected assets/timeframe need ordinary setup:

- preserve the selected pair and timeframe;
- do not navigate the operator away to Research Universe for routine recovery;
- perform every safe automatic/reusable step behind one `Prepare & check research` action;
- if a genuine identity ambiguity still requires operator confirmation, show one bounded inline setup interruption and resume the exact same draft immediately afterward;
- keep identity confirmation separate from asset approval;
- never treat matching ticker text as identity proof;
- do not auto-admit an economic asset merely because it is a quote coordinate or exchange listing.

Do **not** make the user type or reason about an internal version field if current repository authority already owns that version mechanically. If hiding `identity_version` would require changing its scientific/identity meaning, stop and report that specific point for design review instead of guessing.

### Market-data preparation should match the research task

The user asked to prepare `W / PIXEL`, not “prepare W”. The primary Product should communicate and orchestrate preparation for the complete selected research question and timeframe, including every current authoritative dataset/direct-market requirement already owned by Product market-data/readiness.

Do not synthesize a direct market, weaken immutable-generation provenance, or claim readiness before backend readiness says so.

### Support and experiment choices remain backend-owned

After preparation, refresh M10-A Product context / Check support from backend truth.

- no React capability registry;
- no local scientific precedence;
- only `support.runnable` + canonical recipe authorizes launch;
- known-unimplemented methods remain non-runnable;
- formal cointegration must not be implied if QAP only supports rolling OLS residual/z-score evidence. Use truthful naming such as `Residual / OLS z-score` and make any distinction from a formal cointegration test clear from existing backend capability semantics/copy.

### Results should answer the research question

After a successful Pair Research run, the same flow should immediately show the exact sibling experiments and the important backend-owned values already available from current run/read models, without forcing the user to hunt through technical provenance.

At minimum, where current artifacts/read models provide them, surface:

- method/model label;
- declared lookback/window/threshold parameters relevant to that sibling;
- relationship/evidence value such as current z-score/residual statistic when available;
- primary replay/economic result and declared benchmark/control comparison where available;
- exact run link.

Do not calculate scientific values in React. If the current public read model lacks a value already owned by an existing authoritative artifact/read owner, add only the smallest read-only projection needed to present that existing value. Do not create a second result store or recompute model evidence in Product code.

Technical provenance (recipe SHA, compilation SHA, dataset fingerprints, manifest hashes, compiler/catalog versions) remains available under progressive disclosure, not the default result summary.

## Suspicious BTC/WUSDT observation

During acceptance, after quote identity setup, the canonical `BTC` card displayed Binance `WUSDT`. Before changing production code:

1. establish whether this is stale/bad local workspace state created by earlier identity confirmation, or an actual Product mapping/presentation defect;
2. if it is local state only, document that and keep the remediation focused;
3. if it is a small Product binding defect on the same identity/read path, fix the responsible owner without weakening fail-closed identity;
4. if correcting it would require redesigning identity authority, stop and return the finding rather than broadening M10-D remediation.

Do not use the suspicious BTC path as evidence for successful pair research until resolved.

## Observable success conditions

The mission is complete when direct browser/runtime evidence shows:

1. A user can select exact `W`, select `PIXEL`, choose a Product timeframe, and remain on the Research screen.
2. One obvious primary action (`Prepare & check research` or equivalent) advances the same draft through reusable setup, required market-data preparation, and backend support refresh.
3. Routine quote/data plumbing is not exposed as the primary task. Any genuinely ambiguous identity step is inline, bounded, plain-language, and returns to the same draft automatically.
4. The action prepares/checks the complete selected pair/timeframe rather than presenting one asset as if it were the whole research task.
5. Once ready, Pair Research shows backend-supported experiments/reasons and only enables Run from canonical backend truth.
6. A completed default pair family presents immediate sibling/result summaries with backend-owned model/parameter/result values plus exact run links; technical lineage stays under progressive disclosure.
7. Experiment Lab remains advanced and backend-described; no new research method or local scientific registry is introduced.
8. Universal Scan remains scanner-owned and unchanged in authority.
9. The suspicious BTC/WUSDT observation is classified as workspace-state or Product defect and is not silently ignored.
10. The affected M10-D Pair Research task can be rerun without developer coaching as the next human acceptance step.

Use `W / PIXEL` for the representative browser flow when the public venue/data path is available. Never fabricate scientific values merely to satisfy the walkthrough.

## Protected boundaries

Do not change:

- M10-A recipe/support/compiler/family/final-OOS semantics;
- scanner protocol or Universal Scan ownership;
- strict historical PIT semantics;
- asset admission authority;
- fail-closed identity semantics;
- experiment manifest/model/basket/replay/economic authority;
- current evidence/capacity scientific truth;
- live/private trading authority;
- Copula, Palazzi, cointegration, or any other method implementation;
- plugin/runtime architecture.

No Focus Scan.

## Testing / verification policy

Do not create, modify, or run tests.

Use direct evidence tied to the requested behavior. At candidate final state, use only the smallest applicable non-test checks needed for changed contracts, such as:

- headed/visible browser walkthrough of the repaired Pair Research flow;
- actual backend API/operation evidence for the selected pair;
- frontend typecheck/build if frontend source changed;
- focused Ruff/Pyright/import-contract/OpenAPI generation checks only if corresponding backend/API files changed;
- `git diff --check` and staged-diff inspection.

Do not run broad test suites.

## Out of scope

- implementing formal cointegration tests;
- implementing Student-t Copula or Palazzi;
- redesigning Product identity/admission architecture;
- automatically approving assets;
- a generic setup/workflow engine;
- scanner changes;
- unrelated cleanup;
- new portfolio/live-trading features.

## Finish report

Return:

1. status: complete / blocked / design review required;
2. branch, worktree, commit, fresh Git status;
3. exact Pair Research flow before vs after;
4. how identity/admission/data setup is now handled and which authority remains responsible;
5. W/PIXEL direct browser/runtime evidence, including method/result values actually shown;
6. classification of the BTC/WUSDT observation;
7. files/public APIs changed;
8. non-test validation actually run;
9. protected boundaries confirmed unchanged;
10. exact M10-D human acceptance task to rerun next.
