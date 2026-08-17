# Phase 07 — Experiments, Controls, and Research Protocol Implementation Plan

**Goal:** Make QAP runs reproducible and falsifiable with small frozen manifests, matched HODL, a simple non-model rebalancing control, explicit IS/OOS labels, and concise durable result artifacts.

**Architecture:** `qap.experiment` orchestrates already-owned domain components. It freezes inputs and records provenance/results but does not become a candidate-promotion bureaucracy or a second runtime architecture.

**Tech Stack:** Python 3.14, Pydantic for manifest/result boundary validation, JSON, Parquet for derived time series, Git provenance, pytest.

## Global Constraints

- Research serves the accumulation product.
- A run must be reproducible from one manifest plus immutable data fingerprints and code provenance.
- Positive, neutral, and negative outcomes are equally valid artifacts.
- In-sample and OOS labels are explicit.
- No experiment result silently changes default policy/model settings.
- No global registry, promotion state machine, candidate dossier hierarchy, or documentation generator is created.

## File Map

**Modify:**
- `pyproject.toml` — add Pydantic.

**Create:**
- `src/qap/experiment/__init__.py`
- `src/qap/experiment/manifest.py` — strict frozen run manifest.
- `src/qap/experiment/provenance.py` — code/data/config provenance capture.
- `src/qap/experiment/baselines.py` — simple periodic rebalance control.
- `src/qap/experiment/runner.py` — compose replay + evaluation.
- `src/qap/experiment/artifacts.py` — compact JSON/Parquet result writer/reader.
- `src/qap/experiment/__main__.py` — minimal `python -m qap.experiment <manifest>` entry point.
- `tests/unit/experiment/test_manifest.py`
- `tests/unit/experiment/test_baselines.py`
- `tests/unit/experiment/test_artifacts.py`
- `tests/scenarios/test_experiment_reproducibility.py`
- `tests/scenarios/test_negative_experiment_is_recorded.py`
- `tests/fixtures/experiments/two_asset_dummy.json`

## Section 07.1 — Frozen Experiment Manifest

**Interfaces:**
- Consumes: explicit human-authored JSON.
- Produces: validated immutable experiment configuration.

**Manifest fields:**
- schema version;
- experiment name/description;
- admitted basket and frozen starting quantities;
- optional analysis anchor;
- venue/instruments/interval;
- data window start/end and one or more data-source entries containing a logical dataset ID, a path relative to the configured data root, and the expected semantic fingerprint;
- relationship evidence/model ID + config;
- policy ID + config;
- execution cost config;
- benchmark/control config;
- data-role label (`in_sample`, `validation`, `oos`, `forward_paper`);
- predeclared primary metric and success threshold;
- optional deterministic random seed when a future model requires randomness.

**Behavior:**
- Unknown fields are rejected.
- Dataset locator paths must be relative and must not contain `..`; the configured operational data root is supplied by the runner/API environment.
- Locator path is not authoritative identity: the runner loads the located dataset and verifies its expected semantic fingerprint before use.
- Business settings come from manifest, not environment variables.
- Manifest parsing does not load data or mutate runtime state.

**Steps:**
- [ ] Write validation tests for complete manifest, unknown field, invalid basket, invalid timing window, and missing fingerprint.
- [ ] Implement Pydantic boundary model whose validated values are converted to domain types at composition boundaries.

## Section 07.2 — Code/Data/Config Provenance

**Interfaces:**
- Consumes: validated manifest, loaded datasets, local Git state.
- Produces: `RunProvenance`.

**Behavior:**
- Record manifest canonical SHA-256.
- Record every authoritative dataset fingerprint.
- Record a deterministic `code_fingerprint` over the sorted relative paths and bytes of authoritative local code/config needed by the run (`src/qap`, `pyproject.toml`, and `uv.lock`).
- Record current Git commit hash and dirty flag as supplemental human provenance.
- Record QAP package version and UTC run timestamp.
- Dirty-tree research is allowed because the authoritative code fingerprint distinguishes changed source bytes even when the Git commit is unchanged.
- Provenance never shells into or imports the old QAP repository.

**Steps:**
- [ ] Implement canonical manifest serialization/hash.
- [ ] Implement deterministic code fingerprinting from sorted repository-relative paths + file bytes for `src/qap`, `pyproject.toml`, and `uv.lock`; exclude caches/generated artifacts.
- [ ] Capture `git rev-parse HEAD` and `git status --porcelain` through a focused helper with explicit failure behavior when Git metadata is unavailable.
- [ ] Test manifest-hash sensitivity to authoritative values, insensitivity to JSON key ordering, and code-fingerprint sensitivity to a changed source byte.

## Section 07.3 — Simple Rebalancing Control

**Interfaces:**
- Consumes: starting basket weights, declared cadence in bars, current valuation snapshot.
- Produces: target allocation decisions through the same Phase-05/06 execution path.

