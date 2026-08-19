"""Versioned Product current-approved research claim and scanner policy."""

import json
from dataclasses import replace
from hashlib import sha256

from qap.scanner.current_scope import CURRENT_APPROVED_UNIVERSE_POLICY_VERSION
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerProtocol, protocol_identity

CURRENT_APPROVED_RESEARCH_CLAIM_ID = "product-current-approved-market-research-v1"
CURRENT_APPROVED_RESEARCH_CLAIM_LABEL = (
    "Current Approved Market Research (current-survivor retrospective)"
)
CURRENT_APPROVED_SCANNER_PROTOCOL = replace(
    SCANNER_V1_SLICE1,
    protocol_id="product-current-approved-scanner-v1",
    universe_policy_version=CURRENT_APPROVED_UNIVERSE_POLICY_VERSION,
)


def semantic_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def current_approved_claim_identity() -> str:
    return semantic_hash(
        {
            "claim_id": CURRENT_APPROVED_RESEARCH_CLAIM_ID,
            "claim_label": CURRENT_APPROVED_RESEARCH_CLAIM_LABEL,
            "universe_policy_version": CURRENT_APPROVED_UNIVERSE_POLICY_VERSION,
            "scanner_protocol_id": CURRENT_APPROVED_SCANNER_PROTOCOL.protocol_id,
            "scanner_protocol_identity": protocol_identity(
                CURRENT_APPROVED_SCANNER_PROTOCOL
            ),
        }
    )


def current_approved_scanner_protocol(venues: tuple[str, ...]) -> ScannerProtocol:
    selected = set(venues)
    ordered = tuple(venue for venue in SCANNER_V1_SLICE1.venues if venue in selected)
    if not ordered:
        ordered = CURRENT_APPROVED_SCANNER_PROTOCOL.venues
    return replace(CURRENT_APPROVED_SCANNER_PROTOCOL, venues=ordered)


__all__ = [
    "CURRENT_APPROVED_RESEARCH_CLAIM_ID",
    "CURRENT_APPROVED_RESEARCH_CLAIM_LABEL",
    "CURRENT_APPROVED_SCANNER_PROTOCOL",
    "current_approved_claim_identity",
    "current_approved_scanner_protocol",
    "semantic_hash",
]
