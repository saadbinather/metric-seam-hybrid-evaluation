
# Metric Seam: Hybrid Evaluation of Scientific Claims

An independent research pilot exploring the boundary between **LLM-based judgment and executable verification**, motivated by [Prof. Alexander Spangher's Metric Seam project](https://www.alexander-spangher.com/wishlist.html).

## Overview

Can deterministic Python verification replace an LLM's numerical judgment without compromising evaluation fidelity?

We investigate this question through scientific claim verification: determining whether evidence in a research paper's body supports a numerical claim made in its abstract.

Our experiment compares a **hybrid evaluator** against a **matched LLM control**. Both receive identical source passages and share the same semantic scope decision. The only intended difference is how numerical equivalence is evaluated:

- **Hybrid:** LLM-based scope assessment + Python numerical verification.
- **Matched LLM control:** Same scope assessment + LLM-based numerical judgment.

Additional LLM-only and code-only baselines provide context.

## Experimental Setup

| Component | Configuration |
|---|---|
| Dataset | PeerRead (ICLR 2017) |
| Development set | 8 claim–evidence pairs |
| Held-out test set | 40 claim–evidence pairs |
| LLM | Llama-3.1-8B-Instruct (Q4_K_M) |
| Inference | Ollama, temperature 0 |
| Verification | Python, unit normalization and numeric comparison |
| Human evaluation | 40 audited cases; 12 independently double-reviewed |
| Labels | Supported / Unsupported / Unresolved |

All evaluation methods were frozen before held-out analysis. The human labels and model predictions were kept separate until annotation reconciliation and adjudication were complete.

## Results

| Method | Verdicts / 40 | Correct / 17 | Incorrect / 17 | Abstained / 17 |
|---|---:|---:|---:|---:|
| Hybrid (Python verifier) | 5 | 4 | 0 | 13 |
| Matched LLM control | 19 | 12 | 1 | 4 |

**Key findings:**

- Replacing the LLM's numerical judgment with Python reduced verdict coverage from **47.5% to 12.5%**.
- In 14 cases, the matched LLM control returned a verdict while the hybrid abstained.
- The methods produced different definite verdicts in one case (paper 512), which human annotators marked unresolved.
- Among human-decidable cases, the hybrid made no observed incorrect definite predictions, but answered only 4 of 17.
- The low overlap in decided cases prevents a reliable claim of improved accuracy.

These findings highlight a trade-off between **conservative executable verification and decision coverage**.

## Human Evaluation

Of the 40 held-out cases:

| Human label | Count |
|---|---:|
| Supported | 14 |
| Unsupported | 3 |
| Unresolved | 23 |

Two reviewers independently assessed a prespecified 12-case subset, agreeing on 11 of 12 cases before adjudication (Cohen's κ = 0.833).

Disagreements were resolved before revealing model predictions.

## Reproducibility

The experiment used a frozen dataset reservation, fixed prompts, deterministic sampling, and logged model responses.

**Model:** `llama3.1:8b-instruct-q4_K_M`

**Model digest:**
`46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`

**Frozen reservation SHA-256:**
`be71cbac318b479b1fda8dde45192254fbe15c750daf3c1bec47091bd0ad2b32`

The evaluation includes executable verification certificates, source-span provenance, and timing records.

See the accompanying reports for methodological details and complete results.

## Reports

- [Full Experimental Results](reports/FINAL_RESULTS.md)
- [Professor-Facing Research Memo](reports/PROFESSOR_RESEARCH_MEMO.pdf)

## Limitations

This is a small-scale exploratory pilot, not a definitive benchmark.

Only 17 of 40 examples received human-decidable labels, and the hybrid returned a verdict on just five examples. Consequently, paired accuracy comparisons are underpowered, and the experiment cannot establish the originally proposed harmful-error threshold.

The findings describe this frozen evaluation and should not be generalized to other datasets, models, or evaluation domains without further experiments.

## Research Context

This pilot was independently conducted in response to **Experiment 2: Hybrid Evaluation** from Prof. Alexander Spangher's [Metric Seam research wishlist](https://www.alexander-spangher.com/wishlist.html).

The broader project investigates which components of preference metrics can be expressed as executable code and which require articulated, model-based judgments.

**Upstream research code:** [alex2awesome/norm-research](https://github.com/alex2awesome/norm-research/tree/main/methods/metric_seam)

This repository represents an independent exploratory contribution and is not an official release of the upstream project.

## Acknowledgment

Research direction inspired by Prof. Alexander Spangher's publicly available Metric Seam project description and accompanying research code.
