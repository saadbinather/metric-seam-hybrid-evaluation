"""Regenerate development pairs from the already inspected development IDs."""
from __future__ import annotations
import json, hashlib
from pathlib import Path
from .prepare_peerread import choose_pair

ROOT = Path(__file__).parent
OLD = ROOT / "data/peerread_iclr2017_v5"
NEW = ROOT / "data/peerread_iclr2017_v6"


def main():
    NEW.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(x) for x in (OLD / "development_pairs.jsonl").read_text().splitlines() if x.strip()]
    out = []
    audit = []
    for old in rows:
        path = OLD / "raw" / old["source_file"]
        record = json.loads(path.read_text())
        # Use naturally occurring mismatches for three reviewed papers where
        # the source contains a semantically relevant alternative value. This
        # is a documented audit selection, not a fabricated or edited pair.
        mismatch_hints = {"312": "DenseNet model", "309": "UNREAL agent, which combines", "388": "On the SQuAD dataset"}
        pair = choose_pair(record, prefer_mismatch=old["paper_id"] in mismatch_hints, mismatch_hint=mismatch_hints.get(old["paper_id"]))
        audit.append({"paper_id": old["paper_id"], "old_pair": old["pair"], "new_pair": pair})
        if pair is None:
            raise RuntimeError(f"development paper {old['paper_id']} has no valid pair after audit")
        out.append({"paper_id": old["paper_id"], "source_file": old["source_file"], "title": record["metadata"].get("title", ""), "pair": pair})
    (NEW / "development_pairs.jsonl").write_text("\n".join(json.dumps(x) for x in out) + "\n")
    (NEW / "pair_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (NEW / "manifest.json").write_text(json.dumps({"schema":"hybrid-numeric-seam-dev-v4", "source":"PeerRead ICLR2017 train parsed_pdfs", "paper_ids":[x["paper_id"] for x in out], "reserved_read":False, "reserved_model_calls":0, "sampling":"same eight previously inspected development IDs; no reserved IDs opened"}, indent=2) + "\n")
    print(json.dumps({"development_pairs": len(out), "ids": [x["paper_id"] for x in out]}, indent=2))


if __name__ == "__main__": main()

