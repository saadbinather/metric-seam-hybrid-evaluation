# Metric Seam Experiment 2

## Question

Does conservative numerical verification after shared LLM scope binding improve scientific-claim decisions, compared with LLM-only and a matched LLM-numeric control?

## Frozen setup

The 40-paper reservation, prompts, model digest, predictions, certificates, annotations, and provenance are frozen. The four arms are:

- `arm_a_llm_only`: LLM scope binding plus LLM numeric judgment.
- `arm_b_code_only_native`: corrected-verifier code-only secondary comparator.
- `arm_c_hybrid`: LLM scope binding plus deterministic numeric verification.
- `arm_d_llm_numeric`: matched LLM-numeric control using shared scope decisions/source spans.

Model digest: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`.

## Reproduction and tests

From the repository root:

```bash
python3 -m pytest -q tests/test_numeric.py tests/test_integration.py tests/test_data_quality.py
```

Inference is not part of release reproduction. Score calculations use the saved `runs/heldout_frozen/HELDOUT_PREDICTIONS.csv` and `TIMINGS.csv`.

## Results

Hybrid coverage was 5/40 (12.5%) versus 19/40 (47.5%) for matched LLM-numeric control. On 17 human-decidable cases, hybrid had 4 correct, 0 incorrect, and 13 abstentions; the control had 12 correct, 1 incorrect, and 4 abstentions. The primary paired table has 5 both-decided, 0 hybrid-only, 14 control-only, and 21 both-abstained cases. Its 15 output-state disagreements comprise 14 abstention differences and one decided-label difference on human-unresolved paper 512.

See `reports/FINAL_RESULTS.md`, `reports/FINAL_RESULTS.csv`, `reports/PROFESSOR_RESEARCH_MEMO.pdf`, and `annotations/FINAL_ANNOTATIONS_LOCK.json`.

## Repository layout

- `src/` — frozen experiment implementation and runners.
- `tests/` — numeric, integration, and data-quality tests.
- `data/` — dataset manifests, pairs, and source records.
- `runs/` — saved pilot and frozen held-out artifacts.
- `annotations/` — locked labels, reader provenance, and freeze manifests.
- `reports/` — final results, memo, and data-quality report.

## Limitations

There are 23/40 human-unresolved labels, low hybrid coverage, and only four human-decidable jointly decided pairs. The frozen pilot cannot prove or reject the original `<10% harmful-error` hypothesis or establish generalization beyond this reservation.

