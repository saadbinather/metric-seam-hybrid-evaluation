# Metric Seam Experiment 2 — final results

## Integrity and label lock

All gates passed. `BLINDED_ADJUDICATION_QUEUE.csv` has paper 469 marked `RESOLVED` with non-empty verdict and reason. The final annotation set contains exactly the 40 frozen reservation IDs: the original reader-1 set with extra ID 361 excluded and genuine ID 336 added. Original reader files were preserved unchanged; final hashes are in `FINAL_ANNOTATIONS_LOCK.json`.

The frozen reservation manifest hash is `be71cbac318b479b1fda8dde45192254fbe15c750daf3c1bec47091bd0ad2b32`. The model digest is `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`. Existing predictions were scored as-is; no model, prompt, method, or prediction was changed.

## Statistical findings

Human labels: 14 supported, 3 unsupported, and 23 unresolved. Human-decidable cases therefore comprise only 17/40 cases. Wilson 95% intervals are reported for accuracy on cases with supported/unsupported labels.

| Arm | Coverage | Abstentions | Decidable n | Accuracy |
|---|---:|---:|---:|---:|
| LLM-only | 40/40 (100.0%) | 0 | 17 | 14/17 = 82.35% [58.97%, 93.81%] |
| Code-only native arm (secondary comparator) | 8/40 (20.0%) | 32 | 8 | 8/8 = 100.00% [67.56%, 100%] |
| Hybrid | 5/40 (12.5%) | 35 | 4 | 4/4 = 100.00% [51.01%, 100%] |
| Matched LLM-numeric control (primary comparator) | 19/40 (47.5%) | 21 | 13 | 12/13 = 92.31% [66.69%, 98.63%] |

## Primary paired analysis: hybrid vs matched LLM-numeric control

The matched control is `arm_d_llm_numeric`, not the code-only native `arm_b_code_only_native` arm. The frozen prediction artifact records shared scope/source-span inputs for all 40 cases (`arm_d_shared_scope=True`). Across all cases: both decided 5; hybrid decided/control abstained 0; control decided/hybrid abstained 14; both abstained 21. There were 15 exact output-state disagreements and 25 exact agreements: 14 disagreements were abstention-versus-decision differences, and only one was a decided-label disagreement (paper 512: hybrid unsupported, control supported). Paper 512 was human-labeled unresolved, so this is not a human-reference error. Among the five jointly decided cases, the four human-decidable cases were correct for both; the fifth was paper 512, unresolved by the human reviewer. Thus there were no introduced or repaired errors on human-decidable jointly decided cases. McNemar's discordant count is 0/4 on human-decidable jointly decided cases, so no paired superiority claim is defensible.

On the 17 human-decidable cases, hybrid had 4 correct, 0 incorrect, and 13 abstentions; counting abstentions as misses gives 4/17 = 23.53% accuracy, with 23.53% decision coverage. The matched LLM-numeric control had 12 correct, 1 incorrect, and 4 abstentions; counting abstentions as misses gives 12/17 = 70.59% accuracy, with 76.47% decision coverage. Substitution introduced/repaired errors are both zero among jointly decided cases; the key difference is coverage, not demonstrated correctness.

On the 23 human-unresolved cases, LLM-only decided all 23 (12 supported, 11 unsupported); code-only abstained on all 23 (12 `abstain`, 11 `insufficient`); hybrid abstained on all 23; matched LLM-numeric decided 19 (17 supported, 2 unsupported) and abstained on 4. These are behavior counts, not accuracy estimates.

Inter-reader agreement on the prespecified 12 IDs was 11/12 before adjudication, with Cohen's kappa 0.8333. After the independent resolution of paper 469, agreement was 12/12 and kappa 1.0000. The post-adjudication figure is a locked-consensus measure, not independent-reader agreement.

Latency totals from the existing timing artifact were 233,817.06 ms scope and 96,660.63 ms numeric; means were 5,845.43 ms and 2,416.52 ms per case respectively. The frozen held-out Ollama call log contains 80 recorded calls. No monetary cost is inferable without a price schedule, so no dollar cost is fabricated.

## Limitations

The 40-case test set is small, with 23/40 unresolved human labels and very low hybrid coverage. Accuracy intervals are consequently wide, and the primary paired comparison has only five jointly decided cases with zero discordant pairs. These data cannot prove or disprove the original `<10% harmful-error` hypothesis. The perfect post-adjudication kappa is partly tautological because the single disagreement was replaced by consensus. Results describe this frozen run only and do not establish generalization beyond the reservation.
