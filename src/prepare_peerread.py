"""Fetch and prepare label-free PeerRead ICLR parsed-paper candidates.

The script uses the public PeerRead GitHub API only for file discovery and
downloads the selected parsed-paper JSON files. It never reads reviews,
acceptance decisions, or stored judge labels. Development and reservation IDs
are selected before pair extraction and are disjoint by construction.
"""
from __future__ import annotations

import argparse, hashlib, json, random, re, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from methods.metric_seam.science_claims_v2.core_corrected import Quantity, extract_quantities, quantity_anchor_terms

API = "https://api.github.com/repos/allenai/PeerRead/contents/data/iclr_2017/train/parsed_pdfs"
RAW = "https://raw.githubusercontent.com/allenai/PeerRead/master/data/iclr_2017/train/parsed_pdfs/{}"
NUM = re.compile(r"(?<![A-Za-z])(?:\d+(?:\.\d+)?|\.\d+)(?:\s*(?:%|ms|s|sec|seconds?|minutes?|min|hours?|h|GB|MB|M|K))?\b", re.I)
WORD = re.compile(r"[A-Za-z]{4,}")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


_ABBREVIATIONS = {"e.g.", "i.e.", "et al.", "fig.", "eq.", "sec.", "vs.", "approx."}
_STOP = {"a", "an", "and", "are", "as", "at", "be", "by", "can", "for", "from", "has", "have", "in", "is", "it", "of", "on", "or", "our", "that", "the", "their", "this", "to", "was", "we", "were", "which", "with"}


def sentence_spans(text):
    """Split prose without terminating inside decimals or known abbreviations."""
    source = text or ""
    start = 0
    for i, ch in enumerate(source):
        if ch not in ".!?": continue
        if ch == "." and i and i + 1 < len(source) and source[i - 1].isdigit() and source[i + 1].isdigit():
            continue
        prefix = source[max(start, i - 8):i + 1].lower()
        if any(prefix.endswith(abbr) for abbr in _ABBREVIATIONS): continue
        j = i + 1
        while j < len(source) and source[j].isspace(): j += 1
        if j < len(source) and source[j].islower() and ch == ".": continue
        raw = source[start:i + 1]
        left = len(raw) - len(raw.lstrip())
        s = raw.strip()
        if len(s.split()) >= 6:
            a = start + left
            yield s, a, a + len(s)
        start = j
    tail = source[start:].strip()
    if len(tail.split()) >= 6:
        a = len(source) - len(source[start:]) + len(source[start:]) - len(source[start:].lstrip())
        yield tail, a, a + len(tail)


def numeric_signature(text):
    return {x.group(0).lower().replace(" ", "") for x in NUM.finditer(text or "")}


def _content_tokens(text):
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text or "") if w.lower() not in _STOP}


_RATIO = re.compile(r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)(?![A-Za-z0-9])")


def _quantities(text):
    """Use the upstream extractor but collapse slash ratios before selection."""
    source = text or ""
    ratios = []
    for m in _RATIO.finditer(source):
        ratios.append(Quantity(m.group(0), float(m.group(1)) / float(m.group(2)), "ratio", m.start(), m.end()))
    base = [q for q in extract_quantities(source)
            if not any(q.start >= r.start and q.end <= r.end for r in ratios)]
    return tuple(sorted(base + ratios, key=lambda q: q.start))


