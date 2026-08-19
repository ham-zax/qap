"""Linux process identity helpers for local runtime ownership."""

from pathlib import Path


def process_start_marker(pid: int) -> str | None:
    """Return Linux process start ticks, avoiding PID-only liveness checks."""

    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    closing = raw.rfind(")")
    if closing < 0:
        return None
    fields = raw[closing + 2 :].split()
    if len(fields) <= 19:
        return None
    marker = fields[19].strip()
    return marker or None


__all__ = ["process_start_marker"]
