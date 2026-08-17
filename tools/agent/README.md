# QAP Sequential Development Harness

`tools/agent/` is local development support for the **same main implementation agent** that is already working on QAP. It records approved-plan progress, Git scope/writer ownership, and bounded verification evidence. It does not decide the roadmap, implement product code on its own, or launch another coding/review process.

Nothing under `src/qap` imports this tooling. Runtime/progress data lives under `.qap-agent/`, which is Git-ignored.

## Context sources

The Phase-13 context audit found no contradiction that justified changing root instructions. Keep the effective context small and use these sources in precedence/order appropriate to the current task:

1. `AGENTS.md` — concise repository invariants and protected economic/action-space boundaries.
2. `implementation_prompt.md` — controlling direct-agent mission, writer ownership, phase sequence, Skills, verification and escalation rules.
3. `docs/plans/README.md` and `docs/superpowers/plans/2026-08-17-qap-master-implementation-plan.md` — phase ordering and dependencies.
4. The **explicit current approved plan path** and current section being implemented.
5. Only the design/research/decision documents referenced by that section when they are needed for a concrete decision.

Do not copy the full plan/design corpus into `AGENTS.md` or repeatedly scan every document. Repository/Git/process reality outranks stale local progress state.

## Direct-agent contract

The supported loop is:

```text
main ChatGPT implementation agent
  -> inspect repository reality
  -> invoke an applicable Skill when its trigger applies
  -> acquire/reconcile one-writer worktree ownership
  -> snapshot Git state
  -> record section/slice in_progress
  -> implement the coherent slice directly
  -> run focused verification
  -> inspect diff/scope
  -> self-review against plan + protected contracts
  -> repair findings
  -> run completion verification
  -> create a coherent local commit
  -> checkpoint commit + verification evidence
  -> release/handoff writer ownership
  -> continue sequentially
```

The harness never marks a section complete merely because a subprocess returned zero. `complete` requires a commit/reference and passing **latest evidence for every recorded verification command**. If a command fails and the same command later passes after repair, the newer result supersedes that command's old failure for completion gating; the historical evidence remains in the progress record/logs.

A status request is read-only. It does not run verification, create progress state, acquire a writer, modify Git, or perform cleanup.

## Approved plan parsing

Only an explicitly supplied path under `docs/plans/` or `docs/superpowers/plans/` is accepted. The harness never discovers arbitrary Markdown and decides it is executable.

```bash
uv run python tools/agent/qap_agent.py status \
  docs/plans/13-autonomous-development-harness.md

uv run python tools/agent/qap_agent.py section \
  docs/plans/13-autonomous-development-harness.md \
  --section 13.6
```

The parser uses QAP's real `## Section N.N — Title` grammar. Section bodies retain their Steps/Verification/Acceptance/Exit/Stop material, including phase-level verification/exit/stop content following the last numbered section.

## Local progress checkpoints

Progress is stored atomically at:

```text
.qap-agent/<plan-stem>/progress.json
.qap-agent/<plan-stem>/progress.md
.qap-agent/<plan-stem>/logs/
```

Start a section/slice checkpoint from the current repository snapshot:

```bash
uv run python tools/agent/qap_agent.py checkpoint \
  docs/plans/13-autonomous-development-harness.md \
  --section 13.6 \
  --status in_progress \
  --writer-id main-chatgpt \
  --writer-note "sole writer for this worktree" \
  --next-action "implement verification runner"
```

A later session should read `status`, inspect fresh Git/worktree/process reality, reconcile any writer record, and only then resume mutation.

After verified work has a local commit/reference:

```bash
uv run python tools/agent/qap_agent.py checkpoint \
  docs/plans/13-autonomous-development-harness.md \
  --section 13.6 \
  --status complete \
  --commit <commit-sha> \
  --next-action "continue to 13.7"
```

## Bounded verification

Run only reviewed repository-plan commands or an explicit verification command chosen by the implementation agent for the current slice:

```bash
uv run python tools/agent/qap_agent.py verify \
  docs/plans/13-autonomous-development-harness.md \
  --section 13.6 \
  --timeout 120 \
  --command "uv run pytest -q tests/tools/agent/test_verify.py"
```

The runner records exact command, exit code, duration and a bounded output tail in progress state. When invoked through the CLI, full command output is written under the plan's local `.qap-agent/.../logs/` directory. A timeout terminates the command process group and records exit code `124` with `timed_out=true`.

