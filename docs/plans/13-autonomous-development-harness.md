# Phase 13 — Sequential Autonomous Development Harness Implementation Plan

**Goal:** Build a small local development-support harness that helps the same ChatGPT implementation agent continue approved QAP work sequentially across long sessions, preserving progress, verification evidence, Git safety, and hard escalation boundaries without spawning another coding model.

**Architecture:** The harness lives under `tools/agent/` and `.qap-agent/`; it is development tooling only and never becomes a dependency of `src/qap`. The implementation agent remains the sole reasoning/writing owner. The harness parses approved plans, records progress, checks Git scope/writer ownership, runs declared verification commands, and preserves recoverable mission state. It does **not** launch subagents, reviewer agents, worker pools, or another autonomous coding runtime. Transport, Terminal/tmux lifetime, durable waits/timers, Bash output/spool retention, MCP health, log rotation, and primitive routing remain responsibilities of the connected `satori_bridge`/`mcp-harness-local` harness and must not be reimplemented inside QAP.

**Tech Stack:** Python 3.14 standard library first, Git, existing Superpowers Skills/workflows, and the connected WSL harness primitives already available to the implementation session. No generic agent framework, provider abstraction, multi-agent platform, queue, scheduler, or service.

## Update context — 2026-08-17

- **Trigger:** user steering explicitly changed the execution model to direct sequential implementation by the main ChatGPT agent.
- **Purpose:** keep QAP engineering single-agent and sequential while preserving long-session recovery, verification, scope control, and plan discipline.
- **Impact:** the same agent implements, debugs, reviews, verifies, commits, and advances phases directly. Relevant Skills are invoked by that agent when their trigger conditions apply. Phase ordering and all protected economic/research/live-capital boundaries remain unchanged.

## Global Constraints

- Implement this phase only after the manual/direct QAP engineering workflow is proven through earlier phases.
- The harness supports execution of approved plans; it does not invent product roadmap or economic policy.
- The implementation agent owns all repository reasoning and mutations sequentially.
- Maintain one writable autonomous process/session per Git worktree; read-only inspection may coexist, but a second writer must wait for an explicit handoff or use a separately assigned worktree only when isolation is actually required.
- Terminal/PTY ownership and Git worktree writer ownership are separate contracts.
- Do not invoke another model for implementation, review, debugging, investigation, or second opinions. Codex and any other separately metered external model/CLI are explicit opt-in only; a Skill/workflow request for delegated review does not authorize substituting one.
- No runtime import from `tools/agent` into `src/qap`.
- Preserve unrelated user changes and never run destructive Git operations automatically.
- No secret/password/MFA input through prompts, logs, or checkpoint files.
- Architecture/economic/action-space/live-capital changes stop and escalate.
- Long-running local commands may use Terminal + durable waits, but they remain tools of the same implementation mission, not independent agents.
- Treat connected-harness evidence in layers: presentation/UI -> MCP/provider transport -> WSL process/filesystem -> Git/repository state. Opaque presentation is unobservable, not proof of success or failure; use at most one bounded authoritative WSL health probe when execution state is uncertain.

## File Map

**Modify:**
- `.gitignore` — ignore `.qap-agent/` local progress/runtime state.
- `AGENTS.md` — only if a context audit proves a small change is necessary; do not expand by default.

**Create:**
- `tools/agent/README.md` — operator usage, direct-agent workflow, and stop conditions.
- `tools/agent/qap_agent.py` — small command entry point for status/checkpoint/verify helpers; it does not execute another coding model.
- `tools/agent/plan.py` — approved plan/section extraction.
- `tools/agent/state.py` — progress JSON/Markdown persistence under `.qap-agent/`.
- `tools/agent/git_guard.py` — baseline status/diff/commit safety checks.
- `tools/agent/verify.py` — bounded verification command execution and evidence capture.
- `tests/tools/agent/test_plan.py`
- `tests/tools/agent/test_state.py`
- `tests/tools/agent/test_git_guard.py`
- `tests/tools/agent/test_verify.py`

**Do not create:**
- agent-runtime/provider adapters;
- prompt dispatchers for another model;
- worker/reviewer process managers;
- autonomous merge/push logic;
- background coding daemons;
- replacement MCP transports, Terminal/session managers, timer schedulers, log rotators, spool managers, or tool-routing layers already provided by `satori_bridge`.

