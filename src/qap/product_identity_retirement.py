"""Read-only retirement inventory for the contradicted Binance W → BTC data."""

import hashlib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from qap.product_market_data_catalog import load_scanner_catalog
from qap.product_market_data_generation import (
    ProductGenerationReadError,
    provenance_relative_path,
    resolve_immutable_generation,
)
from qap.product_market_data_models import MarketDataGenerationProvenance


class IdentityRetirementPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    catalog_hash: str | None
    generations: tuple[MarketDataGenerationProvenance, ...]
    file_hashes: tuple[tuple[str, str], ...]
    dependencies: tuple[str, ...]

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained_file(root: Path, relative_path: str) -> Path:
    path = root / relative_path
    path.resolve(strict=True).relative_to(root.resolve())
    if path.is_symlink() or not path.is_file():
        raise ValueError("Retirement requires ordinary files within the data root.")
    return path


def preview_retirement(data_root: Path, workspace_root: Path) -> IdentityRetirementPlan:
    catalog_path = data_root / "catalog.json"
    catalog = load_scanner_catalog(data_root) if catalog_path.is_file() else None
    provenances: dict[str, MarketDataGenerationProvenance] = {}
    for path in sorted(
        (data_root / "product-market-data/generations").rglob("*.provenance.json")
    ):
        path.resolve(strict=True).relative_to(data_root.resolve())
        item = MarketDataGenerationProvenance.model_validate_json(path.read_bytes())
        if path != data_root / provenance_relative_path(item.relative_path):
            raise ValueError("Generation provenance path does not match its identity.")
        provenances[item.relative_path] = item
    selected = {
        path
        for path, item in provenances.items()
        if (item.venue, item.venue_symbol, item.base_asset)
        == ("binance", "WUSDT", "BTC")
    }
    # Include descendants: their parent evidence is invalid even if renamed.
    while True:
        descendants = {
            path
            for path, item in provenances.items()
            if item.derivation is not None
            and any(
                parent.relative_path in selected for parent in item.derivation.parents
            )
        }
        expanded = selected | descendants
        if expanded == selected:
            break
        selected = expanded
    if catalog is not None:
        for source in catalog.sources:
            if (source.venue, source.venue_symbol, source.base_asset) == (
                "binance",
                "WUSDT",
                "BTC",
            ) and source.relative_path not in selected:
                raise ValueError(
                    "Contaminated catalog source has no verified provenance."
                )
    generations = tuple(provenances[path] for path in sorted(selected))
    hashes: list[tuple[str, str]] = []
    for item in generations:
        try:
            resolve_immutable_generation(
                data_root,
                dataset_id=item.dataset_id,
                semantic_fingerprint=item.semantic_fingerprint,
            )
        except ProductGenerationReadError as exc:
            raise ValueError(
                "Retirement requires verified generation contents."
            ) from exc
        for relative in (
            item.relative_path,
            provenance_relative_path(item.relative_path),
        ):
            hashes.append((relative, file_hash(contained_file(data_root, relative))))
    identifiers = {
        text
        for item in generations
        for text in (item.dataset_id, item.relative_path, item.semantic_fingerprint)
    }
    dependencies: set[str] = set()
    if identifiers:
        audit_root = workspace_root / "product/identity-retirements"
        for path in sorted(workspace_root.rglob("*")):
            if path.suffix not in {".json", ".jsonl"} or not path.is_file():
                continue
            if path.is_relative_to(audit_root):
                continue
            path.resolve(strict=True).relative_to(workspace_root.resolve())
            text = path.read_text(encoding="utf-8")
            if any(identifier in text for identifier in identifiers):
                dependencies.add(path.relative_to(workspace_root).as_posix())
        if catalog is not None:
            dataset_ids = {item.dataset_id for item in generations}
            for source in catalog.sources:
                if source.relative_path not in selected and (
                    dataset_ids & set(source.direct_pair_dataset_ids)
                ):
                    dependencies.add(f"catalog:{source.dataset_id}")
    return IdentityRetirementPlan(
        catalog_hash=None if catalog is None else file_hash(catalog_path),
        generations=generations,
        file_hashes=tuple(hashes),
        dependencies=tuple(sorted(dependencies)),
    )
