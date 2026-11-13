import json
from src.numeric import compare_quantities, verify_bound_quantity
from src.arms import parse_scope_response, hybrid


def test_ms_vs_seconds():
    assert compare_quantities("inference time was 200 ms", "latency was 0.2 s").status == "supported"


def test_training_vs_inference_is_not_scope_free():
    assert verify_bound_quantity("inference time was 200 ms", "training time was 0.2 s", scope_bound=False).status == "unresolved"


def test_tolerance_ablation():
    assert compare_quantities("100.0 s", "100.4 s", tolerance=0.0).status == "unsupported"
    assert compare_quantities("100.0 s", "100.4 s", tolerance=0.005).status == "supported"


def test_percent_unit_is_parsed_and_normalized():
    assert compare_quantities("34%", "34 percent").status == "supported"


def test_ratio_and_count_units():
    assert compare_quantities("2x bandwidth", "2 times bandwidth").status == "supported"
    assert compare_quantities("5 bits per parameter", "5 bits per parameter").status == "supported"


def test_missing_and_incompatible_units():
    assert compare_quantities("accuracy was 90", "accuracy was 90 percent").status == "unresolved"
    assert compare_quantities("time was 2 s", "mass was 2 kg").status == "unresolved"


def test_malformed_response_and_certificate_replay():
    assert parse_scope_response("not json")[0] is None
    out = hybrid(json.dumps({"scope_bound": True, "claim_text": "200 ms", "evidence_text": "0.2 s"}), lambda a, b: True)
    assert out["status"] == "supported"
    assert out["certificate"]["relative_error"] == 0.0