## Section 13.1 — Context Audit Before Harness Code

**Purpose:** prevent a persistent direct implementation loop from amplifying contradictory or stale instructions.

**Steps:**
- [ ] Use the applicable context/instruction-review workflow available in the session when its trigger conditions apply.
- [ ] Audit root `AGENTS.md`, the controlling implementation prompt, relevant plan references, and repository-level protected-boundary docs.
- [ ] Remove/shorten only context that is demonstrably contradictory, duplicated, stale, or over-constraining; preserve canonical design/reference boundaries.
- [ ] Record the final context sources in `tools/agent/README.md`.
- [ ] Do not copy full design/plan documents into `AGENTS.md`; the implementation agent reads the exact current phase/section when needed.

**Acceptance criteria:**
- One concise root context plus the controlling mission and current plan section is sufficient for the implementation agent to act without repeatedly scanning the entire docs tree.

## Section 13.2 — Direct-Agent Operating Contract

**Purpose:** make the no-delegation execution model explicit and recoverable.

**Contract:**

```text
main ChatGPT implementation agent
  -> inspect repository reality
  -> invoke applicable Skill when triggered
  -> implement coherent slice directly
  -> run focused verification
  -> inspect diff/state
  -> self-review against plan + protected contracts
  -> repair findings
  -> run completion verification
  -> commit/checkpoint
  -> continue sequentially
```

**Behavior:**
- The harness never launches another coding model.
- The harness never marks a section complete merely because a command exited successfully.
- Persistent Terminal processes are allowed only for builds, servers, experiments, browser sessions, or other real tools requiring durable lifetime.
- Status/progress steering is answered promptly from already-recorded/verified state; the harness must not trigger broad verification, review, or cleanup merely to answer `status`. Mission execution then continues automatically.
- The implementation agent verifies writer ownership before each mutating slice; read-only status/inspection is allowed while another writer exists, but mutation is not.
- `verification-before-completion` is the required review/completion workflow before the agent claims a substantive slice/phase is complete or creates its completion commit.
- `systematic-debugging` is used when a bug, failing test, or unexpected behavior triggers that workflow.
- Other installed Skills are invoked only when their own trigger conditions apply; do not create ceremony by invoking irrelevant Skills.

**Steps:**
- [ ] Document this contract in `tools/agent/README.md`.
- [ ] Test that no source file or CLI option can configure a secondary coding/review model.

## Section 13.3 — Approved Plan Parser

**Interfaces:**
- Consumes: one explicit plan path under `docs/plans/` or `docs/superpowers/plans/` and optional section ID.
- Produces: ordered bounded plan sections for the implementation agent to inspect/track.

**Behavior:**
- The harness never discovers arbitrary docs and decides they are executable.
- User/operator or the implementation agent passes the approved plan path explicitly.
- Parser recognizes headings such as `Section 05.3` plus Steps/Verification/Acceptance/Exit/Stop content.
- A section is the default progress unit; checklist micro-items are not separate sessions.
- Parse failure stops before progress mutation.

**CLI shape:**

```bash
uv run python tools/agent/qap_agent.py status docs/plans/05-policy-target-allocation-and-rebalancing.md
uv run python tools/agent/qap_agent.py section docs/plans/05-policy-target-allocation-and-rebalancing.md --section 05.3
```

**Steps:**
- [ ] Write parser fixtures/tests using actual QAP plan structure.
- [ ] Implement only the Markdown grammar this repository actually uses.

## Section 13.4 — Persistent Progress State

**Interfaces:**
- Consumes: plan path, section IDs, direct-agent checkpoints, verification evidence, commits, blockers.
- Produces: `.qap-agent/<plan-slug>/progress.json` and `progress.md`.

**State per section:**
- `pending | in_progress | complete | blocked`;
- baseline Git commit/status fingerprint;
- canonical worktree path, branch, and writer identity/ownership note when the section is `in_progress`;
- active persistent process/wait identifiers when they affect safe recovery;
- start/end timestamps;
- resulting commit hash when committed;
- verification commands and exit codes;
- concise material decision/blocker note;
- next intended direct implementation action.

