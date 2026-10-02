# Experiment log and results

All numbers below are reproducible from this repository:

```bash
ml\.venv\Scripts\python.exe -m dua_reco.cli index
ml\.venv\Scripts\python.exe -m dua_reco.cli tune
ml\.venv\Scripts\python.exe -m dua_reco.cli evaluate --split validation_heldout
ml\.venv\Scripts\python.exe -m dua_reco.cli evaluate --split all
```

## Setup

| Item | Value |
| --- | --- |
| Corpus | 358 Duas (264 Hisn al-Muslim, 94 Qur'an) |
| Embedding model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384-dim, CPU) |
| Lexical model | TF-IDF, 1-2 grams, sublinear TF, 6,809 features |
| Queries | 180 (60 seeds x 2 genuine paraphrases + seed) |
| Ambiguous queries | 9 excluded from scoring |
| Splits | By seed, so paraphrases never straddle train/validation |
| Tuning | Coordinate ascent, training split only, 7 weights |
| Randomness | Seed 42 |

## Models

- **M1** TF-IDF + cosine.
- **M2** SBERT + cosine.
- **M3** Weighted fusion of M1 and M2 (the controlled hybrid; no context features).
- **M4** M3 + five structured context dimensions (situation, emotion, intention, occasion, topic).

The Dua embedding text deliberately **excludes** context labels (`Dua.retrieval_text`), so the M2 -> M4 delta isolates the context contribution instead of smuggling label information into the baseline.

## Headline result: held-out split (42 queries, no tuning bias)

This is the only table free of tuning bias.

| Model | P@5 | R@5 | MRR | nDCG@5 | Hit@5 |
| --- | --- | --- | --- | --- | --- |
| M1 TF-IDF | 0.137 | 0.038 | 0.239 | **0.128** | 0.286 |
| M2 SBERT | 0.314 | 0.113 | 0.544 | **0.353** | 0.714 |
| M3 Hybrid (tuned) | 0.310 | 0.117 | 0.525 | **0.345** | 0.690 |
| M4 Context-aware | 0.419 | 0.182 | 0.627 | **0.462** | 0.738 |

### Significance (paired, per-query nDCG@5)

| Comparison | Mean diff | 95% CI | Bootstrap p | Wilcoxon p | Verdict |
| --- | --- | --- | --- | --- | --- |
| M4 vs M1 | +0.334 | [0.210, 0.457] | <0.001 | — | **significant** |
| M4 vs M3 | +0.117 | [−0.007, +0.241] | 0.062 | — | not significant |
| M4 vs M2 | +0.108 | [−0.014, +0.231] | 0.080 | 0.092 | **not significant** |

### Tuning

M3 and M4 are tuned independently. An earlier version shared weights, and the
M4 tuner drove `lexical` to 0.0, which reduced M3 to a rescaled M2 (identical
scores) and would have inflated M4's reported gain. M3 is now tuned on its own two
weights and lands at `semantic=0.45, lexical=0.05`.

| | M3 | M4 |
| --- | --- | --- |
| semantic | 0.45 | 0.05 |
| lexical | 0.05 | 0.00 |
| situation | — | 0.30 |
| emotion | — | 0.15 |
| intention | — | 0.30 |
| occasion | — | 0.30 |
| topic | — | 0.05 |

## Honest interpretation

1. **The central claim of the project is not established.** M4 beats the semantic
   baseline by +0.108 nDCG@5, but the 95% confidence interval spans zero and both
   paired tests agree it is indistinguishable from M2 at n=42. The thesis must not
   report M4 as a validated improvement over SBERT until this is resolved.

2. **Where context clearly helps is over retrieval-only methods.** M4's advantage over
   M1 (+0.334 nDCG, p<0.001) is large and robust. M4 vs M3 is borderline (p=0.062).
   The defensible claim is that structured context helps substantially relative to
   lexical retrieval, not that it beats well-tuned semantic retrieval.

3. **Hybrid fusion did not beat the semantic baseline.** M3 (0.345) scored marginally
   below M2 (0.353) even when tuned independently. On a 358-record corpus, adding
   TF-IDF to strong sentence embeddings is at best neutral. Reported as a negative
   result rather than hidden.

4. **The context scorer is doing label matching, not reading.** Weight tuning keeps
   pushing `semantic` down (0.30 -> 0.05) and the structured dimensions up
   (`situation`, `intention`, `occasion` at 0.30 each). The tuner is discovering that
   reproducing the annotation labels scores better than understanding the query,
   which is an artefact of how the gold labels were built.

5. **Two effects inflated the apparent result.** Scoring the full 180-query set after
   tuning on part of it gave M4 nDCG@5 = 0.595 with p<0.001, versus 0.462 and p=0.080
   held out. Any write-up must use the held-out figures.

## Threats to validity

- **Circularity (severe).** Gold relevance is derived by `scripts/build_queryset.py`
  from the same draft context annotations that M4 consumes as features. M4 is advantaged
  by construction; the metric measures internal consistency, not relevance to a human.
  Weight tuning makes this worse by rewarding label memorisation.
- **Unreviewed labels.** All context annotations are `DRAFT_UNREVIEWED`. No Islamic
  scholar has validated the ontology, the annotations, or the relevance judgements.
- **Small held-out sample.** n=42 is underpowered. The observed effect (+0.108) with
  its confidence interval is consistent with anything from a small loss to a
  substantial gain; a much larger evaluation is required.
- **Query origin.** The 60 seeds were authored by the developer, so they reflect one
  person's model of which situations matter.
- **Heavily skewed gold.** Queries about `fear` or `protection_from_harm` have up to 100
  gold records. Those queries are easier and dominate the mean.
- **Context-extraction noise.** The zero-shot classifier sometimes picks a secondary
  label that misleads ranking. For "my father passed away" it returns both
  `death_of_loved_one` and `illness`; weighting labels by extractor confidence
  improved the result but did not eliminate the error.

## Next steps to make the claim defensible

1. Independent scholar relevance labelling of at least 150 queries, blind to the models.
2. Expand the held-out set; re-run significance with the larger sample.
3. Break the circularity: score against expert labels derived independently of the
   annotation ontology M4 uses.
4. Ablate each context dimension to show which of the five carries the signal.
5. Consider a proper learning-to-rank objective instead of coordinate ascent, with
   regularisation to stop weight collapse onto the label dimensions.
