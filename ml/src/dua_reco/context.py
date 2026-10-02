"""Zero-shot extraction of user context from free text.

Given "I'm worried about how I'll pay rent", produce the labels
situations={financial_difficulty, debt}, emotions={anxiety}, intentions={sustenance}.

Method: embed the query and every ontology term's probe sentence with the same
encoder, then take the highest-similarity terms per label set above a threshold.
This needs no training data, which matters because the annotation set is small
and unreviewed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .config import Settings, settings as default_settings
from .data import LABEL_SETS, load_label_texts
from .embeddings import Encoder


@dataclass
class ExtractedContext:
    labels: dict[str, list[str]] = field(default_factory=dict)
    scores: dict[str, dict[str, float]] = field(default_factory=dict)

    def get(self, label_set: str) -> list[str]:
        return self.labels.get(label_set, [])

    def as_set(self, label_set: str) -> set[str]:
        return set(self.labels.get(label_set, []))

    def to_dict(self) -> dict:
        return {
            "labels": {k: v for k, v in self.labels.items() if v},
            "scores": {
                k: {t: round(s, 4) for t, s in v.items() if t in self.labels.get(k, [])}
                for k, v in self.scores.items()
            },
        }


class ContextExtractor:
    def __init__(self, encoder: Encoder, cfg: Settings | None = None):
        self.encoder = encoder
        self.cfg = cfg or default_settings
        self.probe_texts = load_label_texts(self.cfg)
        self._flat_texts: list[str] = []
        self._flat_index: dict[str, list[tuple[str, str]]] = {}
        for label_set, probes in self.probe_texts.items():
            self._flat_index[label_set] = []
            for term, text in probes.items():
                self._flat_index[label_set].append((term, len(self._flat_texts)))
                self._flat_texts.append(text)
        self._probe_matrix = encoder.encode(self._flat_texts)

    def extract(self, query_text: str, occasion: str | None = None) -> ExtractedContext:
        vector = self.encoder.encode([query_text])[0]
        similarity = self._probe_matrix @ vector

        context = ExtractedContext()
        for label_set, entries in self._flat_index.items():
            ranked = sorted(
                ((term, float(similarity[idx])) for term, idx in entries),
                key=lambda pair: pair[1],
                reverse=True,
            )
            chosen: list[str] = []
            scores: dict[str, float] = {}
            for term, score in ranked[: self.cfg.context_top_k]:
                # A term whose probe has no lexical or semantic purchase on the query
                # is noise, not a weak signal, so it is dropped rather than ranked low.
                if score < self.cfg.context_threshold:
                    continue
                chosen.append(term)
                scores[term] = score
            context.labels[label_set] = chosen
            context.scores[label_set] = scores

        if occasion:
            context.labels.setdefault("occasions", [])
            if occasion not in context.labels["occasions"]:
                context.labels["occasions"] = [occasion]
            context.scores.setdefault("occasions", {})[occasion] = 1.0

        return context


def context_match_score(query_labels: set[str], dua_labels: frozenset[str] | set[str]) -> float:
    """Normalised overlap. A binary flag throws away ranking information."""
    if not query_labels or not dua_labels:
        return 0.0
    intersection = len(query_labels & dua_labels)
    if not intersection:
        return 0.0
    union = len(query_labels | dua_labels)
    return intersection / union if union else 0.0


def weighted_context_score(
    query_labels: list[str], query_scores: dict[str, float], dua_labels: frozenset[str] | set[str]
) -> float:
    """Context overlap where each query label contributes in proportion to its rank.

    The extractor keeps the top few labels, and they are not equally trustworthy.
    For "my father passed away" it returns both ``death_of_loved_one`` and
    ``illness``; treating them as equally important let the illness-tagged Duas
    outrank the grief Duas. Weighting by the extractor's own similarity score makes
    the stronger label dominate while still crediting the secondary one.
    """
    if not query_labels or not dua_labels:
        return 0.0
    contributions = [
        query_scores.get(label, 0.0) for label in query_labels if label in dua_labels
    ]
    if not contributions:
        return 0.0
    # Average rather than sum: adding labels must not inflate the feature past the
    # range of the retrieval scores it is fused with.
    return sum(contributions) / len(query_labels)


def normalise(scores: dict[str, float]) -> dict[str, float]:
    """Min-max normalise a score dict to [0, 1] for interpretable fusion."""
    if not scores:
        return {}
    lo, hi = min(scores.values()), max(scores.values())
    if hi - lo < 1e-9:
        return {k: 1.0 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


__all__ = [
    "ContextExtractor",
    "ExtractedContext",
    "context_match_score",
    "normalise",
    "LABEL_SETS",
    "np",
]