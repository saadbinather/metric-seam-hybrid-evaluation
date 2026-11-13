"""Four auditable evaluation arms; no arm reads outcome labels."""
from __future__ import annotations

import json
from .numeric import verify_bound_quantity


SCOPE_SCHEMA = {"type": "object", "properties": {"scope_bound": {"type": "boolean"}, "claim_text": {"type": "string"}, "evidence_text": {"type": "string"}}, "required": ["scope_bound", "claim_text", "evidence_text"]}


def parse_scope_response(raw: str):
    try:
        obj = json.loads(raw)
        if not isinstance(obj.get("scope_bound"), bool) or not isinstance(obj.get("claim_text"), str) or not isinstance(obj.get("evidence_text"), str):
            raise ValueError("schema mismatch")
        return obj, None
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return None, f"malformed_scope_response: {exc}"


def code_only(claim, evidence, corrected_verifier, tolerance=0.0):
    """Use the frozen corrected verifier as a semantic gate, then numeric check."""
    scope = corrected_verifier(claim, evidence)
    return verify_bound_quantity(claim, evidence, scope_bound=bool(scope), tolerance=tolerance)


def hybrid(scope_json, corrected_verifier, tolerance=0.0):
    parsed, error = parse_scope_response(scope_json)
    if error:
        return {"status": "unresolved", "reason": error, "certificate": None}
    cert = verify_bound_quantity(parsed["claim_text"], parsed["evidence_text"], scope_bound=parsed["scope_bound"], tolerance=tolerance)
    return {"status": cert.status, "reason": cert.reason, "certificate": cert.to_dict()}


def llm_only(scope_json, numeric_judge):
    parsed, error = parse_scope_response(scope_json)
    if error:
        return {"status": "unresolved", "reason": error}
    if not parsed["scope_bound"]:
        return {"status": "unresolved", "reason": "scope_not_bound"}
    verdict = numeric_judge(parsed["claim_text"], parsed["evidence_text"])
    return verdict if verdict.get("status") in {"supported", "unsupported", "unresolved"} else {"status": "unresolved", "reason": "invalid_numeric_judge_label"}


def ablation_llm_numeric(scope_json, numeric_judge):
    return llm_only(scope_json, numeric_judge)

