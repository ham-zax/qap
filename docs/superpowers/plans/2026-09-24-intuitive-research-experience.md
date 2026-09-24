# QAP: simple research experience — implementation plan

**Status: implementation complete for usability review. Automated interaction checks and representative-user visual acceptance remain pending.**

Update context — 2026-09-24
Trigger: the user rejected the first research-workspace revision as unintuitive,
visually poor and requiring too many clicks, then requested a plan before more code.
Purpose: agree on the experience and implementation sequence before resuming work.
Impact: replaces the presentation direction of the earlier study-workspace plan.
Economic methods, benchmarks, identity/admission rules and holdout roles retain
their existing owners. This document does not approve a new research method.
Evidence: current React screens, the user's feedback, and the
[earlier implementation record](2026-09-24-research-study-workspace.md).

Update context — 2026-09-25
Trigger: the user approved this plan and asked to complete the remaining implementation.
Purpose: record the implemented interaction contract without promoting code checks into
representative-user acceptance.
Impact: the primary pair path now uses one Run comparison action for preparation,
backend support checking and launch; Home/Research/History and the secondary research
surfaces follow the same primary-task hierarchy. Economic, identity, admission,
holdout and live-authority contracts are unchanged.
Evidence: the React surfaces named in Sections B–E; `pnpm build` and
`git diff --check` pass. The source-size gate still reports the pre-existing
758-line `src/qap/market/adapters/binance_public.py` failure outside this change.

## 1. The outcome

A researcher can choose assets, run a comparison, understand the result, change
one assumption and try again. A stakeholder can read the same result and explain
what was tested, what happened after costs and what remains uncertain.

Ordinary use should require understanding three things:

1. **Comparison:** the assets, period and settings being tested.
2. **Result:** what each method achieved against the declared comparisons.
3. **History:** earlier results and how to reopen them.

Studies, recipes, compilations, support checks, manifests and operation IDs remain
internal concepts or optional diagnostic detail. Names are generated from the
chosen assets; naming and managing a project are optional.

“Rethink the models” is interpreted here as rethinking these interaction models.
Changing mathematical models or their economic definitions requires its own scope.

## 2. Why the current screens fail this outcome

| Current behavior | User consequence | Planned correction |
| --- | --- | --- |
| Expanded global guide before the task | Instructions occupy the first screen | Contextual help below the task, closed initially |
| Home presents several equal-weight destinations and readiness explanations | The user must learn the application before starting | One prominent research entry; recent work and secondary tools below |
| Pair study, settings check and execution are separate actions | The user coordinates backend stages | One Run comparison action owns the sequence |
| Sidebar, name field, task tabs, warnings and diagnostics compete with the input | The next action is visually unclear | One focused input area; compact saved-work control |
| Large result panels repeat for every method | Comparing methods requires scrolling and remembering numbers | One comparison summary, then an individual-method detail view |
| History groups records around technical artifact types and identifiers | Previous work is difficult to recognize | Human titles, assets, dates and outcomes first; original records still linked |

Source locations: `components/AppShell.tsx`, `components/ScreenGuide.tsx`,
`features/home/HomeWorkspace.tsx`, `features/discovery/ResearchHome.tsx`,
`PairResearch.tsx`, `ResearchStudyWorkspace.tsx`, `PairResearchCompletion.tsx`,
and `features/experiments/HistoryView.tsx`, under `web/src/`.

## 3. Screen and navigation decisions

Keep existing routes and the primary Home / Research / Portfolios / History
navigation during this change. Redesign what those destinations prioritize.

- **Home:** a prominent “Start a comparison” action, recent results and any active
  task. Asset administration and specialist tools are secondary links. An empty
  workspace invites a first comparison without presenting a wall of failed gates.
- **Research:** open the pair comparison directly. “Scan assets” and “Custom
  experiment” are secondary task choices, not competing launch panels.
- **Results:** remain in the research screen after completion. A persistent result
  link opens the authoritative record without depending on browser draft storage.
- **History:** recent work with recognizable titles, dates, assets and outcomes;
  filtering and detailed lineage are secondary. Preserve the distinction between
  historical, later and current evidence when a result has those layers.
