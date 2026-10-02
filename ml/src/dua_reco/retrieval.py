"""Retrieval models M1-M4 and the context-aware ranker.

M1  TF-IDF + cosine                      lexical baseline
M2  SBERT + cosine                       semantic baseline
M3  M1 + M2 fusion                       hybrid
M4  M3 + structured context dimensions   proposed model

M1 and M2 are deliberately independent so the fusion gain is attributable.
The structured context features are only available to M4, and the dua embedding
text excludes context labels (see Dua.retrieval_text), so the M2 -> M4 delta
isolates the contribution of the context dimensions.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .config import Settings, settings as default_settings
from .context import ContextExtractor, ExtractedContext, weighted_context_score
from .data import Corpus, Dua, load_corpus
from .embeddings import Encoder, build_or_load_corpus_matrix

log = logging.getLogger(__name__)

CONTEXT_FEATURES = ("situation", "emotion", "intention", "occasion", "topic")
FEATURE_TO_LABEL_SET = {
    "situation": "situations",
    "emotion": "emotions",
    "intention": "intentions",
    "occasion": "occasions",
    "topic": "topics",
}


@dataclass
class Scored:
    """One ranked candidate with its full score breakdown, kept for explainability."""

    dua: Dua
    final: float
    components: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "dua_id": self.dua.dua_id,
            "title": self.dua.title,
            "arabic": self.dua.arabic,
            "translation": self.dua.translation,
            "source_work": self.dua.source_work,
            "source_reference": self.dua.source_reference,
            "hadith_reference": self.dua.hadith_reference,
            "reference_status": self.dua.reference_status,
            "review_states": self.dua.review_states,
            "recitation_count": self.dua.recitation_count,
            "final_score": round(self.final, 6),
            "components": {k: round(v, 6) for k, v in self.components.items()},
            "labels": {
                "situations": sorted(self.dua.situations),
                "emotions": sorted(self.dua.emotions),
                "intentions": sorted(self.dua.intentions),
                "occasions": sorted(self.dua.occasions),
                "topics": sorted(self.dua.topics),
            },
        }


class Recommender:
    """Holds the fitted index and serves rankings for every model configuration."""

    def __init__(self, corpus: Corpus | None = None, encoder: Encoder | None = None, cfg: Settings | None = None):
        self.cfg = cfg or default_settings
        self.corpus = corpus if corpus is not None else load_corpus(self.cfg)
        self.encoder = encoder if encoder is not None else Encoder(self.cfg)
        self.duas = list(self.corpus.duas)

        texts = [d.retrieval_text for d in self.duas]
        self.embedding_matrix = build_or_load_corpus_matrix(self.encoder, texts)

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        log.info("index built: %d duas, tfidf %s", len(self.duas), self.tfidf_matrix.shape)

        self.extractor = ContextExtractor(self.encoder, self.cfg)
        self.weights = dict(self.cfg.initial_weights)
        # M3 is tuned separately from M4 so each baseline is shown at its own best.
        self.m3_weights = {"semantic": self.cfg.initial_weights["semantic"],
                           "lexical": self.cfg.initial_weights["lexical"]}
        self._query_cache: dict[str, np.ndarray] = {}
        self.tuned_weights: dict[str, float] | None = None
        if self.cfg.use_tuned_weights:
            self.tuned_weights = self._load_tuned_weights()
            if self.tuned_weights:
                self.weights = dict(self.tuned_weights)
                if "m3_weights" in self.tuned_weights:
                    self.m3_weights = {
                        "semantic": self.tuned_weights["m3_semantic"],
                        "lexical": self.tuned_weights["m3_lexical"],
                    }
                log.info("using tuned weights: %s", self.tuned_weights)

    def _load_tuned_weights(self) -> dict[str, float] | None:
        path = self.cfg.artifacts_dir / "tuning.json"
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            weights = {k: float(v) for k, v in payload["weights"].items()}
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            log.warning("ignoring unreadable tuning file %s: %s", path, exc)
            return None
        if payload.get("embedding_model") != self.encoder.model_name:
            log.warning("tuning file was produced with a different embedding model; ignoring")
            return None
        return weights

    # -- raw signals --------------------------------------------------------
    def semantic_scores(self, query_text: str) -> np.ndarray:
        # Cached because weight tuning re-scores the same queries thousands of times;
        # without this, coordinate ascent is dominated by redundant encoder calls.
        vector = self._query_cache.get(query_text)
        if vector is None:
            vector = self.encoder.encode([query_text])[0]
            self._query_cache[query_text] = vector
        return self.embedding_matrix @ vector

    def lexical_scores(self, query_text: str) -> np.ndarray:
        vector = self.vectorizer.transform([query_text])
        return np.asarray(cosine_similarity(vector, self.tfidf_matrix)[0]).ravel()

    def extract_context(self, query_text: str, occasion: str | None = None) -> ExtractedContext:
        return self.extractor.extract(query_text, occasion)

    # -- models -------------------------------------------------------------
    def rank_m1(self, query_text: str, k: int, **_: object) -> list[Scored]:
        scores = self.lexical_scores(query_text)
        order = np.argsort(-scores)[:k]
        return [
            Scored(self.duas[i], float(scores[i]), {"lexical": float(scores[i])})
            for i in order
            if scores[i] > 0
        ]

    def rank_m2(self, query_text: str, k: int, **_: object) -> list[Scored]:
        scores = self.semantic_scores(query_text)
        order = np.argsort(-scores)[:k]
        return [
            Scored(self.duas[i], float(scores[i]), {"semantic": float(scores[i])})
            for i in order
        ]

    def rank_m3(self, query_text: str, k: int, **_: object) -> list[Scored]:
        """Controlled hybrid: retrieval only, no context features.

        M3 is tuned on its own two weights. Reusing M4's weights here would let the
        context-aware tuner zero out lexical scoring and quietly reduce M3 to M2,
        which would understate the baseline and inflate M4's apparent gain.
        """
        if self.cfg.fusion == "rrf":
            return self._rrf(query_text, k)
        weights = self.m3_weights
        semantic = self.semantic_scores(query_text)
        lexical = self.lexical_scores(query_text)
        pool = min(self.cfg.candidate_pool, len(self.duas))
        candidates = np.argsort(-(weights["semantic"] * semantic + weights["lexical"] * lexical))[:pool]

        semantic_max = semantic[candidates].max() or 1.0
        lexical_max = lexical[candidates].max() or 1.0
        results = []
        for i in candidates:
            components = {
                "semantic": float(weights["semantic"] * semantic[i] / semantic_max),
                "lexical": float(weights["lexical"] * lexical[i] / lexical_max),
            }
            results.append(Scored(self.duas[i], float(sum(components.values())), components))
        results.sort(key=lambda s: -s.final)
        return results[:k]

    def rank_m4(
        self,
        query_text: str,
        k: int,
        occasion: str | None = None,
        favourites: frozenset[str] = frozenset(),
        exclude_ids: frozenset[str] = frozenset(),
        context: ExtractedContext | None = None,
        **_object: object,
    ) -> tuple[list[Scored], ExtractedContext]:
        weights = self.weights
        context = context or self.extract_context(query_text, occasion)
        query_labels = {name: context.get(FEATURE_TO_LABEL_SET[name]) for name in CONTEXT_FEATURES}

        semantic = self.semantic_scores(query_text)
        lexical = self.lexical_scores(query_text)
        base = weights["semantic"] * semantic + weights["lexical"] * lexical
        pool = min(self.cfg.candidate_pool, len(self.duas))
        candidates = np.argsort(-base)[:pool]
        candidates = [i for i in candidates if self.duas[i].dua_id not in exclude_ids]
        if not candidates:
            candidates = list(range(len(self.duas)))

        semantic_ref = max(semantic[candidates].max(), 1e-9)
        lexical_ref = max(lexical[candidates].max(), 1e-9)

        results: list[Scored] = []
        for i in candidates:
            dua = self.duas[i]
            components: dict[str, float] = {
                "semantic": float(weights["semantic"] * semantic[i] / semantic_ref),
                "lexical": float(weights["lexical"] * lexical[i] / lexical_ref),
            }
            total = sum(components.values())
            for name in CONTEXT_FEATURES:
                label_set = FEATURE_TO_LABEL_SET[name]
                raw = weighted_context_score(
                    query_labels[name], context.scores.get(label_set, {}), getattr(dua, label_set)
                )
                weighted = weights[name] * raw
                components[name] = float(weighted)
                total += weighted
            preference = weights.get("preference", 0.0) * (1.0 if dua.dua_id in favourites else 0.0)
            components["preference"] = float(preference)
            total += preference
            results.append(Scored(dua, float(total), components))

        results.sort(key=lambda s: (-s.final, s.dua.dua_id))
        return results[:k], context

    def _rrf(self, query_text: str, k: int) -> list[Scored]:
        """Reciprocal rank fusion - weight-free alternative to weighted scoring."""
        kk = self.cfg.rrf_k
        semantic_order = np.argsort(-self.semantic_scores(query_text))
        lexical_order = np.argsort(-self.lexical_scores(query_text))
        pool = min(self.cfg.candidate_pool, len(self.duas))

        fused: dict[int, float] = {}
        for rank, idx in enumerate(semantic_order[:pool], start=1):
            fused[int(idx)] = fused.get(int(idx), 0.0) + 1.0 / (kk + rank)
        for rank, idx in enumerate(lexical_order[:pool], start=1):
            fused[int(idx)] = fused.get(int(idx), 0.0) + 1.0 / (kk + rank)

        ranked = sorted(fused.items(), key=lambda pair: -pair[1])[:k]
        return [Scored(self.duas[i], score, {"rrf": score}) for i, score in ranked]

    # -- dispatch -----------------------------------------------------------
    def rank(self, model: str, query_text: str, k: int, **kwargs) -> list[Scored]:
        if model == "M1":
            return self.rank_m1(query_text, k)
        if model == "M2":
            return self.rank_m2(query_text, k)
        if model == "M3":
            return self.rank_m3(query_text, k)
        if model == "M4":
            return self.rank_m4(query_text, k, **kwargs)[0]
        raise ValueError(f"unknown model {model!r}; expected M1, M2, M3 or M4")

    def recommend(self, query_text: str, k: int, **kwargs) -> tuple[list[Scored], ExtractedContext]:
        return self.rank_m4(query_text, k, **kwargs)