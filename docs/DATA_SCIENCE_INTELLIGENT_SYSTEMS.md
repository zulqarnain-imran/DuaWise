# Data Science & Intelligent Systems Design

This project is structured as an applied Data Science and Intelligent Systems (DS&IS) solution. It integrates core DS&IS concepts across data engineering, natural language processing, information retrieval, machine learning, evaluation, and explainability.

## 1. Problem Statement & Intelligent System Design

DuaWise addresses the task: **map a free-text description of a life situation to the most contextually appropriate Dua from a curated corpus, with verifiable citations.** 

As an intelligent system, it is designed with the following principles:
- **Retrieval-first, not generation:** To preserve religious authenticity and prevent hallucination, responses are retrieved from cited sources only.
- **Context-aware reasoning:** Beyond text similarity, the system models structured context (situation, emotion, intention, occasion, topic) to improve relevance.
- **Explainable intelligence:** Each recommendation includes score component breakdowns and matched labels, making the reasoning traceable.
- **Grounded outputs:** Every result includes source work, reference, reference-resolution status, and provenance.

## 2. Data Science Pipeline

### Data acquisition & preparation
- **Curated corpus (`data/corpus.json`):** Structured records containing Arabic text, translation, source work, references, recitation metadata, and multi-label annotations (situations, emotions, intentions, occasions, topics).
- **Controlled vocabulary (`data/ontology.json`):** Taxonomy for situations/occasions used for both UI chips and structured context features.
- **Query set construction:** Scripts (`scripts/build_queryset.py`, `scripts/fetch_corpus.py`, `scripts/build_corpus.py`) transform raw sources into reproducible, versioned datasets.
- **Data provenance & integrity:** Metadata tracks provenance and annotation status. Data licensing constraints are explicitly documented (`docs/LICENSES.md`).

### Feature engineering
- **Retrieval text:** A dedicated `retrieval_text` field (excluding context labels) ensures M2's semantic similarity is not trivially contaminated by the same labels M4 consumes as structured features.
- **Structured context features:** Five orthogonal dimensions (situation, emotion, intention, occasion, topic) enable explicit modeling of user context beyond lexical/semantic overlap.
- **Zero-shot extraction:** `dua_reco.context.ContextExtractor` infers structured labels and confidence scores from free-text queries using the encoder, producing explainable context vectors.

## 3. Models & Intelligent Techniques

| Model | Technique | Type | Purpose |
|---|---|---|---|
| M1 | TF-IDF + cosine similarity | Classical IR (lexical) | Sparse term-matching baseline |
| M2 | SBERT (`paraphrase-multilingual-MiniLM-L12-v2`, 384-dim) + cosine | Dense semantic retrieval | Neural embedding baseline capturing semantic similarity |
| M3 | Weighted linear fusion (M1 + M2) | Hybrid IR | Combines lexical precision and semantic recall; tuned independently to avoid baseline leakage |
| M4 | M3 + structured context dimensions + optional preference bias | Context-aware ranking | Proposed intelligent system model leveraging multi-dimensional context signals |

**Design rationale:** M1 and M2 are independent baselines. M3 is tuned separately from M4 so that adding structured context is isolated as the key delta (M2→M4 tests the contribution of context dimensions).

### Fusion strategies
- **Weighted linear fusion:** Normalized per-candidate component scores with tunable weights for interpretability and explainability.
- **Reciprocal Rank Fusion (RRF):** Weight-free alternative (`fusion=rrf`) for robustness when score distributions differ.

## 4. Efficiency & Scalability Considerations

- **Singleton recommender:** `get_recommender()` uses `@lru_cache(maxsize=1)` in the API to avoid reloading encoder/corpus on each request (expensive cold start).
- **Query embedding caching:** In-memory LRU cache of query embeddings (`_query_cache`) avoids redundant encoder calls during tuning/evaluation and repeated queries.
- **Corpus embedding caching:** `build_or_load_corpus_matrix()` persists embeddings as `.npz` keyed by (model_name + corpus content hash), ensuring one-time computation and reproducibility.
- **Candidate pooling:** Per-query candidate pool reduces computation while preserving top candidates for re-ranking.
- **Batch encoding:** SBERT encoding uses configurable batch sizes for efficient throughput.
- **Local-first architecture:** UI is static/edge-friendly; ranking logic isolated in Python service for clear separation of concerns.

## 5. Evaluation Methodology (Data Science Rigor)

- **Offline evaluation:** nDCG@5 on 42 held-out queries, with tuning bias avoided (held-out split).
- **Ablation studies:** M1–M4 comparisons quantify contribution of each component.
- **Statistical validation:** Paired bootstrap for nDCG differences with 95% confidence intervals and p-values.
- **Reproducibility:** All randomness seeded; cached artifacts keyed by content; regression tests guard against metric bugs (e.g. uncentred paired bootstrap, train-set-empty edge case).
- **Honest reporting:** Results explicitly state statistical significance (M4 vs M2: p=0.080, not significant) and construction bias (labels derived from draft annotations also used as features).

## 6. Explainability & Trustworthiness

- **Feature attribution:** Per-result explanation includes contribution of each component (semantic, lexical, context dimensions, preference).
- **Matched labels:** Explanations surface which query→document label matches drove scoring.
- **Grounding enforcement:** System never generates religious text; always returns citations with reference status.
- **Safety constraints:** Explicit ethics constraints (no guarantees, no rulings, scholar review as launch blocker).
- **Human-in-the-loop readiness:** Draft annotations are clearly flagged; UI surfaces review status.

## 7. System Architecture Mapping to DS&IS

The architecture demonstrates integration of intelligent systems components:
- **Perception/NLU:** Zero-shot extraction of structured context from natural language.
- **Knowledge representation:** Controlled vocabulary (ontology) + structured multi-label annotations.
- **Reasoning/retrieval:** Hybrid semantic+lexical retrieval with context-aware re-ranking.
- **Learning/evaluation:** Weight tuning, ablations, IR metrics, statistical inference.
- **Explanation & interface:** Transparent scoring shown in UI; local-first, privacy-preserving interaction.

## 8. References to Reproducibility

Reproduction pipeline (see main README):
```bash
ml\.venv\Scripts\python.exe scripts\fetch_corpus.py
ml\.venv\Scripts\python.exe scripts\build_corpus.py
ml\.venv\Scripts\python.exe scripts\build_queryset.py
ml\.venv\Scripts\python.exe -m dua_reco.cli index
ml\.venv\Scripts\python.exe -m dua_reco.cli tune
ml\.venv\Scripts\python.exe -m dua_reco.cli evaluate --split validation_heldout
```

All experiments are deterministic given seeds and cached embeddings, supporting scientific reproducibility.
