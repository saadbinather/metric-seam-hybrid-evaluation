"""Validate frozen reservation and blind annotation files; no model calls."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
ALLOWED={"supported","unsupported","unresolved"}
FIELDS=["paper_id","claim","evidence","focal_quantity","human_verdict","human_reason"]
def sha256(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def read_csv(p):
 with p.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
 e=[]; ids=[r.get("paper_id","") for r in rows]
 if list(rows[0])!=FIELDS if rows else True: e.append("wrong or missing header")
 if any(not x for x in ids): e.append("blank paper_id")
 if len(ids)!=len(set(ids)): e.append("duplicate paper_id")
 for i,r in enumerate(rows,2):
  v=r.get("human_verdict","").strip(); reason=r.get("human_reason","").strip()
  if not r.get("claim","").strip() or not r.get("evidence","").strip(): e.append(f"row {i}: blank source text")
  if v and v not in ALLOWED: e.append(f"row {i}: invalid verdict")
  if v and not reason: e.append(f"row {i}: verdict without reason")
  if reason and not v: e.append(f"row {i}: reason without verdict")
 return rows,e
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(__file__).parent); ap.add_argument("--labels",nargs="*",type=Path); a=ap.parse_args(); r=a.root
 f=json.loads((r/"FREEZE_MANIFEST.json").read_text()); m=r/f["reservation"]; mm=json.loads(m.read_text()); ids=[str(x).removesuffix(".pdf.json") for x in mm["selection_order"]]; dev={json.loads(x)["paper_id"] for x in (r/f["v6_dev_pairs"]).read_text().splitlines()}
 out={"reservation_manifest_hash":sha256(m),"reservation_hash_matches":sha256(m)==f["reservation_manifest_sha256"],"reserved_count":len(ids),"reserved_unique":len(set(ids)),"dev_overlap":sorted(set(ids)&dev),"heldout_model_calls":f.get("heldout_model_calls"),"files":{}}
 for p in a.labels or []:
  rows,e=read_csv(p); out["files"][str(p)]={"rows":len(rows),"sha256":sha256(p),"errors":e}
 print(json.dumps(out,indent=2,sort_keys=True))
 if not out["reservation_hash_matches"] or len(ids)!=40 or len(set(ids))!=40 or out["dev_overlap"] or out["heldout_model_calls"]!=0 or any(x["errors"] for x in out["files"].values()): raise SystemExit(1)
if __name__=="__main__": main()
