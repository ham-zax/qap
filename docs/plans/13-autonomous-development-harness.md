# Phase 13 — Autonomous Development Harness Implementation Plan

**Goal:** Build a local development harness that can continue executing already-approved QAP plan sections autonomously, with bounded scope, explicit verification, progress persistence, and hard escalation on architecture/economic/live-capital changes.

**Architecture:** The harness lives under `tools/agent/` and `.qap-agent/`; it is development tooling only and never becomes a dependency of `src/qap`. It launches one supported local coding-agent runtime at a time with a narrowly scoped mission extracted from an approved plan, then independently checks repository state and required verification before advancing.

**Tech Stack:** Python 3.14 standard library first, Git, one actually installed/authenticated local agent CLI selected at Phase-13 start, existing Superpowers workflow conventions. No orchestration framework or multi-agent platform unless a later measured need exists.

## Global Constraints

- Implement this phase only after the manual QAP engineering workflow is proven through earlier phases.
- The harness executes approved plans; it does not invent product roadmap or economic policy.
- One agent process works on one bounded plan section at a time in the initial harness.
- No runtime import from `tools/agent` into `src/qap`.
- Preserve unrelated user changes and never run destructive Git operations automatically.
- No secret/password/MFA input through agent prompts or chat logs.
- Architecture/economic/action-space/live-capital changes stop and escalate.
- The harness may operate for long periods on the user's machine, but ChatGPT must never claim background work unless the local harness is actually the process performing it.

## File Map

**Modify:**
- `.gitignore` — ignore `.qap-agent/` local progress/runtime state.
- `AGENTS.md` — only if a context audit proves a small change is necessary; do not expand by default.

**Create:**
- `tools/agent/README.md` — operator usage and stop conditions.
- `tools/agent/qap_agent.py` — command entry point and main loop.
- `tools/agent/plan.py` — approved plan/section extraction.
- `tools/agent/state.py` — progress JSON/Markdown persistence under `.qap-agent/`.
- `tools/agent/git_guard.py` — baseline status/diff/commit safety checks.
- `tools/agent/runtime.py` — one selected installed agent-runtime adapter/command builder.
- `tools/agent/verify.py` — bounded verification command execution and evidence capture.
- `tools/agent/prompt.py` — mission prompt construction from exact plan section + design constraints.
- `tests/tools/agent/test_plan.py`
- `tests/tools/agent/test_state.py`
- `tests/tools/agent/test_git_guard.py`
- `tests/tools/agent/test_prompt.py`
- `tests/tools/agent/test_loop_state_machine.py`

## Section 13.1 — Context Audit Before Harness Code

**Purpose:** prevent the autonomous loop from amplifying contradictory or bloated instructions.

**Steps:**
- [ ] Run the `context-audit` workflow over root `AGENTS.md`, relevant Superpowers/local harness instructions, and repository-level plan references.
- [ ] Remove/shorten only context that is demonstrably contradictory, duplicated, stale, or over-constraining; preserve the canonical design/reference boundaries.
- [ ] Record the final agent-context sources in `tools/agent/README.md`.
- [ ] Do not copy full design/plan documents into `AGENTS.md`; the harness injects the exact current plan section at runtime.

**Acceptance criteria:**
- One concise root context plus exact mission/plan section is sufficient for an agent to act without scanning the entire docs tree.

## Section 13.2 — Select One Real Local Agent Runtime

**Purpose:** use the machine's actual available agent rather than building a fictional adapter layer.

**Deterministic selection process at Phase-13 start:**
1. Probe known supported installed CLIs in the user's preferred order at that time.
2. Select exactly one CLI that is installed, non-interactively invokable, and already authenticated without exposing a secret.
3. Record its executable/version and verified noninteractive invocation in `tools/agent/README.md`.
4. Implement only that runtime in `runtime.py`.
5. If no suitable runtime exists, stop Phase 13; do not create a generic adapter framework for hypothetical agents.

**Steps:**
- [ ] Run bounded `command -v`/version probes.
- [ ] Execute one harmless non-writing probe against a temporary prompt/repository fixture.
- [ ] Capture exit-code/stdout/stderr behavior needed by the harness.

## Section 13.3 — Approved Plan Parser

**Interfaces:**
- Consumes: one explicit plan path under `docs/plans/` or `docs/superpowers/plans/` and optional section ID.
- Produces: ordered bounded missions.