- **Portfolios:** retain the existing asset and relationship requirements. Apply
  the same visual hierarchy and terminology after the research path is complete;
  do not add an arbitrary-basket shortcut that bypasses its source requirements.

### Research layout

Desktop arrangement; mobile stacks the two asset inputs and makes the main button
full width. No permanent sidebar is needed for the primary task.

```text
Research                              Saved comparisons ▾
Test whether rebalancing helped.

┌────────────────────────────────────────────────────────┐
│ First asset [ search / selected ]                       │
│ Second asset[ search / selected ]                       │
│ Period      [ 30 days ] [ 90 days ] [ 180 days ]          │
│                                                        │
│ Two methods · compared with holding and rebalancing      │
│ [Settings]                          [ Run comparison ]  │
└────────────────────────────────────────────────────────┘

Results appear here, with the tested assets and dates.

Scan assets · Custom experiment
```

The methods and cost summary use the actual backend declaration. If exact inputs
require preparation, the interface says they are being prepared and offers a
settings preview; it must not invent dates, holdings, fees or support status.

### Result layout

```text
W / PIXEL · actual tested dates           Earlier runs ▾

Method                         vs Holding   vs Rebalancing
Price-ratio mean reversion      [value]      [value]  [verdict]
Regression-residual method      [value]      [value]  [verdict]

[Selected method's relative-wealth chart]
Plain explanation of its recorded result and limits.

[Change settings]                    [Run again]
Test details ▾                       Reproducibility ▾
```

Use the first declared method for the initial detail view, not the highest score.
Switching methods changes the detail view; both summary rows stay visible. If one
result or chart fails to load, retain the other available results with a retry.
On small screens, summary rows become compact cards with the same labels.

## 4. Click targets and interaction rules

| Task | Target |
| --- | --- |
| Start with both assets selected and default settings | One Run comparison activation |
| Start from empty asset inputs | At most five pointer clicks using search: focus/select A, focus/select B, Run; typing excluded |
| Choose a different period | One additional activation |
| Edit settings and run again | No separate prepare/check/confirm step after editing |
| Reopen a visible recent result | One activation |
| Inspect reproducibility from a result | One disclosure, no nested navigation requirement |
| Save work or name a comparison | Automatic saving; no required naming step |

These targets apply when prerequisites are satisfied. Identity review and explicit
asset/bridge permission are real decisions and are counted separately. Do not
advertise a one-click first installation while those decisions remain necessary.

Both supported pair methods are compared by default. Their readable names and
short descriptions explain their differences. Custom methods and unavailable
capabilities belong in the custom experiment task; do not show disabled speculative
methods in the ordinary form or silently pick the best historical performer.

Settings use labeled fields with units. Basic settings are visible in one panel;
exact configuration and JSON are an optional technical view. Preserve existing
defaults, scopes and validation. A changed parameter invalidates prior support
internally, and the next Run action obtains a fresh backend check automatically.

## 5. Setup, progress and recovery

**First use:** keep the chosen pair visible while resolving only its missing
requirements. Use the existing public-directory, identity, admission and market-data
APIs. Do not grant identity or ownership approval from ticker matching or saved UI
state. Explain the requested decision in ordinary language with its required evidence.

**Ready use:** Run requests prepare → support check → execution. Show a short
progress sentence at the button. Do not turn each stage into a separate card or
ask the user to approve a successful check.

**Missing bridge permission:** show one contextual explanation of temporary USDT
holdings and costs on both legs. “Allow and run comparison” grants the existing
permission, obtains fresh context/support and continues. It never implies live orders.

**Unsupported configuration:** stop before execution. Show the specific backend
reason and useful next action beside the relevant input. Keep the draft and any
independent relationship results. Technical axes and codes stay expandable.

**Navigation and reload:** distinguish preparation in the current page from a
durable backend operation. Once the operation exists, resuming fetches its recorded
status and results. Reload before launch restores the draft and offers Run; it must
not silently launch work. Never claim that browser-only preparation survives closure.

