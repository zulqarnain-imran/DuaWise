"""HTTP API for the DuaWise web client.

The Python engine is the research artifact and owns ranking. The Next.js frontend
consumes this service rather than reimplementing scoring in TypeScript, so the
numbers shown in the UI are the numbers in the thesis.

The recommender is a module-level singleton: loading the encoder and the corpus
costs seconds, and a per-request rebuild would make the API unusably slow.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import settings
from .data import load_corpus, load_ontology
from .embeddings import Encoder
from .explain import explain_all
from .retrieval import Recommender

log = logging.getLogger(__name__)

app = FastAPI(
    title="DuaWise Recommendation API",
    version="1.0.0",
    description=(
        "Context-aware Dua recommendation over cited source texts. "
        "Returns sourced religious text only; it does not generate Duas or issue rulings."
    ),
)

# The frontend is served from a different origin in development and from Vercel in
# production. CORS is restricted to an allowlist rather than "*" so a deployed
# instance cannot be used as an open proxy for the model.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://dua-wise.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class RecommendRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=5, ge=1, le=20)
    occasion: str | None = None
    favourites: list[str] = Field(default_factory=list, max_length=50)
    exclude_ids: list[str] = Field(default_factory=list, max_length=50)


DISCLAIMER = (
    "DuaWise surfaces Duas from cited sources for personal reflection. It does not "
    "generate religious text, guarantee an outcome, or issue religious rulings. "
    "Verify wording and attribution against the original source."
)


@lru_cache(maxsize=1)
def get_recommender() -> Recommender:
    log.info("loading recommender (first request pays this cost)")
    recommender = Recommender(encoder=Encoder(settings), cfg=settings)
    log.info("recommender ready with %d duas", len(recommender.duas))
    return recommender


@lru_cache(maxsize=1)
def get_ontology() -> dict[str, Any]:
    return load_ontology(settings)


@app.get("/health")
def health() -> dict[str, Any]:
    recommender = get_recommender()
    return {
        "status": "ok",
        "corpus_size": len(recommender.duas),
        "embedding_model": recommender.encoder.model_name,
        "fallback_encoder": recommender.encoder.using_fallback,
        "weights_tuned": recommender.tuned_weights is not None,
        "annotation_status": recommender.corpus.meta.get("annotation_status"),
    }


def _display(term_id: str) -> str:
    """Human-readable chip label. The ontology stores only stable slugs."""
    return term_id.replace("_", " ").capitalize()


@app.get("/taxonomy")
def taxonomy() -> dict[str, Any]:
    """Situation and occasion chips for the UI, built from the controlled vocabulary."""
    ontology = get_ontology()
    return {
        label_set: [
            {"id": term["term_id"], "label": _display(term["term_id"]), "definition": term["definition"]}
            for term in terms
        ]
        for label_set, terms in ontology.items()
    }


@app.post("/recommend")
def recommend(request: RecommendRequest) -> dict[str, Any]:
    recommender = get_recommender()
    text = request.query.strip()
    if not text:
        raise HTTPException(status_code=422, detail="query must not be blank")

    results, context = recommender.recommend(
        text,
        request.k,
        occasion=request.occasion,
        favourites=frozenset(request.favourites),
        exclude_ids=frozenset(request.exclude_ids),
    )
    return {
        "query": text,
        "extracted_context": context.to_dict(),
        "results": [r.as_dict() for r in results],
        "explanations": explain_all(results, context),
        "disclaimer": DISCLAIMER,
        "provenance": recommender.corpus.meta.get("provenance"),
        "annotation_status": recommender.corpus.meta.get("annotation_status"),
    }


@app.get("/dua/{dua_id:path}")
def get_dua(dua_id: str) -> dict[str, Any]:
    corpus = load_corpus(settings)
    dua = corpus.by_id.get(dua_id)
    if dua is None:
        raise HTTPException(status_code=404, detail=f"unknown dua_id {dua_id!r}")
    return dua.as_dict()


@app.get("/corpus/stats")
def corpus_stats() -> dict[str, Any]:
    corpus = load_corpus(settings)
    by_work: dict[str, int] = {}
    by_reference_status: dict[str, int] = {}
    for dua in corpus.duas:
        by_work[dua.source_work] = by_work.get(dua.source_work, 0) + 1
        by_reference_status[dua.reference_status] = by_reference_status.get(dua.reference_status, 0) + 1
    return {
        "total": len(corpus.duas),
        "by_work": by_work,
        "by_reference_status": by_reference_status,
        "meta": corpus.meta,
    }


__all__ = ["app", "RecommendRequest", "DISCLAIMER"]