def choose_pair(record, prefer_mismatch=False, mismatch_hint=None):
    abstract = record["metadata"].get("abstractText", "")
    abs_candidates = [(s, a, b) for s, a, b in sentence_spans(abstract) if _quantities(s)]
    body_sections = record["metadata"].get("sections", [])
    body_parts, cursor = [], 0
    for section_index, section in enumerate(body_sections):
        heading = section.get("heading") or ""
        text = section.get("text") or ""
        if not text: continue
        block = (heading + "\n" + text).strip()
        body_parts.append((block, cursor, section_index))
        cursor += len(block) + 2
    abstract_norm = re.sub(r"\s+", " ", abstract).strip().lower()
    fallback = None
    for claim, ca, cb in abs_candidates:
        cquantities = _quantities(claim)
        for block, base, section_index in body_parts:
            block_text = block.split("\n", 1)[-1]
            block_norm = re.sub(r"\s+", " ", block_text).strip().lower()
            if block_norm == abstract_norm or block_norm.startswith(abstract_norm[:200]):
                continue
            for evidence, ea, eb in sentence_spans(block):
                if re.sub(r"\s+", " ", evidence).strip().lower() in abstract_norm:
                    continue
                equantities = _quantities(evidence)
                # Eligibility is semantic/numeric, not equality-based: a
                # relevant evidence sentence with a different value is valid
                # input for the unsupported arm outcome.
                if not equantities: continue
                overlap = _content_tokens(claim) & _content_tokens(evidence)
                if len(overlap) < 2 and not any(len(w) >= 7 for w in overlap):
                    continue
                # Choose one focal quantity only when its local entity anchor
                # is shared. Multi-result sentences are retained only when a
                # unique anchor pair exists; otherwise they are ambiguous.
                candidates = []
                for ci, cq in enumerate(cquantities):
                    ca_terms = set(quantity_anchor_terms(claim, cq))
                    for ei, eq in enumerate(equantities):
                        ea_terms = set(quantity_anchor_terms(evidence, eq))
                        score = len(ca_terms & ea_terms)
                        same_surface = int(cq.raw.lower().replace(" ", "") == eq.raw.lower().replace(" ", ""))
                        if score: candidates.append((score, same_surface, -abs(ci - ei), cq, eq))
                if not candidates: continue
                # Equality is never part of the default ranking. When the
                # reviewed audit explicitly requests a naturally occurring
                # mismatch, mismatch-first is an audit stratification only.
                candidates.sort(key=lambda x: ((int(x[3].raw.lower().replace(" ", "") != x[4].raw.lower().replace(" ", "")) if prefer_mismatch else 0), x[0], x[2]), reverse=True)
                best = candidates[0]
                _, _, _, focal_claim, focal_evidence = best
                result = {"claim_text": claim, "claim_start": ca, "claim_end": cb,
                        "claim_source": "abstract", "evidence_text": evidence,
                        "evidence_start": base + ea, "evidence_end": base + eb,
                        "evidence_source": "body_section", "evidence_independent": True,
                        "evidence_section_index": section_index,
                        "claim_quantities": [cq.raw for cq in cquantities],
                        "evidence_quantities": [eq.raw for eq in equantities],
                        "focal_claim_quantity": focal_claim.raw,
                        "focal_evidence_quantity": focal_evidence.raw,
                        "multi_result": len(cquantities) > 1 or len(equantities) > 1,
                        "semantic_overlap": sorted(overlap)}
                if fallback is None:
                    fallback = result
                if prefer_mismatch and mismatch_hint and mismatch_hint.lower() not in evidence.lower():
                    continue
                if not prefer_mismatch or focal_claim.raw.lower().replace(" ", "") != focal_evidence.raw.lower().replace(" ", ""):
                    return result
    return fallback


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261108)
    ap.add_argument("--development", type=int, default=8)
    ap.add_argument("--reserved", type=int, default=40)
    ap.add_argument("--exclude-id", action="append", default=[])
    args = ap.parse_args()
    raw = args.out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    listing = json.loads(urllib.request.urlopen(API, timeout=60).read())
    names = sorted(x["name"] for x in listing if x["name"].endswith(".json"))
    # Eligibility is established before sampling. Sampling a fixed number of
    # papers and filtering afterward creates an avoidable, seed-dependent
    # shortfall and is not a valid development design.
    records, downloads = {}, []
    scan_order = list(names)
    random.Random(args.seed).shuffle(scan_order)

    def fetch(name):
        path = raw / name
        if not path.exists():
            path.write_bytes(urllib.request.urlopen(RAW.format(name), timeout=120).read())
        return name, path

    with ThreadPoolExecutor(max_workers=16) as pool:
        fetched = list(pool.map(fetch, scan_order))
    for name, path in fetched:
        path = raw / name
        downloads.append({"name": name, "sha256": sha256(path), "bytes": path.stat().st_size})
        records[name] = json.loads(path.read_text(encoding="utf-8"))
    excluded = {str(x) for x in args.exclude_id}
    eligible = [name for name in scan_order
                if name.removesuffix(".pdf.json") not in excluded
                and choose_pair(records[name]) is not None]
    selected = eligible[:args.development + args.reserved]
    dev_names, test_names = selected[:args.development], selected[args.development:]
    dev_pairs, reserved_pairs, shortfall = [], [], []
    for name in selected:
        rec = records[name]
        pair = choose_pair(rec)
        row = {"paper_id": name.removesuffix(".pdf.json"), "source_file": name, "title": rec["metadata"].get("title", ""), "pair": pair}
        if pair is None: shortfall.append(row)
        elif name in dev_names: dev_pairs.append(row)
        else: reserved_pairs.append(row)
    manifest = {"schema": "hybrid-numeric-seam-peerread-v3", "source_api": API, "raw_base": RAW, "venue_split": "iclr_2017/train/parsed_pdfs", "seed": args.seed, "eligibility_before_sampling": True, "numeric_equality_required": False, "excluded_ids": sorted(excluded), "eligible_pool_count": len(eligible), "requested": {"development": args.development, "reserved": args.reserved}, "selected_file_count": len(selected), "downloads": downloads, "labels_loaded": False, "reviews_loaded": False, "acceptance_loaded": False, "selection_order": selected, "shortfall_count": len(shortfall)}
    (args.out / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (args.out / "development_pairs.jsonl").write_text("\n".join(json.dumps(x) for x in dev_pairs) + ("\n" if dev_pairs else ""))
    (args.out / "reserved_pairs.jsonl").write_text("\n".join(json.dumps(x) for x in reserved_pairs) + ("\n" if reserved_pairs else ""))
    (args.out / "shortfall.json").write_text(json.dumps(shortfall, indent=2) + "\n")
    print(json.dumps({"development_pairs": len(dev_pairs), "reserved_pairs": len(reserved_pairs), "shortfall": len(shortfall), "selected": len(selected)}, indent=2))


if __name__ == "__main__": main()

