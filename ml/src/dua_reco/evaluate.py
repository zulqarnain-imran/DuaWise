"""Evaluation: ranking metrics, splits, significance tests, error analysis."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from .data import Query

# Queries flagged ambiguous have several defensible answer sets, so scoring them
# against one gold set penalises correct systems. They are reported separately.
Ranker = Callable[[str, int], Sequence[str]]


def dcg(gains: Sequence[float]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(ranked_ids: Sequence[str], gold: dict[str, int], k: int) -> float:
    if not gold:
        return 0.0
    gains = [gold.get(rid, 0) for rid in ranked_ids[:k]]
    ideal = sorted(gold.values(), reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    return dcg(gains) / ideal_dcg if ideal_dcg > 0 else 0.0


def precision_at_k(ranked_ids: Sequence[str], gold: dict[str, int], k: int, threshold: int = 1) -> float:
    if not ranked_ids[:k]:
        return 0.0
    hits = sum(1 for rid in ranked_ids[:k] if gold.get(rid, 0) >= threshold)
    return hits / min(k, len(ranked_ids))


def recall_at_k(ranked_ids: Sequence[str], gold: dict[str, int], k: int, threshold: int = 1) -> float:
    relevant = {rid for rid, grade in gold.items() if grade >= threshold}
    if not relevant:
        return 0.0
    hits = sum(1 for rid in ranked_ids[:k] if rid in relevant)
    return hits / len(relevant)


def hit_at_k(ranked_ids: Sequence[str], gold: dict[str, int], k: int, threshold: int = 1) -> float:
    return 1.0 if any(gold.get(rid, 0) >= threshold for rid in ranked_ids[:k]) else 0.0


def mrr(ranked_ids: Sequence[str], gold: dict[str, int], threshold: int = 1) -> float:
    for position, rid in enumerate(ranked_ids, start=1):
        if gold.get(rid, 0) >= threshold:
            return 1.0 / position
    return 0.0


@dataclass
class QueryResult:
    query_id: str
    ndcg: float
    precision: float
    recall: float
    hit: float
    reciprocal_rank: float
    retrieved: list[str]


def evaluate_query(
    query: Query, ranked_ids: Sequence[str], k: int
) -> QueryResult:
    gold = query.gold_relevance
    return QueryResult(
        query_id=query.query_id,
        ndcg=ndcg_at_k(ranked_ids, gold, k),
        precision=precision_at_k(ranked_ids, gold, k),
        recall=recall_at_k(ranked_ids, gold, k),
        hit=hit_at_k(ranked_ids, gold, k),
        reciprocal_rank=mrr(ranked_ids, gold),
        retrieved=list(ranked_ids),
    )


def evaluate(
    queries: Iterable[Query],
    ranker: Ranker,
    k: int = 5,
    exclude_ambiguous: bool = True,
) -> dict[str, float]:
    selected = [q for q in queries if not (exclude_ambiguous and q.ambiguous)]
    if not selected:
        return {}
    results = [evaluate_query(q, ranker(q.text, k), k) for q in selected]
    count = len(results)

    def mean(attr: str) -> float:
        return sum(getattr(r, attr) for r in results) / count

    return {
        "n": count,
        f"P@{k}": mean("precision"),
        f"R@{k}": mean("recall"),
        "MRR": mean("reciprocal_rank"),
        f"nDCG@{k}": mean("ndcg"),
        f"Hit@{k}": mean("hit"),
    }


def paired_bootstrap(
    a: Sequence[float], b: Sequence[float], iterations: int = 10_000, seed: int = 42
) -> dict[str, float]:
    """Two-sided paired bootstrap on the difference in means.

    Returns the observed difference and a p-value for the null hypothesis that the
    models are equally good.

    The resampling must be done on mean-centered differences. A bootstrap
    distribution of raw differences is centred on the observed mean by
    construction, so comparing |resampled mean| against |observed mean| rejects
    roughly half the time regardless of effect size and reports p ~= 0.5 for even
    overwhelming differences. Centering puts the distribution at the null.
    """
    if len(a) != len(b) or not a:
        raise ValueError("paired_bootstrap requires equal-length non-empty sequences")
    rng = random.Random(seed)
    n = len(a)
    diffs = [x - y for x, y in zip(a, b)]
    observed = sum(diffs) / n
    centered = [d - observed for d in diffs]
    sd = (sum(d * d for d in centered) / (n - 1)) ** 0.5 if n > 1 else 0.0

    count_ge = 0
    for _ in range(iterations):
        total = 0.0
        for _ in range(n):
            total += centered[rng.randrange(n)]
        if abs(total / n) >= abs(observed) - 1e-12:
            count_ge += 1

    # add-one keeps the p-value strictly positive, avoiding p = 0 on huge effects
    p_value = (count_ge + 1) / (iterations + 1)
    return {
        "mean_difference": observed,
        "p_value": p_value,
        "n": n,
        "iterations": iterations,
        "significant_at_0.05": p_value < 0.05,
        "ci95_low": observed - 1.96 * sd / (n**0.5) if n else 0.0,
        "ci95_high": observed + 1.96 * sd / (n**0.5) if n else 0.0,
    }


def wilcoxon_signed_rank(diffs: Sequence[float]) -> dict[str, float]:
    """Normal-approximation Wilcoxon signed-rank test (no ties correction)."""
    nonzero = [d for d in diffs if abs(d) > 1e-12]
    if not nonzero:
        return {"statistic": 0.0, "z": 0.0, "p_value": 1.0, "n": 0}
    order = sorted(range(len(nonzero)), key=lambda i: abs(nonzero[i]))
    ranks = [0.0] * len(nonzero)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and abs(abs(nonzero[order[j + 1]]) - abs(nonzero[order[i]])) < 1e-12:
            j += 1
        average = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    positives = sum(r for r, d in zip(ranks, nonzero) if d > 0)
    n = len(nonzero)
    mean = n * (n + 1) / 4
    sd = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (positives - mean) / sd if sd > 0 else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"statistic": positives, "z": z, "p_value": p, "n": n}


def stratified_split(
    queries: Sequence[Query], validation_fraction: float, seed: int = 42
) -> tuple[list[Query], list[Query]]:
    """Split by seed query so paraphrases of one seed cannot straddle the split.

    Splitting on individual queries would leak: a paraphrase of a validation
    query in the training set inflates every tuned number.
    """
    rng = random.Random(seed)
    by_seed: dict[str, list[Query]] = {}
    for query in queries:
        # "Q020p1" and "Q020" share a seed, so a paraphrase never crosses the split.
        seed_id = query.query_id.partition("p")[0] if query.query_id[-1].isdigit() else query.query_id
        by_seed.setdefault(seed_id, []).append(query)

    seeds = sorted(by_seed)
    rng.shuffle(seeds)
    # Cap the cut so both splits stay non-empty: an extreme fraction must not
    # silently produce an empty training set, which would make tuning meaningless.
    cut = min(max(1, int(round(len(seeds) * validation_fraction))), len(seeds) - 1)
    validation_seeds = set(seeds[:cut])

    train: list[Query] = []
    validation: list[Query] = []
    for seed_id, group in by_seed.items():
        (validation if seed_id in validation_seeds else train).extend(group)
    return train, validation


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0