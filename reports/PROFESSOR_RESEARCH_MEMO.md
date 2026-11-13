# Professor-facing memo: Metric Seam Experiment 2

## Question

This experiment tests whether a hybrid numerical-and-scope evaluation seam changes decisions relative to an LLM-only arm and a matched LLM-numeric control, using a frozen 40-paper reservation and no post hoc model tuning. The code-only native arm is a separate secondary comparator.

## Design integrity

The frozen model digest is `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`, and the reservation manifest hash is `be71cbac318b479b1fda8dde45192254fbe15c750daf3c1bec47091bd0ad2b32`. Existing predictions were scored without rerunning models. The first-reader mismatch was repaired by obtaining a genuine label for 336 and excluding 361; original annotation files remain preserved and hashed.

## Main findings

The final human reference set contains 14 supported, 3 unsupported, and 23 unresolved cases. LLM-only covered all 40 cases and achieved 14/17 accuracy on human-decidable cases (82.35%, Wilson 95% CI 58.97–93.81%). Hybrid covered only 5 cases (12.5%) and achieved 4/4 among its decisions, while the matched LLM-numeric control covered 19 cases (47.5%) and achieved 12/13 (92.31%, CI 66.69–98.63%). The separate code-only native arm covered 8 cases (20%) and achieved 8/8.

The primary hybrid/control pairing uses identical scope decisions and source spans. Across all 40 cases, both decided 5, hybrid-only 0, control-only 14, and both abstained 21. The 15 exact output-state disagreements are therefore not 15 conflicting labels: 14 are abstention-versus-decision differences, and only one is a decided-label disagreement (paper 512). Paper 512 was human-labeled unresolved, so it is not a human-reference error. Of the five jointly decided cases, the four human-decidable cases were correct for both; the fifth was unresolved. Thus there were no introduced or repaired errors on human-decidable jointly decided cases. On all 17 human-decidable cases, hybrid had 4 correct, 0 incorrect, and 13 abstentions (4/17 = 23.53% when abstentions count as misses); the matched control had 12 correct, 1 incorrect, and 4 abstentions (12/17 = 70.59%). Coverage, rather than an observed accuracy advantage, drives the difference. On human-unresolved cases, LLM-only made 23 decisions, hybrid made none, and matched LLM-numeric made 19 decisions.

The two readers agreed on 11/12 cases before adjudication (κ=0.833); after resolving paper 469 as supported, locked consensus was 12/12 (κ=1.000). The latter should not be interpreted as independent reliability because it includes the adjudication outcome.

## Interpretation

The strongest defensible conclusion is that the frozen hybrid seam was conservative and low-coverage in this run. When abstentions are counted as misses, it scored 4/17 on human-decidable cases versus 12/17 for the matched LLM-numeric control. The paired sample has only five jointly decided cases and no discordant pairs, so the result does not establish superiority or inferiority beyond this frozen artifact. The original `<10% harmful-error` hypothesis cannot be proven or rejected from this sample.

The experiment is therefore informative about abstention behavior and annotation discipline, not a conclusive ranking of arms. Low coverage, 23/40 unresolved human labels, and the small paired sample prevent proving the original `<10% harmful-error` hypothesis. Future work should prespecify how unresolved human cases are handled and enlarge the reservation before drawing performance conclusions.
