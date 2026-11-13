"""Lock complete reader labels with SHA-256 and agreement metadata."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json
from pathlib import Path
ALLOWED={"supported","unsupported","unresolved"}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 rows=list(csv.DictReader(p.open(newline="",encoding="utf-8"))); ids=[r["paper_id"] for r in rows]
 if len(ids)!=len(set(ids)) or any(r.get("human_verdict") not in ALLOWED or not r.get("human_reason","").strip() for r in rows): raise ValueError(f"incomplete or invalid labels: {p}")
 return {r["paper_id"]:r["human_verdict"] for r in rows}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("reader40",type=Path); ap.add_argument("reader12",type=Path); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args(); x,y=load(a.reader40),load(a.reader12); common=sorted(set(x)&set(y)); agree=sum(x[k]==y[k] for k in common)
 lock={"schema":"hybrid-numeric-seam-annotation-lock-v1","locked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"reader40":{"sha256":digest(a.reader40),"count":len(x)},"reader12":{"sha256":digest(a.reader12),"count":len(y)},"overlap_count":len(common),"agreement_count":agree,"agreement_rate":agree/len(common) if common else None,"heldout_execution_gate":len(x)==40 and len(y)==12 and len(common)==12}
 a.out.write_text(json.dumps(lock,indent=2,sort_keys=True)+"\n"); print(json.dumps(lock,indent=2,sort_keys=True))
if __name__=="__main__": main()