**Duplicate actions and stale responses:** lock a submitted selection, reject a
second launch while it is pending, and bind returned work to the submitted question.
Old callbacks cannot overwrite newer drafts. Preserve existing storage conflict and
corruption handling; backend run references survive independently in History.

**Results:** operational completion and economic outcome use separate wording.
A method that beats holding but fails its simple-control criterion retains its
backend verdict. Missing economics show “Unavailable”, never zero or success.

## 6. Visual design rules

- Retain the current dark palette initially. Improve hierarchy through typography,
  spacing and alignment before introducing another theme or a dependency.
- Constrain the main research form to roughly 900–1,000 px; allow charts/results
  more width where useful. Avoid stretching a small form across the full desktop.
- Use a single primary action color. Secondary controls are quieter text/outline
  treatments. Healthy infrastructure information stays in a utility area; actual
  failures remain discoverable and visible when relevant to the task.
- Use one principal surface around the form, whitespace between sections and
  separators where needed. Avoid nested borders around every sentence or metric.
- Use at least 44 px input/action targets, visible keyboard focus, associated
  labels and explicit selected state. Asset search supports keyboard selection,
  escape and understandable empty results.
- Keep the page usable at 360 px width without horizontal page scrolling. Give
  charts and genuinely wide tables their own contained overflow behavior.
- Keep loading/error/empty states in the same layout as their eventual content.
  Do not move focus or scroll the page after every background update.
- Avoid repeated banners about authority and provenance. Keep a concise research
  context note and explain specific limitations where they affect interpretation.

## 7. Implementation sequence

Each slice produces reviewable application behavior. The first useful slice must
include inputs, execution and results, not stop at a styled empty form.

### A. Review the proposed experience

- [x] Review the research and result arrangements above and the click targets.
- [x] Treat this plan as the approved interaction direction; the earlier technical checklist is
  historical evidence and does not establish usability acceptance.
- [x] Preserve the first-iteration branch history. The earlier header/help changes
  were assessed against this plan rather than treated as usability acceptance.

### B. Build the complete pair-comparison path

- [x] Refactor `PairResearch.tsx` so one explicit action coordinates preparation,
  support and launch. Prefer a bounded feature-owned hook if the controller grows;
  avoid a generic workflow engine. No React effect starts a scientific operation.
- [x] Simplify `PairResearchSetup.tsx`, `ResearchAssetSelector.tsx`,
  `ResearchStudyWorkspace.tsx` and `PairExperimentPreview.tsx`: asset selection,
  period, compact saved-work control, optional settings, generated title.
- [x] Use the existing APIs in `api/client.ts` and `api/queries.ts`. Inspect their
  error and operation contracts before composing calls. Backend support remains
  the execution gate; do not duplicate scientific validation in React.
- [x] Rework `PairResearchCompletion.tsx` into a joint method summary and selected
  detail view using existing experiment/performance responses. Keep exact values,
  provenance access and all method results.
- [x] Preserve and adapt `researchStudies.ts` / `useResearchStudies.ts` continuity
  behavior. A browser draft remains a convenience, not a new research ledger.

Exit: a prepared pair reaches results with one launch action; an unsupported pair
stops with a useful reason; editing settings reruns through a fresh support check.

### C. Give the application a consistent frame

- [x] Refine `AppShell.tsx`, `ScreenGuide.tsx`, `HomeWorkspace.tsx` and
  `ResearchHome.tsx`: primary task first, concise navigation, optional help and
  recent work that can be recognized without identifiers.
- [x] Apply the visual rules through existing tokens/classes and small shared UI pieces
  only where multiple screens actually need them; no new styling dependency is required.
- [x] Keep specialist routes reachable and existing links valid. Do not preload
  advanced mutation-capable work or make the default screen depend on every
  optional history/scanner endpoint succeeding.

Exit: Home and Research clearly identify a first action; help and operational
details no longer displace the task; layout works with keyboard and small screens.

### D. Make returning and comparing understandable

- [x] Simplify `HistoryView.tsx` around recognizable work and dates. Use existing
  family/compilation relationships to group records; do not invent lineage from names.