**Behavior:**
- Harness never discovers arbitrary docs and decides they are executable.
- User/operator passes the approved plan path.
- Parser recognizes plan headings such as `Section 05.3` and their Steps/Verification/Acceptance/Exit/Stop content.
- A section is the default autonomous mission unit; checklist micro-items are not separate agent sessions unless the plan itself requires it.
- Stop Conditions are included in every mission prompt.
- Parse failure stops before invoking an agent.

**CLI shape:**

```bash
uv run python tools/agent/qap_agent.py run docs/plans/05-policy-target-allocation-and-rebalancing.md
uv run python tools/agent/qap_agent.py run docs/plans/05-policy-target-allocation-and-rebalancing.md --section 05.3
```

**Steps:**
- [ ] Write parser fixtures/tests using actual QAP plan structure.
- [ ] Implement only the heading/checklist grammar this repository uses; no general Markdown parser framework unless needed.

## Section 13.4 — Persistent Progress State

**Interfaces:**
- Consumes: plan path, section IDs, agent outcomes, verification evidence, commits.
- Produces: `.qap-agent/<plan-slug>/progress.json` and `progress.md`.

**State per section:**
- `pending | in_progress | complete | blocked`;
- baseline Git commit/status fingerprint;
- agent runtime/version;
- start/end timestamps;
- resulting commit hash when committed;
- verification commands and exit codes;
- blocker/retry reason.

**Behavior:**
- State writes are atomic (`tempfile` + replace).
- On restart, harness resumes the first non-complete section after validating repository state against recorded progress.
- Progress is local/gitignored; plans and code commits remain durable Git truth.

**Steps:**
- [ ] Write crash/resume and corrupted-state tests.
- [ ] Provide `status` command that reads progress without launching an agent.

## Section 13.5 — Git Guard

**Interfaces:**
- Consumes: repository status before/after each mission.
- Produces: safe-to-run/safe-to-advance decision.

**Behavior:**
- Capture `git status --porcelain=v1`, current branch, and HEAD before mission.
- If unrelated dirty state exists before first mission, record paths and include "preserve these paths" in prompt; do not reset/stash them automatically.
- After mission, verify changed paths are plausibly inside the approved section's file map plus necessary dependency/lock files.
- Unexpected broad/deletion changes block advancement for review.
- Harness never executes `git reset --hard`, `git clean -fd`, force push, branch deletion, or automatic merge.

**Steps:**
- [ ] Test with temporary Git repository containing unrelated dirty file.
- [ ] Test allowed planned change and unexpected destructive change detection.

## Section 13.6 — Mission Prompt Construction

**Interfaces:**
- Consumes: exact plan section, root `AGENTS.md`, relevant design/reference paths, baseline Git state.
- Produces: bounded agent prompt.

**Prompt includes:**
- repository path;
- exact plan path/section text;
- instruction to inspect only necessary files;
- explicit unrelated dirty paths to preserve;
- requirement to follow repository `AGENTS.md` and `docs/REFERENCE_BOUNDARY.md`;
- prohibition on broadening scope/implementing future phases;
- exact plan verification/acceptance/stop conditions;
- requirement to leave evidence in normal Git diff/tests, not write a new essay unless plan requests docs;
- escalation instruction for architecture/economic/action-space/live-capital ambiguity.

**Steps:**
- [ ] Snapshot-test the prompt semantically with focused assertions (mission text, stop conditions, dirty paths, no future-phase content).
- [ ] Keep prompt concise enough that the agent can hold target code + mission in context.

## Section 13.7 — Single-Mission Execution Loop

**State machine:**

```text
load approved plan/progress
 -> select next pending section
 -> git safety snapshot
 -> mark in_progress
 -> launch one agent runtime
 -> collect exit/evidence
 -> inspect git diff
 -> run required verification
 -> inline review against section acceptance/stop conditions
 -> complete+commit OR one bounded repair attempt OR blocked
 -> continue to next section
```

**Behavior:**
- Agent process must have a finite per-mission timeout configured by operator/harness; timeout marks blocked rather than spawning duplicates.
- A successful agent exit is not sufficient; verification and diff guard must pass.
- First failed verification may trigger one repair prompt containing only failure evidence and original mission.
- Second failure blocks and stops the loop for human review.
- A blocked section prevents later dependent sections from auto-running.

**Steps:**
- [ ] Implement loop state machine with a fake runtime in tests.
- [ ] Test success, agent failure, verification failure + successful repair, repeated failure, timeout, and stop-condition escalation.

## Section 13.8 — Verification Runner

