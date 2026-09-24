# Research study workspace

Update context — 2026-09-24
Trigger: the user rejected another set of isolated UX fixes and requested a simple
researcher/stakeholder workflow, then authorized inferred details and execution.
Purpose: organize existing pair research around a resumable question and its attempts.
Impact: supersedes the pair-screen presentation/continuity portion of M11; preserves
all economic, admission, identity, final-OOS, and live-authority contracts.
Evidence: `2026-08-20-qap-pair-study-research-workflow-design.md`, current source,
and the user's research-workflow review in this session.

## User outcome

A local researcher selects two assets, resolves required setup in place, understands
the declared experiment, runs it, reads its conclusion, and returns to the same
study and earlier attempts. A stakeholder can understand a result without hashes,
component identifiers, or operation vocabulary. Advanced inspection remains available.

## Design

Update context — 2026-09-24 (interaction-model revision)
Trigger: the user rejected the first workspace as still unintuitive and click-heavy.
Purpose: replace process administration with a direct comparison interaction.
Impact: supersedes the first presentation below, not persistence or scientific authority.
Evidence: expanded global screen guides, equal-weight Home task cards, separate
prepare/check/run controls, and repeated result panels in current source.

Proposed interaction contract (implementation paused for the user's requested
[plan review](../plans/2026-09-24-intuitive-research-experience.md)):

- The primary screen is two asset inputs, a period and **Run comparison**.
  On a ready workspace there is one launch action, not separate study/check/run actions.
- Run explicitly requests preparation, backend validation and execution in sequence.
  Failed support never launches a run. Identity, asset admission and transient bridge
  permission remain explicit; granting bridge permission can continue the requested run.
- Settings preview and descriptive charts are optional; ordinary use does not require
  understanding models, recipes, SHA values or support axes. No method is silently chosen
  as a winner and no benchmark or default scientific configuration is changed.
- Saved work is a compact switcher, with automatic pair titles and optional renaming.
  Results precede optional relationship diagnostics; older runs use one compact selector.
- Global help is closed and below the task. Home has one primary research action.
  Healthy infrastructure status does not dominate the header; failures remain visible.
- Visual hierarchy uses one focused work area, restrained borders, generous input
  sizing, compact secondary actions and consistent spacing. No new UI dependency.

The following first-iteration decisions are retained only where they do not conflict
with the interaction contract above:

- Research opens on a study workspace with saved studies, a clear New study action,
  and an editable study name. Pair question and timeframe survive navigation/reload.
- A versioned browser-local study index is scoped by backend workspace identity.
  It stores intent and operation references only, never authoritative economics,
  support decisions, price data, identity approval, or run status. The interface
  explains local storage and reports unavailable/corrupt storage without overwriting it.
- On resume, current asset approval comes from the backend. Results and operation
  status are fetched again from their authoritative endpoints. Old attempts remain
  inspectable when the question changes. Browser storage does not replace History.
- Pair setup includes public market-directory loading, explicit asset confirmation
  and approval, and unresolved quote identities. No ticker is automatically treated
  as an identity. Quote confirmation does not grant economic or execution authority.
- Present relationship study before economic support. A downstream recipe failure
  must not discard successfully fetched relationship evidence. Freeze the request
  selection while running/preparing to prevent responses attaching to another question.
- Explain periods (30/90/180-day evaluation, 1h/4h/1d bars), methods, dates, starting
  allocation, fees/slippage, and benchmarks before launch using backend declarations.
- Expose supported numerical relationship/decision parameters as labeled controls
  in Experiment Lab; raw JSON remains an advanced option. Configuration changes
  require another backend support check; no client-side scientific eligibility rules.
- Results lead with the backend economic conclusion, HODL/control comparisons and
  existing performance chart. Method/configuration details are secondary; hashes,
  compilation lineage and machine identifiers sit under reproducibility details.
- Keep scan, portfolio, and advanced research accessible using their existing owners.
  Do not add a generic workflow engine, database, strategy method, or second ledger.

## Acceptance and limits

Verify study serialization, workspace separation, corrupt/blocked-storage behavior,
resume and attempt retention with focused CLI tests. Typecheck/build the frontend,
run the source-size gate, and inspect the final diff. No browser is authorized.
CLI DOM tests may verify interactions without launching a browser. Do not claim
rendered accessibility, real-public-data completion, or human acceptance from these.
Studies are local to this browser; existing backend History retains run artifacts
independently. Cross-device study synchronization is outside this change.
