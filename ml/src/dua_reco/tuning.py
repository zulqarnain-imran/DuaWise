"""Weight tuning by coordinate ascent on the training split.

Deliberately simple and inspectable. The feature set is small, so a full grid is
infeasible and a black-box optimiser would obscure what actually helped.

M3 and M4 are tuned separately. Sharing weights between them lets the
context-aware tuner zero out the lexical term, which collapses M3 into M2 and
makes the M3-vs-M4 comparison meaningless.

Weights are fitted on training queries only; validation is never consulted here.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import Settings, settings as default_settings
from .data import Query
from .evaluate import evaluate
from .retrieval import Recommender

log = logging.getLogger(__name__)

M4_WEIGHTS = ("semantic", "lexical", "situation", "emotion", "intention", "occasion", "topic")
M3_WEIGHTS = ("semantic", "lexical")
GRID = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.45, 0.60)


def objective(recommender: Recommender, queries: list[Query], k: int, model: str = "M4") -> float:
    metrics = evaluate(
        queries,
        lambda text, n: [r.dua.dua_id for r in recommender.rank(model, text, n)],
        k=k,
        exclude_ambiguous=True,
    )
    return metrics.get(f"nDCG@{k}", 0.0)


def _ascend(
    recommender: Recommender,
    train: list[Query],
    k: int,
    names: tuple[str, ...],
    model: str,
    attribute: str,
    rounds: int,
    grid: tuple[float, ...],
) -> tuple[dict[str, float], list[dict]]:
    weights = getattr(recommender, attribute)
    best = objective(recommender, train, k, model)
    history = [{"round": 0, "score": best, "weights": dict(weights)}]
    log.info("%s initial nDCG@%d = %.4f", model, k, best)

    for round_index in range(1, rounds + 1):
        improved = False
        for name in names:
            current = weights[name]
            local_best, local_best_weight = best, current
            for candidate in grid:
                if candidate == current:
                    continue
                weights[name] = candidate
                score = objective(recommender, train, k, model)
                if score > local_best + 1e-6:
                    local_best, local_best_weight = score, candidate
            weights[name] = local_best_weight
            if local_best > best + 1e-6:
                log.info("%s round %d: %s %.2f -> %.2f (nDCG@%d %.4f -> %.4f)",
                         model, round_index, name, current, local_best_weight, k, best, local_best)
                best = local_best
                improved = True
        history.append({"round": round_index, "score": best, "weights": dict(weights)})
        if not improved:
            log.info("%s converged after round %d", model, round_index)
            break
    return weights, history


def coordinate_ascent(
    recommender: Recommender,
    train: list[Query],
    k: int,
    rounds: int = 3,
    grid: tuple[float, ...] = GRID,
) -> tuple[dict[str, float], list[dict]]:
    m3_weights, m3_history = _ascend(
        recommender, train, k, M3_WEIGHTS, "M3", "m3_weights", rounds, grid
    )
    m4_weights, m4_history = _ascend(
        recommender, train, k, M4_WEIGHTS, "M4", "weights", rounds, grid
    )

    # Persist both under one payload, with M3's pair under reserved keys.
    combined = dict(m4_weights)
    combined["m3_weights"] = True
    combined["m3_semantic"] = m3_weights["semantic"]
    combined["m3_lexical"] = m3_weights["lexical"]
    return combined, [{"model": "M3", "history": m3_history}, {"model": "M4", "history": m4_history}]


def save_tuning(
    recommender: Recommender,
    weights: dict[str, float],
    history: list[dict],
    train_metrics: dict,
    validation_metrics: dict,
    path: Path | None = None,
    cfg: Settings | None = None,
) -> Path:
    cfg = cfg or default_settings
    path = path or cfg.artifacts_dir / "tuning.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    def clean(metrics: dict) -> dict:
        return {k: round(v, 6) if isinstance(v, float) else v for k, v in metrics.items()}

    payload = {
        "weights": weights,
        "history": history,
        "m3_weights": recommender.m3_weights,
        "train_metrics": clean(train_metrics),
        "validation_metrics": clean(validation_metrics),
        "embedding_model": recommender.encoder.model_name,
        "fallback_encoder": recommender.encoder.using_fallback,
        "notes": [
            "M3 and M4 are tuned independently on the training split only.",
            "Queries flagged ambiguous are excluded from the objective.",
            "Gold labels are derived from draft annotations, so these metrics "
            "measure internal consistency, not expert agreement.",
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("wrote %s", path)
    return path


__all__ = ["coordinate_ascent", "save_tuning", "objective", "M3_WEIGHTS", "M4_WEIGHTS", "GRID"]
