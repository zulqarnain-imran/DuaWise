"""Metric correctness tests.

These guard the research claims: if nDCG or the significance tests are wrong, every
number in docs/EXPERIMENTS.md is wrong. Expected values are hand-computed, not
taken from the implementation.
"""

from __future__ import annotations

import pytest

from dua_reco.data import Query
from dua_reco.evaluate import (
    dcg,
    evaluate,
    hit_at_k,
    mrr,
    ndcg_at_k,
    paired_bootstrap,
    precision_at_k,
    recall_at_k,
    stratified_split,
    wilcoxon_signed_rank,
)


def make_query(query_id: str, gold: dict[str, int], ambiguous: bool = False) -> Query:
    return Query(
        query_id=query_id,
        text="t",
        gold_relevance=gold,
        implied_occasion=None,
        lexical_mismatch=False,
        ambiguous=ambiguous,
        intended_context={},
    )


class TestDCG:
    def test_discount_positions(self):
        # 1/log2(2)=1, 1/log2(3)=0.6309, 1/log2(4)=0.5
        assert dcg([1, 1, 1]) == pytest.approx(1 + 0.63093 + 0.5)

    def test_empty_is_zero(self):
        assert dcg([]) == 0.0


class TestNDCG:
    def test_perfect_ranking_is_one(self):
        gold = {"a": 3, "b": 2, "c": 1}
        assert ndcg_at_k(["a", "b", "c"], gold, 5) == pytest.approx(1.0)

    def test_no_relevant_retrieved_is_zero(self):
        assert ndcg_at_k(["x", "y"], {"a": 3}, 5) == 0.0

    def test_empty_gold_is_zero(self):
        assert ndcg_at_k(["a"], {}, 5) == 0.0

    def test_inverted_ranking_penalised(self):
        gold = {"a": 3, "b": 1}
        assert ndcg_at_k(["a", "b"], gold, 5) > ndcg_at_k(["b", "a"], gold, 5)

    def test_rewards_grading_not_just_hits(self):
        """A grade-3 first is better than a grade-1 first, holding hit count equal."""
        gold = {"a": 3, "b": 1}
        assert ndcg_at_k(["a", "b"], gold, 2) > ndcg_at_k(["b", "a"], gold, 2)

    def test_k_truncation_uses_truncated_ideal(self):
        gold = {"a": 3, "b": 2, "c": 1, "d": 1}
        # Only two positions counted, so ideal_dcg uses the top two grades.
        assert ndcg_at_k(["a", "b"], gold, 2) == pytest.approx(1.0)

    def test_ndcg_bounded(self):
        gold = {"a": 2, "b": 2}
        for ranking in (["a", "b"], ["b", "a"], ["z", "a"]):
            assert 0.0 <= ndcg_at_k(ranking, gold, 5) <= 1.0


class TestPrecisionRecallHitMRR:
    GOLD = {"a": 3, "b": 1, "c": 2}

    def test_precision(self):
        assert precision_at_k(["a", "z", "y", "w", "v"], self.GOLD, 5) == pytest.approx(0.2)
        assert precision_at_k(["a", "b", "z", "y", "w"], self.GOLD, 5) == pytest.approx(0.4)

    def test_precision_divides_by_returned_not_k(self):
        assert precision_at_k(["a"], self.GOLD, 5) == pytest.approx(1.0)

    def test_recall(self):
        assert recall_at_k(["a", "b"], self.GOLD, 5) == pytest.approx(2 / 3)
        assert recall_at_k(["z"], self.GOLD, 5) == 0.0

    def test_hit(self):
        assert hit_at_k(["z", "a"], self.GOLD, 5) == 1.0
        assert hit_at_k(["z", "y"], self.GOLD, 5) == 0.0
        assert hit_at_k(["z", "y"], self.GOLD, 1) == 0.0

    def test_mrr(self):
        assert mrr(["z", "a"], self.GOLD) == pytest.approx(0.5)
        assert mrr(["a", "b"], self.GOLD) == pytest.approx(1.0)
        assert mrr(["z"], self.GOLD) == 0.0

    def test_threshold_respects_grades(self):
        gold = {"a": 1}
        assert hit_at_k(["a"], gold, 5, threshold=1) == 1.0
        assert hit_at_k(["a"], gold, 5, threshold=2) == 0.0