**Interfaces:**
- Consumes: verification commands explicitly present in the plan section plus repository-global affected checks when the plan requires them.
- Produces: command/exit/duration/output-tail evidence.

**Behavior:**
- No shell interpolation from arbitrary untrusted network input; commands originate from reviewed repository plans.
- Run section-focused verification first.
- Do not automatically run all phases/full suites when the plan does not require it.
- Output is bounded in progress state; full logs may be stored under `.qap-agent/<plan>/logs/`.

**Steps:**
- [ ] Implement subprocess execution with timeout and captured output.
- [ ] Preserve exact command and exit code.

## Section 13.9 — Inline Review and Scope Control

**Review checklist after each mission:**
- section acceptance criteria satisfied;
- no future-phase work;
- no new speculative abstraction/dependency;
- no changed hand-written source/test file exceeds 700 lines; any file at 500–700 lines is explicitly reviewed for decomposition before further growth;
- no God-object/module with multiple unrelated reasons to change, even if under the numeric cap;
- no change to economic objective, matched-HODL semantics, action-space, state ownership, timing, historical-reference boundary, or live authority;
- no unrelated user change modified;
- verification evidence fresh.

**Behavior:**
- Review can reject a technically passing diff for scope/architecture violation.
- The harness does not invent an independent "reviewer agent" unless actual subagent tooling is later available and deliberately adopted.

## Section 13.10 — Commit Discipline

**Behavior:**
- After a section passes verification/review, create one Git commit with message `phase XX section YY: <section title>`.
- Never push automatically in initial harness.
- Never amend/rebase previous user commits automatically.
- Commit only paths belonging to the mission; preserve unrelated pre-existing dirty files unstaged.
- Record commit hash in progress.

**Steps:**
- [ ] Test staging path selection in temporary repo.
- [ ] Require clean planned-path diff after commit while allowing recorded unrelated dirt to remain.

## Section 13.11 — Hard Escalation Conditions

Stop the autonomous loop immediately when work would require:

- changing the product economic objective;
- redefining matched-HODL-relative wealth as the primary metric or promoting coin accumulation/standalone fiat P&L over it;
- enabling leverage, borrowing, derivatives, interest-bearing mechanics, or unapproved assets;
- creating a second wallet/accounting owner;
- changing point-in-time/default fill semantics;
- importing/coupling QAP v1/v2 at runtime;
- adding live order placement or private credentials;
- violating a plan Stop Condition;
- destructive Git operation;
- human secret/MFA/sudo input;
- selecting work not contained in the approved plan;
- unresolved repeated verification failure.

The progress record must name the exact section and evidence that caused escalation.

## Section 13.12 — Dry Run Before Real Autonomous Use

**Steps:**
- [ ] Create a temporary toy Git repository and a tiny approved plan with two independent sections.
- [ ] Run the full harness loop using the selected real agent runtime on harmless file/test changes.
- [ ] Interrupt/restart between sections and verify resume.
- [ ] Inject an unrelated dirty file and verify preservation.
- [ ] Inject a failing verification and verify one repair then block behavior.
- [ ] Confirm no automatic push/destructive Git actions occur.

Only after the dry run passes should the harness operate on QAP implementation plans.

## Phase Verification

```bash
uv run pytest -q tests/tools/agent
uv run ruff check tools/agent tests/tools/agent
uv run ruff format --check tools/agent tests/tools/agent
uv run pyright tools/agent tests/tools/agent
uv run python scripts/check_source_size.py
```

Then run the documented toy-repository dry run and inspect its progress/commits manually once before enabling unattended local execution.

## Phase Exit Criteria

- [ ] One real local agent runtime is supported and verified.
- [ ] Harness executes exact approved plan sections sequentially.
- [ ] Progress survives interruption.
- [ ] Unrelated dirty state is preserved.
- [ ] Required verification/diff review gates advancement.
- [ ] One bounded repair attempt is enforced; repeated failure blocks.
- [ ] Architecture/economic/live-capital changes escalate.
- [ ] Harness commits locally but does not push automatically.
- [ ] `src/qap` has no dependency on harness code.
- [ ] Toy-repository autonomous dry run succeeds before QAP use.

## Stop Conditions

Do not add multi-agent swarms, distributed queues, speculative planner agents, autonomous roadmap generation, auto-merge/push, broad self-modifying context, or a persistent service until the single-agent approved-plan loop has demonstrated a concrete limitation that justifies the added mechanism.
