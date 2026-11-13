"""Run the four arms on the available development pairs only."""
from __future__ import annotations
import csv, json, time
from pathlib import Path
from .ollama import OllamaClient
from .arms import parse_scope_response, hybrid, llm_only
from .numeric import verify_bound_quantity
from methods.metric_seam.science_claims_v2 import core_corrected

ROOT = Path(__file__).parent
DATA = ROOT / "data/peerread_iclr2017_v6"
RUN = ROOT / "runs/dev_pilot"

SCOPE_SYSTEM = "You bind an abstract scientific numerical claim to the supplied body evidence. Return JSON only. Do not infer missing facts."
SCOPE_PROMPT = """Decide whether the body passage independently supports the same experimental scope as the abstract claim. Return exactly JSON with scope_bound (boolean), claim_text (string copied from claim), evidence_text (string copied from evidence).\n\nABSTRACT CLAIM:\n{claim}\n\nBODY EVIDENCE:\n{evidence}"""
NUM_SYSTEM = "You are a conservative numerical equivalence judge. Return JSON only. Compare the supplied quantities and their experimental scope; abstain when units or scope are missing/incompatible."
NUM_PROMPT = """Return exactly JSON with status one of supported, unsupported, unresolved and reason string. Determine whether the evidence numerically supports the claim.\nCLAIM: {claim}\nEVIDENCE: {evidence}"""


def llm_json(client, prompt, system):
    r = client.generate(prompt, system=system, schema={"type":"object"})
    if not r.ok: return {"status":"unresolved", "reason":r.error}, r
    raw = (r.payload or {}).get("response", "")
    try: return json.loads(raw), r
    except json.JSONDecodeError as exc: return {"status":"unresolved", "reason":f"malformed:{exc}"}, r


def main():
    RUN.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(x) for x in (DATA / "development_pairs.jsonl").read_text().splitlines() if x.strip()]
    client = OllamaClient(log_path=RUN / "ollama_calls.jsonl")
    out = []
    for row in rows:
        pair = row["pair"]
        full = json.loads((DATA / "raw" / row["source_file"]).read_text())
        abstract = full["metadata"].get("abstractText", "")
        body = "\n\n".join((s.get("heading") or "") + "\n" + (s.get("text") or "") for s in full["metadata"].get("sections", []))
        scope, sr = llm_json(client, SCOPE_PROMPT.format(claim=pair["claim_text"], evidence=pair["evidence_text"]), SCOPE_SYSTEM)
        parsed, parse_error = parse_scope_response(json.dumps(scope))
        scope_bound = bool(parsed and parsed.get("scope_bound"))
        pair_native = core_corrected.verify_document(row["paper_id"], pair["claim_text"], pair["evidence_text"])
        full_native = core_corrected.verify_document(row["paper_id"], abstract, body)
        native_status = pair_native.get("status")
        model_claim = parsed["claim_text"] if parsed else ""
        model_evidence = parsed["evidence_text"] if parsed else ""
        # The prepared source spans are the selected spans. The model's echoed
        # strings are audit material only; truncated echoes must never become
        # new numeric inputs.
        selected_claim = pair["claim_text"]
        selected_evidence = pair["evidence_text"]
        span_binding_ok = model_claim == selected_claim and model_evidence == selected_evidence
        selected_scope = json.dumps({"scope_bound": scope_bound, "claim_text": selected_claim, "evidence_text": selected_evidence})
        hyb = hybrid(selected_scope, lambda *_: True, tolerance=0.0)
        llm_num, nr = llm_json(client, NUM_PROMPT.format(claim=selected_claim, evidence=selected_evidence), NUM_SYSTEM)
        if llm_num.get("status") not in {"supported", "unsupported", "unresolved"}: llm_num = {"status":"unresolved", "reason":"invalid_label"}
        # The matched LLM control must share the hybrid scope gate. Its only
        # permitted difference is the numeric decision mechanism.
        llm_control = llm_num if scope_bound else {"status": "unresolved", "reason": "scope_not_bound"}
        exact = verify_bound_quantity(selected_claim, selected_evidence, scope_bound=scope_bound, tolerance=0.0).to_dict()
        relaxed = verify_bound_quantity(selected_claim, selected_evidence, scope_bound=scope_bound, tolerance=0.005).to_dict()
        out.append({"paper_id": row["paper_id"], "title": row["title"], "claim": pair["claim_text"], "evidence": pair["evidence_text"], "claim_quantities": "; ".join(pair.get("claim_quantities", [])), "selected_claim": selected_claim, "selected_evidence": selected_evidence, "model_echo_claim": model_claim, "model_echo_evidence": model_evidence, "span_binding_ok": span_binding_ok, "claim_start": pair["claim_start"], "claim_end": pair["claim_end"], "evidence_start": pair["evidence_start"], "evidence_end": pair["evidence_end"], "scope_bound": scope_bound, "scope_parse_error": parse_error, "shared_scope_claim": selected_claim, "shared_scope_evidence": selected_evidence, "arm_a_llm_only": llm_num.get("status"), "arm_b_code_only_native": native_status, "arm_b_pair_output": pair_native, "arm_b_full_output": full_native, "arm_c_hybrid": hyb["status"], "arm_c_certificate": hyb["certificate"], "arm_d_llm_numeric": llm_control.get("status"), "arm_d_shared_input": True, "exact_status": exact["status"], "relaxed_0_5pct_status": relaxed["status"], "model_digest": sr.model_digest, "scope_latency_ms": sr.latency_ms, "numeric_latency_ms": nr.latency_ms})
    with (RUN / "DEV_PILOT_RESULTS.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted({k for x in out for k in x}))
        writer.writeheader()
        for x in out: writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k,v in x.items()})
    replay = []
    for x in out:
        cert = x.get("arm_c_certificate")
        replay.append(bool(cert and cert.get("status") == x.get("arm_c_hybrid")))
    (RUN / "certificate_replay.json").write_text(json.dumps({"checked":len(replay), "passed":sum(replay)}, indent=2) + "\n")
    with (RUN / "HUMAN_AUDIT_BLINDED.csv").open("w", newline="") as f:
        fields = ["paper_id", "claim", "evidence", "focal_quantity", "human_verdict", "human_reason"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for x in out:
            writer.writerow({"paper_id": x["paper_id"], "claim": x["claim"], "evidence": x["evidence"], "focal_quantity": "; ".join(x for x in x.get("claim_quantities", "").split("; ") if x), "human_verdict": "", "human_reason": ""})
    print(json.dumps({"development_pairs":len(out), "certificate_replay_passed":sum(replay), "model_digest":client.digest()}, indent=2))


if __name__ == "__main__": main()