class TestEvaluate:
    def test_excludes_ambiguous(self):
        queries = [
            make_query("Q1", {"a": 3}),
            make_query("Q2", {"a": 3}, ambiguous=True),
        ]
        metrics = evaluate(queries, lambda text, k: ["a"], k=5)
        assert metrics["n"] == 1

    def test_empty_selection_returns_empty(self):
        queries = [make_query("Q1", {"a": 3}, ambiguous=True)]
        assert evaluate(queries, lambda text, k: ["a"], k=5) == {}

    def test_perfect_system_scores_one(self):
        queries = [make_query(f"Q{i}", {"a": 3, "b": 2}) for i in range(4)]
        metrics = evaluate(queries, lambda text, k: ["a", "b"], k=2)
        assert metrics["nDCG@2"] == pytest.approx(1.0)
        assert metrics["P@2"] == pytest.approx(1.0)
        assert metrics["Hit@2"] == pytest.approx(1.0)


class TestPairedBootstrap:
    def test_large_effect_is_significant(self):
        a = [0.70 + 0.001 * i for i in range(60)]
        b = [0.40 + 0.001 * i for i in range(60)]
        result = paired_bootstrap(a, b, iterations=2000)
        assert result["mean_difference"] == pytest.approx(0.30)
        assert result["p_value"] < 0.05
        assert result["significant_at_0.05"] is True

    def test_null_effect_is_not_significant(self):
        """The regression this suite exists for.

        Raw resampling is centred on the observed mean, so an uncentred test returns
        p ~= 0.5 for real effects and p ~= 1.0 here. A correct null must not reject.
        """
        a = [0.50, 0.62, 0.44, 0.71, 0.55, 0.66, 0.48, 0.60] * 8
        b = [0.51, 0.60, 0.46, 0.70, 0.54, 0.67, 0.49, 0.61] * 8
        result = paired_bootstrap(a, b, iterations=2000)
        assert abs(result["mean_difference"]) < 0.01
        assert result["p_value"] > 0.05
        assert result["significant_at_0.05"] is False

    def test_identical_inputs_give_p_one(self):
        a = [0.3, 0.5, 0.7, 0.2, 0.9]
        assert paired_bootstrap(a, a, iterations=1000)["p_value"] == pytest.approx(1.0)

    def test_p_value_never_zero(self):
        a = [1.0] * 50
        b = [0.0] * 50
        assert paired_bootstrap(a, b, iterations=500)["p_value"] > 0.0

    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError):
            paired_bootstrap([1.0, 2.0], [1.0])

    def test_confidence_interval_brackets_mean(self):
        a = [0.8, 0.6, 0.7, 0.9, 0.5] * 6
        b = [0.3, 0.2, 0.4, 0.1, 0.5] * 6
        result = paired_bootstrap(a, b, iterations=1000)
        assert result["ci95_low"] < result["mean_difference"] < result["ci95_high"]


class TestWilcoxon:
    def test_all_positive_differences_is_significant(self):
        result = wilcoxon_signed_rank([0.1] * 30)
        assert result["p_value"] < 0.001
        assert result["n"] == 30

    def test_all_zero_is_neutral(self):
        assert wilcoxon_signed_rank([0.0] * 10)["p_value"] == 1.0

    def test_zeroes_excluded_from_n(self):
        result = wilcoxon_signed_rank([0.2, 0.3, 0.0, 0.0, 0.1])
        assert result["n"] == 3

    def test_symmetric_differences_not_significant(self):
        result = wilcoxon_signed_rank([0.2, -0.2] * 15)
        assert result["p_value"] > 0.05


class TestStratifiedSplit:
    def test_paraphrases_never_straddle_split(self):
        queries = [
            make_query("Q001", {}), make_query("Q001p1", {}), make_query("Q001p2", {}),
            make_query("Q002", {}), make_query("Q002p1", {}), make_query("Q002p2", {}),
        ]
        train, validation = stratified_split(queries, 0.5, seed=42)
        train_seeds = {q.query_id.partition("p")[0] for q in train}
        val_seeds = {q.query_id.partition("p")[0] for q in validation}
        assert not (train_seeds & val_seeds)
        assert len(train) + len(validation) == 6

    def test_split_is_deterministic(self):
        queries = [make_query(f"Q{i:03d}", {}) for i in range(20)]
        first = stratified_split(queries, 0.3, seed=42)
        second = stratified_split(queries, 0.3, seed=42)
        assert [q.query_id for q in first[0]] == [q.query_id for q in second[0]]
        assert [q.query_id for q in first[1]] == [q.query_id for q in second[1]]

    def test_validation_never_empty(self):
        queries = [make_query("Q001", {}), make_query("Q002", {})]
        train, validation = stratified_split(queries, 0.99, seed=1)
        assert validation
        assert train
