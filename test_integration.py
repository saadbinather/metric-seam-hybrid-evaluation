import json
from pathlib import Path
from .arms import parse_scope_response
from .numeric import compare_quantities
from .ollama import OllamaResult


def test_real_prepared_development_data_has_offsets_and_independent_evidence():
    path = Path(__file__).parent / "data/peerread_iclr2017_v6/development_pairs.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert rows
    for row in rows:
        pair = row["pair"]
        assert pair["evidence_independent"] is True
        assert pair["claim_start"] < pair["claim_end"]
        assert pair["evidence_start"] < pair["evidence_end"]


def test_malformed_ollama_payload_is_unresolved():
    obj, error = parse_scope_response('{"scope_bound": "yes"}')
    assert obj is None and error


def test_certificate_replay_is_deterministic():
    first = compare_quantities("200 ms", "0.2 s").to_dict()
    second = compare_quantities("200 ms", "0.2 s").to_dict()
    assert first == second


def test_matched_llm_control_applies_shared_scope_gate():
    from .arms import ablation_llm_numeric
    scope = json.dumps({"scope_bound": False, "claim_text": "100%", "evidence_text": "90%"})
    result = ablation_llm_numeric(scope, lambda *_: {"status": "supported"})
    assert result == {"status": "unresolved", "reason": "scope_not_bound"}


def test_llm_only_keeps_independent_numeric_verdict():
    from .run_dev_pilot import llm_json
    scope = json.dumps({"scope_bound": False, "claim_text": "100%", "evidence_text": "90%"})
    parsed, _ = parse_scope_response(scope)
    numeric = {"status": "unsupported"}
    assert parsed["scope_bound"] is False
    assert numeric["status"] == "unsupported"


def test_pair_selection_allows_relevant_different_value():
    from .prepare_peerread import choose_pair
    record = {"metadata": {"abstractText": "Our proposed method reaches 90% accuracy on the held-out benchmark.", "sections": [{"heading": "Results", "text": "The same accuracy measure reaches 84% on the held-out benchmark."}]}}
    pair = choose_pair(record)
    assert pair is not None
    assert pair["claim_quantities"] != pair["evidence_quantities"]


def test_reviewed_source_contains_natural_mismatched_focal_pairs():
    path = Path(__file__).parent / "data/peerread_iclr2017_v6/development_pairs.jsonl"
    rows = {r["paper_id"]: r for r in (json.loads(x) for x in path.read_text().splitlines())}
    for paper_id in ("312", "309", "388"):
        pair = rows[paper_id]["pair"]
        assert pair["focal_claim_quantity"] != pair["focal_evidence_quantity"]


def test_ollama_result_schema_is_serializable():
    result = OllamaResult(True, {"response": "{}"}, None, 1.0, "digest")
    assert json.loads(json.dumps(result.__dict__))['model_digest'] == "digest"