- [x] Surface earlier runs from the current comparison in a compact selector.
  The displayed result always identifies its own tested assets, dates and settings,
  even when the current draft has changed.
- [x] Keep historical/later/current evidence distinctions when present. Preserve
  rejected and unavailable results as well as positive ones.
- [x] Retain local-storage limitations in an unobtrusive explanation. Existing
  backend records remain accessible without the browser draft index.

Exit: the user can leave, return and recognize earlier work without reconstructing
it from operation IDs or treating a newly edited draft as an old result's input.

### E. Apply the same pattern to secondary research tools

- [x] In `ProductResearch.tsx`, prioritize scope, period, one scan action and an
  understandable result count. Collapse successful readiness detail; show actual
  blockers where they can be resolved. Keep preparation bounded to the chosen scope.
- [x] In `ExperimentLab.tsx` and `RecipeAuthoringControls.tsx`, prioritize supported
  method choices and labeled settings. Retain exact JSON access under technical detail.
  Continue to report unsupported requested methods honestly.
- [x] In `BasketHome.tsx` and `BasketScopeControls.tsx`, simplify the presentation
  of source selection, assets and required relationships. Keep the graph as an
  inspection aid where possible. Do not invent or auto-approve portfolio edges.
- [x] Reuse the result presentation vocabulary on these screens while rendering
  each domain's own authoritative outputs.

Exit: secondary tools follow the same choose → run → read pattern wherever their
existing contracts permit it, with clearly explained additional decisions.

### F. Verify behavior and record acceptance honestly

Verification record — 2026-09-25: `pnpm build` passes, including TypeScript
checking, and `git diff --check` passes. The source-size gate was rerun and still
fails only on the pre-existing 758-line Binance public adapter recorded below.
No test suite, CLI DOM interaction suite, or browser/representative-user acceptance
was run in this implementation pass; those remain separate gates.

- [ ] Use focused CLI interaction tests for the new orchestration and persistence
  risks. Adapt existing tests to user behavior; do not merely assert new copy.
- [ ] Cover a normal run, preparation failure, unsupported settings, bridge
  permission, double launch, parameter edits, navigation during launch, reload,
  cross-tab/storage failure, partial result failure and preserved economic verdicts.
- [ ] Run frontend typecheck/build, relevant route/component checks, diff checks
  and the source-size gate. Keep new handwritten modules below 500 lines where
  practical; no new module may exceed 700 without an approved exception.
- [x] Compare failures with the existing baseline. Repair failures caused by this
  change; report independent debt without relabeling the repository as green.
- [ ] Inspect accessible structure and keyboard interactions through CLI DOM tests.
  Browser automation remains prohibited by the user's instruction.
- [x] Record visual and representative-user acceptance as pending until it is
  actually observed. Passing DOM tests cannot prove a good visual experience.

## 8. Boundaries and known limitations

This implementation does not change economic objectives, methods, cost/fill rules,
benchmark definitions, final-OOS handling, universe eligibility or live authority.
It introduces no model search, automatic winner selection, new exchange, cloud
account, cross-device sync or separate experiment engine. Useful MFSM reporting
patterns are already documented in the [read-only assessment](../../research/2026-09-24-mfsm-experiment-patterns.md).

The previous revision's CLI baseline was 64 passing / 6 failing frontend tests;
the six failures also reproduced on unchanged `dfaa8c2`. The source-size gate
failed on unchanged `src/qap/market/adapters/binance_public.py` at 758 lines.
The frontend-test counts remain historical baseline observations. The 2026-09-25
source-size rerun confirms the same unrelated 758-line failure.

The main product constraint is first-use identity evidence: the current backend
requires explicit verified mappings. Improving its wording and placement is in
scope. Replacing that contract with a trusted identity service is a separate design
decision and must not be smuggled into a visual simplification.

## 9. Completion criteria

The code is ready for usability review when the proposed click targets work,
failures preserve context, all results retain their authoritative meaning, and
the application offers one clear next action at each stage. Implementation checks
and user acceptance are recorded separately. The plan is not complete merely
because every component has been rewritten or a new theme has been applied.
