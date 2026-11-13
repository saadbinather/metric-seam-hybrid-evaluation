# Development data-quality audit

Scope: the eight already-inspected development paper IDs only. No reserved
paper content was opened and no model calls were made during this audit.

## Root causes

1. The old sentence splitter stopped at any period. `3.65` therefore became
   `3.` and the remaining sentence was lost.
2. The old quantity extractor treated `1/25` as two independent quantities,
   `1` and `25`.
3. The old selector accepted numeric overlap without semantic token overlap.
   Years, list indices, and unrelated percentages could therefore select an
   irrelevant body sentence.
4. PeerRead parsed JSON sometimes repeats the abstract as section text. The
   old selector did not reject sentence-level duplicates.
5. Multi-result claims were not assigned a focal relation. The new selector
   records all quantities, chooses one focal quantity using local entity
   anchors and exact-surface tie-breaking, and marks `multi_result`.

Numeric equality is not an eligibility requirement. A candidate needs numeric
content in both passages and semantic relevance; different values remain
eligible for an `unsupported` outcome.

## Before and after

| ID | Before defect | Corrected source-backed pair | Focal relation |
|---|---|---|---|
| 312 | claim/evidence ended at `3.` | claim has `3.65 ... 1.05x`; body has complete `3.65 ... 1.05x` sentence | `1.05x` → `1.05x` |
| 709 | claim stopped at `1.` and evidence duplicated abstract offset | independent section-1 evidence contains complete `1.3 BLEU` sentence | `1.3` → `1.3` |
| 617 | selected unrelated list sentence containing `1`/`1000` | section-1 evidence discusses asynchronous vs synchronous speedup and `1.7x` | `1.7x` → `1.7x` |
| 309 | three claim quantities were partially matched | relevant Labyrinth result sentence; all quantities retained, focal relation selected | `87%` → `87%`; `multi_result=true` |
| 785 | `1/25` decomposed; body duplicated abstract | independent conclusion sentence preserves ratio as one quantity | `1/25` → `1/25` |
| 596 | unrelated Freebase nationality sentence | section-0 contribution sentence discusses IRNs/FB15k and `5.7%` | `5.7%` → `5.7%` |
| 388 | claim stopped at `71.` and evidence duplicated abstract | independent results-section sentence reports DCN and `80.4% F1` | `80.4%` → `80.4%` |
| 552 | valid numeric relation mixed with an unscoped `1-bit` quantity | independent memory-copy result; focal `5,000 timesteps` retained | `5,000` → `5,000` |

Current source offsets and section indices are stored in
`data/peerread_iclr2017_v6/development_pairs.jsonl`. Claim offsets are relative
to the PeerRead `abstractText`; evidence offsets are relative to the
deterministic concatenation of parsed body sections, with the original section
index recorded. Raw source JSON remains under the previously downloaded
development source directory and was not rewritten.

## Regression coverage

`test_data_quality.py` now checks all eight IDs, complete decimal/percentage
claims, ratio preservation, independent evidence, focal quantities, semantic
relevance for the previously unrelated cases, and valid source offsets.

The full focused suite result after regeneration is:

```text
15 passed
```

## Remaining limitations

- The PeerRead parser is OCR/Science-Parse output, so some section boundaries
  and punctuation remain noisy.
- Focal selection for multi-result claims is a deterministic local-anchor rule,
  not a human semantic annotation.
- No model evaluation was rerun after this data-only audit. The existing held-
  out reservation remains sealed and unchanged.

