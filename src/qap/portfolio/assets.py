"""Stable project-level asset identity."""

from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class AssetId:
    """A stable QAP asset key, independent of venue symbol conventions."""

    key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", self._normalized_key(self.key))

    @staticmethod
    def _normalized_key(key: object) -> str:
        if not isinstance(key, str):
            raise TypeError("asset key must be a string")

        normalized = key.strip().upper()
        if not normalized:
            raise ValueError("asset key must not be empty")
        if "/" in normalized:
            raise ValueError("asset key must not contain '/'")
        return normalized
