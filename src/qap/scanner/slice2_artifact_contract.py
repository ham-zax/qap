"""Frozen Scanner-V1 Slice-2 artifact names from the approved design."""

ARTIFACT_DESIGN_SHA256 = (
    "0817427b8d4950136ea3b5c3bb5fd51f08753ba6449574bb38c8911d2a334ac4"
)

# Approved top-level storage surface.
COHORT_DEFINITION = "cohort.json"
FREEZES_TABLE = "freezes.parquet"
CHECKPOINTS_INDEX = "checkpoints.parquet"
OUTCOMES_INDEX = "outcomes.parquet"

# Internal recoverable per-checkpoint generation artifacts.
CHECKPOINT_TABLE = "checkpoint.parquet"
LIQUIDITY_TABLE = "liquidity.parquet"
QUALIFICATION_TABLE = "qualification.parquet"
MANIFEST = "manifest.json"
CHECKPOINT_DIRECTORY = "checkpoint-generations"

__all__ = [
    "ARTIFACT_DESIGN_SHA256",
    "CHECKPOINT_DIRECTORY",
    "CHECKPOINTS_INDEX",
    "CHECKPOINT_TABLE",
    "COHORT_DEFINITION",
    "FREEZES_TABLE",
    "LIQUIDITY_TABLE",
    "MANIFEST",
    "OUTCOMES_INDEX",
    "QUALIFICATION_TABLE",
]
