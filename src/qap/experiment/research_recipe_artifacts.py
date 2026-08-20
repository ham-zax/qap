"""Immutable family-owned research recipe compilation artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, ValidationError

from qap.experiment.integrity import build_integrity_record, read_and_validate_integrity
from qap.experiment.manifest import ExperimentManifest
from qap.experiment.provenance import canonical_manifest_bytes, manifest_sha256
from qap.experiment.research_recipe import (
    ResearchRecipeCompilationV1,
    ResearchRecipeV1,
)

_RECIPE_ROOT = "research-recipe-families"
_RECIPE_FILE = "recipe.json"
_COMPILATION_FILE = "compilation.json"


class ResearchRecipeArtifactError(RuntimeError):
    """Raised when immutable research-recipe lineage cannot be trusted."""


@dataclass(frozen=True, slots=True)
class StoredResearchRecipeCompilation:
    directory: Path
    recipe: ResearchRecipeV1
    compilation: ResearchRecipeCompilationV1
    manifests: tuple[ExperimentManifest, ...]


def _family_component(research_family_id: str) -> str:
    component = quote(research_family_id, safe="-_.~")
    if not component or component in {".", ".."}:
        raise ResearchRecipeArtifactError("research family ID is not path-safe")
    return component


def _compilation_directory(
    run_root: str | Path,
    research_family_id: str,
    compilation_sha256: str,
) -> Path:
    return (
        Path(run_root).resolve()
        / _RECIPE_ROOT
        / _family_component(research_family_id)
        / "compilations"
        / compilation_sha256
    )


def _manifest_name(position: int) -> str:
    return f"manifest-{position:03d}.json"


def _write_model(path: Path, model: BaseModel) -> None:
    payload = (model.model_dump_json(indent=2) + "\n").encode("utf-8")
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()


def _validate_membership(
    recipe: ResearchRecipeV1,
    compilation: ResearchRecipeCompilationV1,
    manifests: tuple[ExperimentManifest, ...],
) -> None:
    if compilation.recipe_sha256 != recipe.recipe_sha256:
        raise ResearchRecipeArtifactError("compilation recipe hash mismatch")
    if compilation.research_family_id != recipe.research_family_id:
        raise ResearchRecipeArtifactError("compilation research family mismatch")
    if any(
        manifest.research_family_id != recipe.research_family_id
        for manifest in manifests
    ):
        raise ResearchRecipeArtifactError("compiled manifest research family mismatch")
    hashes = tuple(manifest_sha256(manifest) for manifest in manifests)
    if hashes != compilation.ordered_compiled_manifest_sha256:
        raise ResearchRecipeArtifactError("compiled manifest hash ordering mismatch")


def write_research_recipe_compilation(
    *,
    run_root: str | Path,
    recipe: ResearchRecipeV1,
    compilation: ResearchRecipeCompilationV1,
    manifests: tuple[ExperimentManifest, ...],
) -> StoredResearchRecipeCompilation:
    """Persist one immutable recipe/compilation before scientific execution."""

    _validate_membership(recipe, compilation, manifests)
    directory = _compilation_directory(
        run_root,
        recipe.research_family_id,
        compilation.compilation_sha256,
    )
    if directory.exists():
        stored = read_research_recipe_compilation(directory)
        if (
            stored.recipe != recipe
            or stored.compilation != compilation
            or stored.manifests != manifests
        ):
            raise ResearchRecipeArtifactError(
                "immutable compilation identity already has different content"
            )
        return stored

    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir()
    try:
        _write_model(directory / _RECIPE_FILE, recipe)
        _write_model(directory / _COMPILATION_FILE, compilation)
        for position, manifest in enumerate(manifests):
            with (directory / _manifest_name(position)).open("xb") as handle:
                handle.write(canonical_manifest_bytes(manifest) + b"\n")
                handle.flush()
        file_names = (
            _RECIPE_FILE,
            _COMPILATION_FILE,
            *tuple(_manifest_name(position) for position in range(len(manifests))),
        )
        integrity = build_integrity_record(
            directory,
            artifact_id=compilation.compilation_sha256,
            file_names=file_names,
        )
        _write_model(directory / "integrity.json", integrity)
    except OSError as exc:
        raise ResearchRecipeArtifactError(
            "failed to persist immutable research recipe compilation"
        ) from exc
    return read_research_recipe_compilation(directory)


def read_research_recipe_compilation(
    directory: str | Path,
) -> StoredResearchRecipeCompilation:
    root = Path(directory).resolve()
    try:
        compilation = ResearchRecipeCompilationV1.model_validate_json(
            (root / _COMPILATION_FILE).read_text(encoding="utf-8")
        )
        recipe = ResearchRecipeV1.model_validate_json(
            (root / _RECIPE_FILE).read_text(encoding="utf-8")
        )
        manifest_names = tuple(
            _manifest_name(position)
            for position in range(len(compilation.ordered_compiled_manifest_sha256))
        )
        expected_files = frozenset({_RECIPE_FILE, _COMPILATION_FILE, *manifest_names})
        read_and_validate_integrity(
            root,
            artifact_id=compilation.compilation_sha256,
            required_files=expected_files,
            allowed_files=expected_files,
        )
        manifests = tuple(
            ExperimentManifest.model_validate_json(
                (root / name).read_text(encoding="utf-8")
            )
            for name in manifest_names
        )
    except (OSError, ValueError, ValidationError) as exc:
        raise ResearchRecipeArtifactError(
            "research recipe compilation integrity validation failed"
        ) from exc
    if root.name != compilation.compilation_sha256:
        raise ResearchRecipeArtifactError("compilation directory identity mismatch")
    _validate_membership(recipe, compilation, manifests)
    return StoredResearchRecipeCompilation(
        directory=root,
        recipe=recipe,
        compilation=compilation,
        manifests=manifests,
    )


def find_research_recipe_compilation(
    run_root: str | Path,
    compilation_sha256: str,
) -> StoredResearchRecipeCompilation | None:
    root = Path(run_root).resolve() / _RECIPE_ROOT
    matches = tuple(root.glob(f"*/compilations/{compilation_sha256}"))
    if not matches:
        return None
    if len(matches) != 1:
        raise ResearchRecipeArtifactError(
            "compilation hash resolves to multiple research families"
        )
    return read_research_recipe_compilation(matches[0])


def find_research_recipe_compilations_for_manifest(
    run_root: str | Path,
    *,
    research_family_id: str,
    exact_manifest_sha256: str,
) -> tuple[StoredResearchRecipeCompilation, ...]:
    """Return integrity-verified compilations that declare one exact manifest."""

    root = (
        Path(run_root).resolve()
        / _RECIPE_ROOT
        / _family_component(research_family_id)
        / "compilations"
    )
    if not root.is_dir():
        return ()
    matches: list[StoredResearchRecipeCompilation] = []
    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        stored = read_research_recipe_compilation(directory)
        if exact_manifest_sha256 in stored.compilation.ordered_compiled_manifest_sha256:
            matches.append(stored)
    return tuple(matches)


__all__ = [
    "ResearchRecipeArtifactError",
    "StoredResearchRecipeCompilation",
    "find_research_recipe_compilation",
    "find_research_recipe_compilations_for_manifest",
    "read_research_recipe_compilation",
    "write_research_recipe_compilation",
]
