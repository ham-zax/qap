# Phase 00 — Constitution and Repository Foundation Implementation Plan

**Goal:** Create the smallest executable clean-QAP Python repository with deterministic local tooling and concise project instructions, without introducing product behavior.

**Architecture:** Establish a standard `src/` Python package and test layout. Keep repository policy in a short root `AGENTS.md`; keep economic design in the approved design spec rather than duplicating it across agent instructions.

**Tech Stack:** Python 3.14, `uv`, pytest, Ruff, Pyright, Git.

## Global Constraints

- This phase must not implement trading, market data, models, APIs, or web code.
- QAP v1/v2 remain read-only and are referenced only through `docs/REFERENCE_BOUNDARY.md`.
- Generated market data, run artifacts, secrets, virtual environments, and web build output must be excluded from Git.
- No worktree is needed for this clean empty repository unless later local state creates a real isolation reason.

## File Map

**Create:**

- `pyproject.toml` — project metadata, Python version, pytest/Ruff/Pyright dev dependencies and configuration.
- `uv.lock` — resolved Python dependencies created by `uv sync`.
- `.gitignore` — generated/runtime/secrets exclusions.
- `AGENTS.md` — concise mission, invariants, reference boundary, planning/execution rules.
- `src/qap/__init__.py` — package marker/version surface only.
- `tests/test_smoke.py` — proves the package imports under the managed environment.
- `scripts/check_source_size.py` — repository maintainability guard for hand-written Python/TypeScript/TSX source and tests.

**Existing design inputs:**

- `docs/superpowers/specs/2026-08-17-qap-system-design.md`
- `docs/superpowers/specs/2026-08-17-qap-web-operations-design.md`
- `docs/REFERENCE_BOUNDARY.md`
- `docs/plans/README.md`

## Section 00.1 — Python Project Metadata

**Interfaces:**
- Consumes: repository design constraints.
- Produces: installable local package and repeatable dev environment.

**Steps:**
- [ ] Create `pyproject.toml` with project name `qap`, Python requirement `>=3.14,<3.15`, package discovery from `src`, and no runtime dependencies yet.
- [ ] Add dev dependencies `pytest`, `ruff`, and `pyright` through `uv`.
- [ ] Configure pytest to discover `tests/` and Ruff to target Python 3.14.
- [ ] Configure Pyright for strict checking of `src/qap` with test checking enabled but without forcing third-party stub packages that are not yet needed.
- [ ] Run `uv sync` to create `uv.lock`.

**Verification:**

```bash
uv sync
uv run python -V
```

**Acceptance criteria:**
- Environment resolves reproducibly from `pyproject.toml` + `uv.lock`.
- No runtime scientific/web dependencies are present.

## Section 00.2 — Repository Hygiene

**Interfaces:**
- Consumes: planned runtime artifact locations.
- Produces: Git boundary that prevents generated/private state from being committed.

**Steps:**
- [ ] Create `.gitignore` entries for `.venv/`, Python caches, `.pytest_cache/`, `.ruff_cache/`, `.pyright/`, coverage output, `data/`, `runs/`, `web/node_modules/`, `web/dist/`, local `.env*` files except an explicitly documented `.env.example` if one is later needed, and editor/OS noise.
- [ ] Do not ignore committed deterministic fixtures under `tests/fixtures/`.
- [ ] Confirm `git status --ignored --short` classifies a temporary `data/_probe` and `runs/_probe` as ignored, then delete the probes.

**Verification:**

```bash
mkdir -p data runs
touch data/_probe runs/_probe
git status --ignored --short
rm data/_probe runs/_probe
```

**Acceptance criteria:**
- Runtime artifacts are ignored.
- Test fixtures remain commit-eligible.

## Section 00.3 — Concise Agent Context

**Interfaces:**
- Consumes: system design and historical reference constitution.
- Produces: minimal root instructions for future coding agents.

**Steps:**
- [ ] Create `AGENTS.md` with only: product one-liner, core economic object, spot-only action boundary, one-state-one-owner rule, matched-HODL control, v1/v2 read-only reference rule, no-live-execution gate, source-size/God-object rule, commands, and instruction to follow `docs/plans/` for approved work.
- [ ] Explicitly forbid copying the old repository architecture by default.
- [ ] Keep `AGENTS.md` short enough to be read in one screenful; link to design docs instead of repeating them.

**Verification:**

```bash
wc -l AGENTS.md
rg -n "v1|v2|HODL|spot|live|docs/plans" AGENTS.md
```

**Acceptance criteria:**
- Instructions are sufficient to prevent major scope/authority errors without becoming another governance corpus.

## Section 00.4 — Source-Size and God-Object Guard

**Interfaces:**
- Consumes: repository paths.
- Produces: deterministic verification result for hand-written source/test file size.

**Behavior:**
- Scan hand-written `.py`, `.ts`, and `.tsx` files under `src/`, `tests/`, `scripts/`, `tools/`, and `web/src/` when those directories exist.
- Exclude known generated artifacts such as `web/src/routeTree.gen.ts`, generated OpenAPI schema files, lockfiles, vendor directories, build output, and data/fixture files.
- Files below 500 lines pass silently.
- Files from 500 through 700 lines emit a clear review warning and still return success, so agents must decompose before adding more responsibility.
- Files above 700 lines fail with non-zero exit unless their exact path/pattern is present in the narrow generated/exempt list.
- The checker itself must remain small and direct; no configuration framework or dependency is added for it.

**Steps:**
- [ ] Write `scripts/check_source_size.py` using the standard library only.
- [ ] Add focused tests only if the checker grows enough logic to justify them; otherwise verify it with temporary probe files in a bounded command/script self-test.
- [ ] Run it against the repository and record the command in `AGENTS.md`.

**Verification:**

```bash
uv run python scripts/check_source_size.py
```

**Acceptance criteria:**
- A temporary 701-line hand-written source probe fails.
- A temporary 500–700-line probe warns.
- A normal small file passes.
- Generated/lock/vendor/data paths are excluded only by explicit narrow rules.

## Section 00.5 — Importable Package and Smoke Test

**Interfaces:**
- Consumes: managed Python environment.
- Produces: first executable verification boundary.

**Steps:**
- [ ] Create `src/qap/__init__.py` with package docstring and `__version__ = "0.1.0-dev"` only.
- [ ] Create `tests/test_smoke.py` that imports `qap` and asserts the development version string is non-empty.
- [ ] Do not add domain classes or placeholder packages in this phase.

**Verification:**

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
uv run python scripts/check_source_size.py
```

**Acceptance criteria:**
- All commands pass.
- `src/qap` contains no speculative modules.

## Phase Exit Criteria

- [ ] Repository is executable through `uv`.
- [ ] Smoke test, lint, format check, and type check pass.
- [ ] Git excludes generated/private runtime artifacts.
- [ ] `AGENTS.md` is concise and points to the canonical design/reference docs.
- [ ] Source-size verification enforces the 500-line review threshold / 700-line hard cap for hand-written code.
- [ ] No product capability has been implemented yet.

## Stop Conditions

Return to design review instead of expanding Phase 00 if repository setup appears to require Docker, a database, a JS workspace, CI, plugin architecture, or historical-repo runtime coupling. None is justified here.