**Behavior:**
- State writes are atomic (`tempfile` + replace).
- On a later session, repository/Git/process reality outranks stale progress state; an inherited writer record must be reconciled against fresh worktree/process evidence before mutation resumes.
- Progress is local/gitignored; plans and code commits remain durable Git truth.
- Checkpoints never contain secrets or private credentials.

**Steps:**
- [ ] Write crash/resume and corrupted-state tests.
- [ ] Provide a `status` command that reads progress without mutating the repository.
- [ ] Provide an explicit `checkpoint` command/function used by the implementation agent at meaningful boundaries.

## Section 13.5 — Git Guard

**Interfaces:**
- Consumes: repository status before/after a direct implementation slice.
- Produces: safe-to-proceed/safe-to-commit evidence.

**Behavior:**
- Capture canonical worktree path, `git status --porcelain=v1`, current branch, and HEAD.
- Track cooperative writer ownership for the worktree while a mutating slice is active. A different active writer blocks mutation but not read-only `status`/inspection. Stale ownership may be cleared only after fresh process/worktree evidence proves the previous writer is no longer active.
- Preserve unrelated dirty state; never reset/stash/clean it automatically.
- Compare changed paths against the current plan section's file map plus necessary dependency/lock/config files.
- Unexpected broad/deletion changes become a self-review blocker before commit.
- Never execute `git reset --hard`, `git clean -fd`, force push, branch deletion, or automatic merge/push.

**Steps:**
- [ ] Test with temporary Git repository containing unrelated dirty files.
- [ ] Test an allowed planned change and an unexpected destructive change.
- [ ] Test that a second writer identity is blocked from mutation in the same worktree while read-only status remains allowed, and that explicit/stale-verified handoff permits the next writer.

## Section 13.6 — Verification Runner

**Interfaces:**
- Consumes: verification commands explicitly present in the plan section plus repository-global affected checks when the plan requires them.
- Produces: command/exit/duration/output-tail evidence.

**Behavior:**
- Commands originate from reviewed repository plans or explicit direct-agent verification decisions, not arbitrary untrusted network text.
- Run section-focused verification first.
- A read-only `status` request never invokes this runner implicitly.
- Do not automatically run every historical phase/full suite when the claim does not require it.
- Output is bounded in progress state; full logs may be stored under `.qap-agent/<plan>/logs/`.
- A zero exit code is evidence for that command only; plan acceptance and protected-contract review remain the implementation agent's responsibility.

**Steps:**
- [ ] Implement subprocess execution with timeout and captured output.
- [ ] Preserve exact command and exit code.
- [ ] Test success, failure, timeout, and bounded log capture.

## Section 13.7 — Sequential Slice Checkpoint Loop

The harness records this direct-agent sequence; the implementation agent performs it:

```text
read current plan section
 -> snapshot Git state
 -> mark section/slice in_progress
 -> main agent implements directly
 -> run focused verification
 -> inspect diff/state
 -> invoke applicable self-review/debugging Skills
 -> repair if needed
 -> run required completion verification
 -> commit coherent work
 -> mark complete + record evidence
 -> continue to next dependency-safe section
```

**Behavior:**
- No background coding worker exists.
- No second model is launched for review. Codex or any other separately metered model/CLI requires explicit user authorization for the current task and is otherwise forbidden.
- Writer ownership is acquired/reconciled before mutation and released/checkpointed at a safe handoff boundary; Terminal ownership alone does not satisfy this check.
- A failed verification leaves the slice `in_progress` or `blocked`; the same agent diagnoses and repairs it.
- Repeated failure does not automatically consume new research holdouts or weaken acceptance criteria.
- A blocked dependent section prevents later dependent work from being claimed complete.

**Steps:**
- [ ] Test legal progress transitions and restart recovery.
- [ ] Test that `complete` requires recorded fresh verification evidence and a commit/reference where the plan expects one.

## Section 13.8 — Risk-Proportional Self-Review

After each coherent slice, the implementation agent re-reads the relevant diff and acceptance criteria. Review depth increases for:

- inventory/accounting/valuation;
- matched HODL and contribution controls;
- fees/slippage/fills/quantization/execution;
- timing/lookahead/replay determinism;
- research-family/OOS/multiplicity semantics;
- numerically delicate statistical/model logic;
- cross-package dependency/ownership changes;
- significant vectorization/performance rewrites.