Do not use this runner to execute commands copied from untrusted network text without review. The runner also rejects known destructive Git commands such as hard reset/clean, push, rebase, merge, and branch deletion instead of treating them as verification.

## Git scope guard

`snapshot_git()` records:

- canonical Git worktree path;
- branch and HEAD;
- porcelain status and a status fingerprint;
- content fingerprints for every dirty path.

`assert_safe_scope()` compares a current snapshot with the section baseline. It preserves unrelated pre-existing dirt by requiring its status/content fingerprint to remain unchanged. New/changed paths must be in the reviewed allowed set. Deletions fail by default unless the caller explicitly declares the deletion allowed.

The guard returns the planned changed paths that are safe candidates for staging. It does **not** stage, commit, reset, stash, clean, merge, rebase, push, or delete branches automatically.

## Cooperative writer ownership

Writer ownership is separate from Terminal/PTY ownership. Use one writable implementation owner per Git worktree. Read-only status/inspection may coexist.

The helper lease lives at:

```text
.qap-agent/worktree-writer.json
```

Inspect without mutation:

```bash
uv run python tools/agent/qap_agent.py writer-status .
```

When the connected environment can supply a real durable owner process PID, acquire/release explicitly:

```bash
uv run python tools/agent/qap_agent.py writer-acquire . \
  --writer-id main-chatgpt \
  --owner-pid <durable-owner-pid> \
  --note "Phase 13 slice"

uv run python tools/agent/qap_agent.py writer-release . \
  --writer-id main-chatgpt
```

A different writer is blocked while the recorded PID is alive. If fresh process evidence shows the PID is dead, a new writer may replace the stale lease. The helper does not create a background ownership daemon; durable process/session lifetime remains the connected harness's responsibility.

## Responsibilities deliberately left to the connected harness

QAP does not reimplement infrastructure already owned by `satori_bridge` / `mcp-harness-local`:

- MCP transport/health;
- Terminal/tmux lifecycle and human/model PTY ownership;
- durable waits/timers;
- Bash output/spool retention;
- log rotation outside `.qap-agent` verification logs;
- primitive/tool routing.

Persistent processes are real tools (servers, builds, experiments, browsers), not secondary coding agents.

## Hard escalation conditions

Stop the sequential implementation slice and record the exact blocker before continuing if the required change would alter any protected boundary, including:

- primary matched-HODL-relative wealth objective or benchmark definitions;
- fee/slippage/fill/quantization/reference-price semantics that change economics;
- dataset role, final-OOS reservation/consumption, or reuse of viewed evidence as fresh holdout;
- fixed-basket versus point-in-time universe claim semantics;
- inventory/accounting ownership;
- spot-only/no-leverage/no-borrowing/no-derivatives/no-interest action space;
- QAP v1/v2 runtime coupling;
- live order placement or private credentials;
- approved-plan Stop Conditions;
- destructive Git operations;
- secret/password/MFA/sudo input;
- an unresolved verification failure that can only be "fixed" by weakening a protected contract.

User capital/risk decisions and architecture/public-contract/security ownership decisions are escalation items. Routine implementation details and necessary in-scope transitive changes are handled autonomously and reported.

## Prohibited behavior

The harness has no provider abstraction, prompt dispatcher, coding worker, reviewer worker, queue, scheduler, auto-merge/push facility, or persistent coding service. It must not be extended with those merely to make development appear more autonomous.

Never place passwords, private keys, API secrets, MFA values or sudo input in progress/checkpoint/log files.

## Toy-repository dry run

The repository contains one deterministic test that creates a temporary Git repository and exercises the complete sequential workflow without any external coding process:

```bash
uv run pytest -q tests/tools/agent/test_dry_run.py -s
```

It verifies:

- two-section plan parsing;
- unrelated dirty-file preservation;
- live second-writer rejection and explicit writer handoff;
- atomic checkpoint/restart recovery;
- scoped changed-path selection for staging;
- a failing verification that prevents completion;
- same-command repair/reverification;
- two local commits recorded into progress;
- no remote/push side effect.

## Phase-13 verification

```bash
uv run pytest -q tests/tools/agent
uv run ruff check tools/agent tests/tools/agent
uv run ruff format --check tools/agent tests/tools/agent
uv run pyright tools/agent tests/tools/agent
uv run python scripts/check_source_size.py
```

Before claiming Phase 13 complete, also inspect the actual Git diff/status, run the toy dry run once explicitly, and apply the repository's normal verification-before-completion discipline.