**Behavior:**
- At fixed cadence, request restoration to the frozen starting value weights.
- Otherwise no action.
- Uses identical cost/execution/timing semantics as model-driven QAP.
- Exists as a baseline/control, not an endorsed production strategy.

**Steps:**
- [ ] Write a deterministic cadence test.
- [ ] Implement control by producing normal `PolicyDecision`/`AllocationTarget` objects; do not create a separate backtester.

## Section 07.4 — Experiment Runner

**Interfaces:**
- Consumes: manifest + data resolved by fingerprint.
- Produces: strategy replay, HODL comparison, optional simple-control replay, and one result record.

**Behavior:**
- Validate data fingerprints before replay.
- Construct fresh starting portfolio independently for strategy/HODL/control.
- Run strategy and control through the same execution engine.
- Evaluate all terminal states using the same terminal valuation snapshot.
- Classify result as `positive` when the primary metric is greater than the predeclared threshold, `neutral` when exactly equal, and `negative` when below; classification has no promotion side effect.

**Steps:**
- [ ] Implement orchestration using composition functions, not a generic workflow engine.
- [ ] Assert benchmark same-start invariant before result creation.

## Section 07.5 — Durable Artifacts

**Interfaces:**
- Consumes: manifest, provenance, replay traces, economic results.
- Produces: one run directory under gitignored `runs/<run_id>/`.

**Artifact layout:**

```text
runs/<run_id>/
  manifest.json
  provenance.json
  result.json
  performance.parquet
  inventory.parquet
  events.jsonl
```

**Behavior:**
- `run_id` is a deterministic prefix/hash of manifest hash + ordered data fingerprints + `code_fingerprint`. Git commit/dirty state remains supplemental provenance and therefore cannot cause two different dirty source trees to collide under one run ID.
- `result.json` is compact and contains primary/secondary terminal metrics and status.
- `performance.parquet` contains one row per evaluation timestamp with strategy value, matched-HODL value, optional simple-control value, and relative-performance fields. Exact financial values use a lossless representation; API chart DTOs may convert presentation copies to floats.
- `inventory.parquet` is long-form with timestamp, role (`strategy`, `hodl`, optional `control`), asset, exact quantity/value representation, and presentation weight. It is the source for allocation/inventory history.
- `events.jsonl` is append-ordered decision/rebalance/fill trace data sufficient to reconstruct web markers and audit execution identity without serializing Python objects.
- Large bar inputs are not copied into each run; `manifest.json` retains the validated relative locator plus expected fingerprint.
- Existing `runs/<run_id>/` is never overwritten. A repeated semantic run is executed under a fresh temporary test/output root when reproducibility is being checked; production tooling must not silently replace prior artifacts.
- Artifact reader validates schema versions for JSON and tabular files.

**Steps:**
- [ ] Write artifact roundtrip test in temporary directory.
- [ ] Confirm run directory creation is deterministic and does not overwrite a semantically different run.

## Section 07.6 — Minimal Command Entry Point

**Interfaces:**
- Consumes: path to one manifest.
- Produces: run ID, status, primary metric, artifact path on stdout; non-zero exit on invalid run setup.

**Behavior:**
- Invocation: `uv run python -m qap.experiment path/to/manifest.json`.
- No command tree, interactive wizard, global config discovery, or rich CLI framework.
- Human-readable output remains short; machine authority is the artifact.

**Steps:**
- [ ] Implement argument parsing with standard-library `argparse`.
- [ ] Add one subprocess-style scenario test only if direct function tests cannot cover command exit/output economically.

## Section 07.7 — Reproducibility and Negative-Result Scenarios

**Steps:**
- [ ] Run the same fixture experiment twice under two isolated temporary run roots and assert authoritative result fields/artifact series match while ignoring non-authoritative wall-clock provenance fields.
- [ ] Assert a deliberately bad dummy policy produces and persists a `negative` result rather than throwing because performance is poor.
- [ ] Alter one dataset value and assert expected fingerprint mismatch prevents the run.
- [ ] Change data-role from `in_sample` to `oos` and confirm the label appears in the result/provenance without changing the financial calculation itself.

**Verification:**

```bash
uv run pytest -q tests/unit/experiment tests/scenarios/test_experiment_reproducibility.py tests/scenarios/test_negative_experiment_is_recorded.py
```

## Phase Verification

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
```

## Phase Exit Criteria

- [ ] Manifest/config/data/code provenance is explicit and durable.
- [ ] Strategy, HODL, and simple control use the same starting basket and timing/cost semantics.
- [ ] IS/OOS role is explicit.
- [ ] Negative and neutral results persist normally.
- [ ] A run is reproducible without a giant research-governance layer.
- [ ] Historical v1/v2 runtime is not called.

## Stop Conditions

Do not add promotion workflows, candidate registries, experiment databases, notebooks as authoritative runners, distributed job queues, automatic hyperparameter search, or a generalized backtest framework. Add only when a later concrete research problem proves the need.
