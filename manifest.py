"""Create a provenance-only manifest from user-supplied, already authorized data."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20261107)
    p.add_argument("--development-papers", type=int, default=8)
    p.add_argument("--heldout-papers", type=int, default=40)
    args = p.parse_args()
    if not args.input.exists(): raise SystemExit(f"input does not exist: {args.input}")
    manifest = {"schema": "hybrid-numeric-seam-manifest-v1", "input": str(args.input), "sha256": sha256(args.input), "seed": args.seed, "development_papers": args.development_papers, "heldout_papers": args.heldout_papers, "labels_loaded": False, "judge_scores_loaded": False, "selection": "deterministic sampling must be performed by a separate approved data-preparation step"}
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__": main()

