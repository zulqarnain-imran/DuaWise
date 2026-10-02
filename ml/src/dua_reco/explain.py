"""Human-readable explanations for a recommendation.

A religious-context recommender has to justify itself. Every score shown in the
UI traces back to a named reason here, and the wording avoids claims about
efficacy, rulings, or divine response.
"""

from __future__ import annotations

from .context import ExtractedContext
from .retrieval import CONTEXT_FEATURES, FEATURE_TO_LABEL_SET, Scored

FEATURE_LABELS = {
    "semantic": "Meaning similarity to your words",
    "lexical": "Wording overlap",
    "situation": "Matches the situation you described",
    "emotion": "Matches the feeling you described",
    "intention": "Matches what you are seeking",
    "occasion": "Suitable for this time or occasion",
    "topic": "Topic match",
    "preference": "One of your saved Duas",
    "rrf": "Reciprocal rank fusion",
}


def matched_labels(result: Scored, context: ExtractedContext) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for feature in CONTEXT_FEATURES:
        wanted = context.as_set(FEATURE_TO_LABEL_SET[feature])
        if not wanted:
            continue
        present = getattr(result.dua, FEATURE_TO_LABEL_SET[feature])
        shared = sorted(wanted & present)
        if shared:
            out[FEATURE_LABELS[feature]] = shared
    return out


def explain(result: Scored, context: ExtractedContext, rank: int) -> dict:
    contributing = sorted(
        ((k, v) for k, v in result.components.items() if v > 1e-6),
        key=lambda pair: -pair[1],
    )
    return {
        "rank": rank,
        "dua_id": result.dua.dua_id,
        "title": result.dua.title,
        "final_score": round(result.final, 6),
        "reasons": [
            {"feature": FEATURE_LABELS.get(k, k), "contribution": round(v, 6)} for k, v in contributing
        ],
        "matched_labels": matched_labels(result, context),
        "source": {
            "work": result.dua.source_work,
            "reference": result.dua.source_reference,
            "hadith_reference": result.dua.hadith_reference,
            "reference_status": result.dua.reference_status,
        },
        "review_states": result.dua.review_states,
        "disclaimer": (
            "Suggested for reflection. Verify the wording and reference against the "
            "original source before relying on it."
        ),
    }


def explain_all(results: list[Scored], context: ExtractedContext) -> list[dict]:
    return [explain(r, context, i) for i, r in enumerate(results, start=1)]
