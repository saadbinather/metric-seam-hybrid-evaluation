"""Run frozen four-arm evaluation on reserved pairs only."""
from __future__ import annotations
import csv, json
from pathlib import Path
from .ollama import OllamaClient
from .run_dev_pilot import SCOPE_PROMPT, SCOPE_SYSTEM, NUM_PROMPT, NUM_SYSTEM, llm_json
from .arms import parse_scope_response, hybrid
from .numeric import verify_bound_quantity
from methods.metric_seam.science_claims_v2 import core_corrected

ROOT = Path(__file__).parent
DATA = ROOT / "data/peerread_iclr2017_v7_a"
RUN = ROOT / "runs/heldout_frozen"

def main():
    RUN.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(x) for x in (DATA / "reserved_pairs.jsonl").read_text().splitlines() if x.strip()]
    client = OllamaClient(log_path=RUN / "ollama_calls.jsonl")
    out = []
    for row in rows:
        pair = row["pair"]
        scope, sr = llm_json(client, SCOPE_PROMPT.format(claim=pair["claim_text"], evidence=pair["evidence_text"]), SCOPE_SYSTEM)
        parsed, parse_error = parse_scope_response(json.dumps(scope))
        bound = bool(parsed and parsed.get("scope_bound"))
        claim, evidence = pair["claim_text"], pair["evidence_text"]
        native = core_corrected.verify_document(row["paper_id"], claim, evidence)
        shared = json.dumps({"scope_bound": bound, "claim_text": claim, "evidence_text": evidence})
        hybrid_out = hybrid(shared, lambda *_: True)
        numeric, nr = llm_json(client, NUM_PROMPT.format(claim=claim, evidence=evidence), NUM_SYSTEM)
        if numeric.get("status") not in {"supported", "unsupported", "unresolved"}:
            numeric = {"status": "unresolved", "reason": "invalid_label"}
        control = numeric if bound else {"status": "unresolved", "reason": "scope_not_bound"}
        out.append({"paper_id": row["paper_id"], "claim": claim, "evidence": evidence,
                    "scope_bound": bound, "scope_parse_error": parse_error,
                    "arm_a_llm_only": numeric.get("status"),
                    "arm_b_code_only_native": native.get("status"), "arm_b_native_output": native,
                    "arm_c_hybrid": hybrid_out["status"], "arm_c_certificate": hybrid_out["certificate"],
                    "arm_d_llm_numeric": control.get("status"), "arm_d_shared_scope": True,
                    "exact_certificate": verify_bound_quantity(claim, evidence, scope_bound=bound, tolerance=0.0).to_dict(),
                    "scope_latency_ms": sr.latency_ms, "numeric_latency_ms": nr.latency_ms,
                    "model_digest": sr.model_digest})
    with (RUN / "HELDOUT_PREDICTIONS.csv").open("w", newline="") as f:
        fields = sorted({k for x in out for k in x}); writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for x in out: writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in x.items()})
    replay = [x["arm_c_certificate"] and x["arm_c_certificate"]["status"] == x["arm_c_hybrid"] for x in out]
    (RUN / "certificate_replay.json").write_text(json.dumps({"checked": len(replay), "passed": sum(replay)}, indent=2) + "\n")
    print(json.dumps({"papers": len(out), "replay_passed": sum(replay), "digest": client.digest(), "predictions": str(RUN / "HELDOUT_PREDICTIONS.csv"), "raw": str(RUN / "ollama_calls.jsonl")}, indent=2))

if __name__ == "__main__":
    main()
