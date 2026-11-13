"""Conservative numeric comparison for scientific claim/evidence pairs.

Numbers are compared only after unit normalization and only inside an
explicitly bound quantity. A matching scalar without a compatible quantity
binding is unresolved, never supported.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import re
from typing import Optional


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str
    dimension: str
    canonical_value: float
    start: int
    end: int
    raw: str


@dataclass(frozen=True)
class NumericCertificate:
    status: str
    reason: str
    claim: Optional[dict]
    evidence: Optional[dict]
    tolerance: float
    relative_error: Optional[float]

    def to_dict(self):
        return asdict(self)


_NUM = r"(?:\d+(?:\.\d+)?|\.\d+)(?:\s*[eE][+-]?\d+)?"
_UNIT = {
    "ms": ("time", 1e-3), "millisecond": ("time", 1e-3), "milliseconds": ("time", 1e-3),
    "s": ("time", 1.0), "sec": ("time", 1.0), "second": ("time", 1.0), "seconds": ("time", 1.0),
    "min": ("time", 60.0), "minute": ("time", 60.0), "minutes": ("time", 60.0),
    "h": ("time", 3600.0), "hr": ("time", 3600.0), "hour": ("time", 3600.0), "hours": ("time", 3600.0),
    "%": ("fraction", .01), "percent": ("fraction", .01), "percentage": ("fraction", .01),
    "x": ("ratio", 1.0), "times": ("ratio", 1.0), "fold": ("ratio", 1.0),
    "bit": ("information", 1.0), "bits": ("information", 1.0),
    "layer": ("count", 1.0), "layers": ("count", 1.0),
    "million": ("count", 1_000_000.0), "millions": ("count", 1_000_000.0),
    "billion": ("count", 1_000_000_000.0), "billions": ("count", 1_000_000_000.0),
    "mg": ("mass", 1e-3), "g": ("mass", 1.0), "kg": ("mass", 1e3),
}
_PAT = re.compile(rf"(?P<num>{_NUM})\s*(?P<unit>milliseconds?|ms|seconds?|secs?|s|minutes?|mins?|hours?|hrs?|h|percent(?:age)?|%|times?|fold|x|bits?|layers?|millions?|billions?|mg|kg|g)(?![A-Za-z])", re.I)


def _float(s: str) -> float:
    return float(s.replace(" ", ""))


def extract_quantities(text: str) -> list[Quantity]:
    out = []
    for m in _PAT.finditer(text or ""):
        raw_unit = m.group("unit").lower()
        raw_unit = {"sec": "s", "secs": "s", "mins": "min", "hrs": "h", "time": "times"}.get(raw_unit, raw_unit)
        dim, scale = _UNIT[raw_unit]
        value = _float(m.group("num"))
        out.append(Quantity(value, raw_unit, dim, value * scale, m.start(), m.end(), m.group(0)))
    return out


def compare_quantities(claim: str, evidence: str, *, tolerance: float = 0.0) -> NumericCertificate:
    cq, eq = extract_quantities(claim), extract_quantities(evidence)
    if not cq or not eq:
        return NumericCertificate("unresolved", "missing_numeric_quantity", None, None, tolerance, None)
    if all(q.dimension == "count" and q.unit == "unitless" for q in cq + eq):
        return NumericCertificate("unresolved", "unitless_quantity_ambiguous", asdict(cq[0]), asdict(eq[0]), tolerance, None)
    compatible = [(c, e) for c in cq for e in eq if c.dimension == e.dimension]
    if not compatible:
        return NumericCertificate("unresolved", "incompatible_or_missing_units", asdict(cq[0]), asdict(eq[0]), tolerance, None)
    c, e = min(compatible, key=lambda pair: abs(pair[0].canonical_value - pair[1].canonical_value))
    denom = max(abs(c.canonical_value), 1e-15)
    err = abs(c.canonical_value - e.canonical_value) / denom
    status = "supported" if err <= tolerance else "unsupported"
    return NumericCertificate(status, "within_tolerance" if status == "supported" else "numeric_mismatch", asdict(c), asdict(e), tolerance, err)


def verify_bound_quantity(claim_text: str, evidence_text: str, *, scope_bound: bool, tolerance: float = 0.0) -> NumericCertificate:
    if not scope_bound:
        return NumericCertificate("unresolved", "scope_not_bound", None, None, tolerance, None)
    return compare_quantities(claim_text, evidence_text, tolerance=tolerance)

