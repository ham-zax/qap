# QAP Scanner V1 Slice-2 Results

Date: 2026-08-18
Status: prospective/current execution-evidence implementation is complete and repository-verified; this is not final-OOS evidence and not a trading recommendation.

## Verified source state

- Branch: `qap-implementation-20260818`
- Milestone-6 implementation commit: `7d57b66` (`feat: complete scanner slice2 prospective vertical`)
- First repository verification closure: `dbc968a` (`test: close scanner slice2 completion gates`)
- Seven-finding vertical remediation commit: `809431c` (`fix: close slice2 vertical review seams`)
- Final repository verification source state: `809431c`
- Slice 1 remains the historical discovery/replay prerequisite and was not reopened during Slice-2 completion.
- Slice 3 remains deferred behind its separate design/approval gate.

## Scope closed by Slice 2

Slice 2 now provides the bounded vertical path approved by the corrected design:

```text
completed Slice-1 survivor
  -> immutable CandidateFreeze / cohort enrollment
  -> exact forward checkpoint information state
  -> ordinary QAP prospective replay
  -> immutable ForwardOutcome
  -> bounded public Binance/Gate L1/depth/metadata evidence
  -> explicit-capital directional capacity qualification
  -> research_only / small_capacity / tradable_now
  -> candidate/cohort scoreboard without portfolio aggregation
```

The operator surface is intentionally small:

```text
python -m qap.scanner.forward_cli freeze ...
python -m qap.scanner.forward_cli advance ...
python -m qap.scanner.forward_cli capture ...
python -m qap.scanner.forward_cli qualify ...
python -m qap.scanner.forward_cli show ...
```

There is no scheduler, database, private exchange action, order placement, credential authority, combined candidate inventory allocator, or Slice-3 basket execution path.

## Contract evidence

### Prospective causality and cohort semantics

- `CandidateFreeze` owns the immutable frozen candidate/protocol/control/cost lineage.
- `forward_start` is strictly after `frozen_at`.
- the first counted outcome completes strictly after `forward_start`;
- zero-new-member automatic cohorts are valid evidence;
- active identical semantic freezes are represented as reselections rather than duplicate concurrent experiments;
- matured freezes may permit a later new prospective generation;
- automatic and manual membership remain separately attributable.

### Checkpoint identity and physical provenance

`ForwardCheckpoint.checkpoint_id` is semantic: it binds dataset identity plus the exact replay-prefix information-state fingerprints and causal boundaries. The replay prefix includes the frozen warm-up window and the bar ending at `forward_start`, because ordinary QAP consumes those rows to establish the frozen replay state before scoring later observations. Whole-source fingerprints remain persisted for physical admission, tamper detection, and replay reproducibility but do not re-identify the semantic checkpoint when only later physical source extent changes. Same-cutoff reuse recomputes this semantic checkpoint identity and aborts on mismatch rather than returning stale evidence.

Ordinary QAP run identity remains a physical/reproducibility identity. Prospective QAP manifests require the exact admitted whole-source fingerprint recorded by the checkpoint. If the current catalog points to a different whole-source artifact, replay is denied with a catalog/fingerprint mismatch rather than silently minting a different authoritative run for the same checkpoint. This satisfies the design contract that the same freeze + future slice reproduces the same run/result or fails loudly.

### Failure taxonomy

Generation-fatal research-integrity failures are not downgraded to normal candidate outcomes. Frozen protocol/identity violations, source fingerprint mismatch, artifact-integrity failures, reserved data violations and equivalent setup-integrity failures propagate and deny publication.

Candidate-specific replay failures that preserve the frozen evidence contract are represented as `ForwardOutcome(status=invalid, ...)` with a detailed reason and remain visible in the cohort denominator.

### Artifact integrity and append-only persistence

- immutable cohort authority (`cohort.json` and `freezes.parquet`) is sealed and revalidated with the neutral `qap.artifact_integrity` exact-file/digest primitive;
- `checkpoints.parquet` and `outcomes.parquet` are explicitly derived indexes and are rebuildable from independently integrity-validated checkpoint generations after interruption;
- checkpoint generations are independently immutable and integrity-validated before read/reindex;
- checkpoint indices advance monotonically per freeze; retroactive backfill is rejected;
- qualification no longer mutates a completed checkpoint;
- each explicit-capital qualification is a separate immutable append-only generation keyed by checkpoint/freeze/as-of/capital/evidence/QAP references;
- qualification evidence also uses the neutral exact-file integrity primitive.

### Public capture and capacity

