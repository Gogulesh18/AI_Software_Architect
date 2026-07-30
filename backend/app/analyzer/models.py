"""Shared finding/severity types used across the quality/security/performance/SOLID detectors."""

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Finding:
    category: str
    severity: str  # "info" | "low" | "medium" | "high" | "critical"
    file: str
    message: str
    line: int = 0
    symbol: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def findings_to_dicts(findings: list[Finding]) -> list[dict]:
    return [f.to_dict() for f in findings]