**Required behavior:**
- use focused adversarial/property tests when warranted;
- use `systematic-debugging` when its trigger applies;
- use `verification-before-completion` before success/phase-complete claims and completion commits;
- inspect actual repository state rather than trusting a prior command summary;
- do not invoke another reviewer model or separately metered agent/CLI unless the user explicitly authorizes that model for the current task.

Self-review from fresh repository evidence is the autonomous-loop default. A future independent manual review may be performed deliberately after implementation if the user requests it; it is outside this autonomous sequential loop.

## Section 13.9 — Commit Discipline

**Behavior:**
- Create meaningful local commits only after the direct implementation slice passes its required verification/self-review.
- Never push automatically.
- Never amend/rebase previous user commits automatically.
- Commit only paths belonging to the coherent slice; preserve unrelated pre-existing dirty files unstaged.
- Record commit hash in progress.

**Steps:**
- [ ] Test staging-path selection in a temporary repo.
- [ ] Require planned-path diff to be clean after commit while allowing recorded unrelated dirt to remain.

## Section 13.10 — Hard Escalation Conditions

Stop the sequential mission immediately when continuation would require:

- changing the product economic objective;
- redefining matched-HODL-relative wealth as the primary metric or promoting coin accumulation/standalone fiat P&L over it;
- enabling leverage, borrowing, derivatives, interest-bearing mechanics, or unapproved assets;
- creating a second wallet/accounting owner;
- changing point-in-time/default fill semantics;
- changing benchmark definitions or the predeclared primary incremental control;
- changing fee/slippage/quantization/reference-price semantics that can alter economic results;
- changing dataset role, final-OOS commitment/consumption status, or relabeling viewed evidence as fresh holdout data;
- changing fixed-basket versus point-in-time universe eligibility/claim semantics;
- importing/coupling QAP v1/v2 at runtime;
- adding live order placement or private credentials;
- violating a plan Stop Condition;
- destructive Git operation;
- human secret/MFA/sudo input;
- unresolved verification failure where the approved contract cannot be satisfied without changing protected semantics.

The progress record names the exact section and evidence that caused escalation.

## Section 13.11 — Dry Run

**Steps:**
- [ ] Create a temporary toy Git repository and a tiny approved plan with two sequential sections.
- [ ] Exercise plan parsing, progress/checkpointing, Git guard, writer-ownership handoff, verification capture, commit recording, and restart recovery without launching another coding model.
- [ ] Inject an unrelated dirty file and verify preservation.
- [ ] Inject a failing verification and verify the state remains non-complete until the same implementation agent repairs/re-verifies it.
- [ ] Confirm read-only `status` performs no verification/review side effects and no automatic push/destructive Git actions occur.

## Phase Verification

```bash
uv run pytest -q tests/tools/agent
uv run ruff check tools/agent tests/tools/agent
uv run ruff format --check tools/agent tests/tools/agent
uv run pyright tools/agent tests/tools/agent
uv run python scripts/check_source_size.py
```

Then run the documented toy-repository dry run and inspect its progress/commit evidence once.

## Phase Exit Criteria

- [ ] Harness supports one sequential direct implementation agent; it launches no secondary coding/review model and never invokes Codex/another metered model without explicit user authorization.
- [ ] Approved plan sections and progress are recoverable across session interruption.
- [ ] Relevant Skills remain the implementation agent's review/debugging workflow rather than secondary-agent substitutes.
- [ ] One-writer-per-worktree ownership is enforced for mutations while read-only status/inspection remains available.
- [ ] Unrelated dirty state is preserved.
- [ ] Required verification/diff/self-review gates completion.
- [ ] Architecture/economic/live-capital changes escalate.
- [ ] Local commits may be recorded but nothing is pushed automatically.
- [ ] `src/qap` has no dependency on harness code.
- [ ] Toy-repository dry run succeeds without any multi-agent runtime.

## Stop Conditions

Do not add external coding-model integration, model providers, subagents, reviewer agents, worker pools, distributed queues, speculative planner agents, autonomous roadmap generation, auto-merge/push, broad self-modifying context, a persistent coding service, or duplicate MCP/Terminal/wait/logging/spool-management infrastructure already owned by `satori_bridge`. The implementation agent remains the single sequential owner of QAP engineering and self-review.