- Binance and Gate public Spot capture are bounded and unauthenticated;
- live capture observation time is owned by the capture operation rather than supplied by an operator CLI timestamp;
- the typed prospective protocol freezes shallow depth at top 20 levels per side;
- market metadata preserves public tradability/order constraints rather than dropping non-tradable state;
- qualification requires the frozen 14-day capture contract (95% overall and 90% per UTC day at the declared cadences);
- book cost is measured against mid and includes spread/taker impact;
- buy and sell `C95`, `q_star` and `q_safe = 0.5 * q_star` remain direction-specific;
- required transition fractions use the frozen structural 20% floor plus larger observed drift demand;
- sell-side evaluated sizes become infeasible when the actual book walk requires base quantity above the venue maximum, allowing the existing bisection to find the executable boundary;
- unfillable snapshots remain denominator failures rather than disappearing;
- explicit-capital economics are established only through ordinary QAP replay with measured baseline slippage and the frozen adverse scenario;
- qualification is an independent current claim at explicit UTC `as_of`; ordinary QAP first replays the frozen candidate through that timestamp, and only observations inside the causal 14-day window ending at that same `as_of` enter capture evidence identity.

## No-network vertical evidence

The deterministic Slice-2 scenario exercises the real vertical owners without exchange network access:

1. produce a legitimate Slice-1 deep-replay survivor through the existing manual-replay path;
2. freeze it before future observations exist;
3. publish new immutable forward source artifacts under the same dataset identities;
4. advance the cohort through ordinary QAP;
5. publish a `partial` prospective outcome;
6. qualify with insufficient capture and obtain `research_only / microstructure_coverage_insufficient`;
7. advance the qualification clock beyond the short prospective horizon and supply deterministic local L1/depth/metadata capture satisfying the full 14-day contract at explicit `as_of`;
8. run ordinary QAP through that current `as_of`, then run explicit-capital QAP qualification at the same timestamp;
9. publish the evidence-bound qualification returned by the ordinary QAP economic gates, with non-null current-state and requested-capital QAP run IDs when those replays are required;
10. expose automatic scanner-selection economics separately from manual-only and all-selection evidence through the scoreboard.

Additional negative paths are explicit:

- zero-new-member cohort remains visible;
- a reproducible candidate-specific forward-data gap becomes `INVALID` rather than disappearing;
- unfillable depth remains fail-closed;
- fatal provenance/protocol/integrity failures abort instead of being represented as candidate `INVALID`.

The deterministic qualification scenario is implementation evidence using synthetic/local market data. Its economic classification is whatever ordinary QAP establishes for that exact synthetic state; it is not a statement that a real market is currently tradable at that capital.

## Review-finding closure

The later six-finding Slice-2 review against `01f3234` is closed in the verified `dbc968a` state:

1. fatal protocol/integrity failures are separated from candidate-invalid replay outcomes;
2. cohort/freeze evidence uses shared exact-file integrity validation;
3. checkpoint semantic identity excludes mutable whole-source extent while retaining provenance on the record;
4. sell capacity enforces actual base-quantity venue limits in the book-walk/bisection path;
5. explicit-capital qualification is separate append-only evidence rather than checkpoint mutation;
6. the intentional `qap.experiment.prospective_scanner_adapter -> qap.scanner` edge is narrowly represented in the architecture gate while the broader financial-core prohibition remains intact.

The subsequent seven-finding review against `746af5c` is closed in `809431c`:

1. Gate `tradable` metadata is compared after canonical normalization as `TRADABLE`, so legitimate Gate markets can satisfy the two-way gate;
2. cohort advance clamps `through` per freeze, so mixed-resolution members mature at their own canonical endpoints and already-finalized members remain idempotent;
3. checkpoint semantic identity covers the exact QAP replay prefix, and same-cutoff reuse rejects changed information state;
4. qualification has an explicit independent `as_of`, obtains current candidate state through ordinary QAP at that timestamp, and excludes later capture observations from the same causal claim;
5. live capture no longer exposes operator-controlled `--observed-at` research timestamps;
6. immutable cohort authority remains sealed while checkpoint/outcome indexes are derived and recoverable after interruption;
7. headline cohort economics summarize automatic scanner selections only, with manual-only and all-selection results separately labeled.

## Repository completion gate

The exact `809431c` source/test state was verified with the required repository gates:

```text
uv run pytest -q
631 passed, 1 skipped in 164.59s

uv run ruff check .
All checks passed!

uv run ruff format --check .
315 files already formatted

uv run pyright src tests scripts
0 errors, 0 warnings, 0 informations

uv run python scripts/check_source_size.py
source-size: ok (19 review warnings; no >700-line hard failure)

uv run lint-imports
8 contracts kept, 0 broken

git diff --check
passed
```

The source-size warnings remain review tripwires only. No current hand-written file exceeds the repository hard limit.

## Research limitations

Slice 2 establishes trustworthy prospective/current evidence machinery; it does not prove scanner alpha. A zero-survivor or all-failed prospective cohort is valid evidence.

Public microstructure capture is current/forward evidence only and does not retroactively certify historical execution capacity. `research_only`, `small_capacity`, and `tradable_now` are timestamp- and hypothetical-capital-specific classifications, not permanent asset labels.

The scoreboard intentionally does not sum overlapping candidate terminal wealth into a scanner portfolio return. One combined inventory/basket authority remains Slice 3 and requires a separately approved design and implementation plan.

Reserved final OOS remains sealed and is not consumed by scanner discovery or prospective research evidence.