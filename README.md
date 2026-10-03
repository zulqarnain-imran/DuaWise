# DuaWise

A context-aware Dua recommendation engine and web app, built as a personal side project.

Describe a situation in your own words and DuaWise retrieves a Dua from a cited source, showing the Arabic, the translation, the reference, and which signals drove the suggestion.

**Status: research prototype.** The engine runs locally. Public deployment is blocked on data licensing and scholar review — see [Licensing](docs/LICENSES.md).

## What it does

- **Free-text search** with zero-shot extraction of situation, emotion, intention and occasion from the query.
- **Situation and occasion chips** from a controlled vocabulary, so a user who does not want to type can still browse.
- **Grounded output.** Every result carries its source work, reference, and reference-resolution status. Nothing is generated.
- **Explainable ranking.** Each card shows the score components that put it there.
- **Local-only history.** Saved Duas live in `localStorage`. No account, no analytics, no server-side query storage.

## Does this type of system already exist?

This space partially exists, but not in this exact form.

### What already exists

- **Category-based Dua apps** (e.g., Muslim Pro, IslamicFinder, Athan, Dua & Azkar apps) let users browse Duas by theme (morning/evening, illness, travel, etc.). These are taxonomy-driven, not free-text situation-aware.
- **Keyword search on Islamic text sites** (e.g., sunnah.com, islamicfinder.org, dua.org) allow searching Dua/Hadith collections, but ranking is typically lexical/keyword-based with limited semantic understanding of the user's situation.
- **General Islamic NLP research** exists on Quran and Hadith retrieval (Quranic QA, semantic search over Islamic corpora). Semantic search tools exist in research, but they are usually general-purpose retrieval rather than optimized for mapping free-text life situations to Duas.

### What's novel here

- **Free-text situation understanding:** Extracts situation, emotion, intention, and occasion from natural language (zero-shot) and maps them to relevant recommendations.
- **Explicit structured context:** The proposed model (M4) adds five structured context dimensions beyond text similarity—a modeling choice not common in consumer apps.
- **Explainable ranking:** Each result shows its score components rather than a black-box similarity score. Most existing apps offer no explanation of why a Dua was suggested.
- **Grounding-first design:** Every result must carry its source work, reference, reference-resolution status, and the system explicitly never generates religious text.
- **Local-first and privacy-preserving:** No accounts, no analytics, no server-side query storage; history lives entirely in `localStorage`.

**Verdict:** Consumer apps exist in this general space, but a context-aware, explainable, retrieval-grounded Dua recommender with structured context features and published evaluation is uncommon. As implemented, this is a **novel research prototype**, not a derivative of an existing mainstream product.

## Has this type of research already been conducted?

Yes in adjacent areas, but limited and not identical to this work.

### Related research areas

- **Islamic Information Retrieval (IR):** Work exists on Quranic search, Hadith retrieval, and Arabic text retrieval. Datasets and semantic search approaches have been explored academically.
- **Context-aware recommendation:** Context-aware recommenders exist broadly (movies, news, etc.), but applying structured "life situation" context to Dua retrieval is not a heavily studied subdomain.
- **Zero-shot/semantic search on religious texts:** Sentence embeddings (SBERT) have been applied to Islamic corpora in research, but typically for verse similarity/search rather than situation→Dua mapping.

### What makes this research distinctive

- **Task formulation:** Mapping free-text user situations to appropriate Duas with citations is a specific, underexplored IR task.
- **Controlled vocabulary + structured signals:** Combines free-text NLU with a controlled vocabulary for situations/occasions and five structured context dimensions.
- **Explicit ablation (M1–M4):** Systematic comparison of TF-IDF (M1), SBERT (M2), hybrid fusion (M3), and context-aware fusion (M4). Few works in this domain report this level of controlled ablation.
- **Honest statistical reporting:** The evaluation transparently reports that M4's improvement over M2 is not statistically significant (p=0.080), while improvement over lexical retrieval is large and significant—a level of candor uncommon in applied prototypes.
- **Reproducibility focus:** End-to-end pipeline with seeded randomness, cached embeddings keyed by model name and corpus content, regression tests for metric correctness, and documented reproduction steps.

**Verdict:** While core IR techniques (hybrid retrieval, semantic embeddings, context-aware ranking) are well-established, **this specific formulation (situation-aware Dua recommendation with grounded citations, explainable components, and structured context dimensions) has not been extensively studied or published in the same form.** This is original applied research contributing a small, evaluated prototype in an underexplored niche.

## Architecture

```
apps/web     Next.js 16 PWA (TypeScript, Tailwind) — UI only, no ranking logic
ml/src       Python research engine — owns all ranking, served over HTTP
data         corpus, controlled vocabulary, evaluation set, artifacts
docs         specification, experiment log, ethics, licensing
scripts      data ingestion and corpus/query-set construction
```

Ranking lives only in Python. The frontend never re-implements scoring, so the numbers in the UI are the numbers in the thesis.

### Models

| | Approach |
| --- | --- |
| M1 | TF-IDF + cosine (lexical retrieval) |
| M2 | Sentence embeddings (`paraphrase-multilingual-MiniLM-L12-v2`, 384-dim) (semantic retrieval) |
| M3 | Weighted fusion of M1 and M2, tuned independently (hybrid retrieval) |
| M4 | M3 plus five structured context dimensions (the proposed context-aware model) |

## Quick start

Two processes: the Python engine and the web app.

```bash
# 1. Engine (from the repository root)
ml\.venv\Scripts\python.exe -m pip install -e "ml[embeddings]"
ml\.venv\Scripts\python.exe -m uvicorn dua_reco.server:app --port 8000

# 2. Web app
npm install --prefix apps/web
npm run dev --prefix apps/web
```

Then open <http://localhost:3000>.

## Reproducing the research

```bash
ml\.venv\Scripts\python.exe scripts\fetch_corpus.py
ml\.venv\Scripts\python.exe scripts\build_corpus.py
ml\.venv\Scripts\python.exe scripts\build_queryset.py
ml\.venv\Scripts\python.exe -m dua_reco.cli index
ml\.venv\Scripts\python.exe -m dua_reco.cli tune
ml\.venv\Scripts\python.exe -m dua_reco.cli evaluate --split validation_heldout
```

All randomness is seeded. Corpus embeddings are cached and keyed by model name and corpus content.

## Headline results, stated honestly

On 42 held-out queries, free of tuning bias:

| Model            | nDCG@5 |
| --------------   | ------ |
| M1 TF-IDF        | 0.128  |
| M2 SBERT         | 0.353  |
| M3 Hybrid        | 0.345  |
| M4 Context-aware | 0.462  |

**Statistical analysis:**
- **M4 vs M2:** +0.108 nDCG@5, 95% CI [−0.014, +0.231], p = 0.080 (**not statistically significant**)
- **M4 vs M1:** +0.334, p < 0.001 (**large and robust**)
- **M3 vs M2:** Hybrid fusion did not beat the semantic baseline.

**Important caveat:** Evaluation labels are derived from the same draft annotations M4 consumes as features, which inflates M4 by construction. The full analysis, threats to validity, and what would be needed to make the claim defensible are in [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md).

## Testing

```bash
ml\.venv\Scripts\python.exe -m pytest ml\tests -q   # metric correctness
npm run lint --prefix apps/web
npm run typecheck --prefix apps/web
npm run build --prefix apps/web
```

The Python tests include regression tests for two bugs that produced wrong published numbers: an uncentred paired bootstrap that reported p ≈ 0.5 for any effect size, and a split that could empty the training set.

## Constraints this project operates under

- Never generates religious text.
- Never guarantees outcomes or issues religious rulings.
- Always shows sources; never presents unreviewed annotation as expert-validated.
- Treats scholar review as a launch blocker, not a nice-to-have.

See [docs/ETHICS.md](docs/ETHICS.md).

## Known limitations

1. Corpus is 358 records, so absolute recall is low by construction.
2. All annotations are unreviewed drafts from one author.
3. The zero-shot context classifier sometimes extracts a secondary label that misleads ranking.
4. Upstream Hadith reference strings arrive in Bengali script, untranslated.
5. Two data licences are unresolved.
6. No accounts, no cross-device history, no admin or scholar-review interface.

## Data Science & Intelligent Systems (DS&IS) Context

For a detailed mapping of this project to Data Science & Intelligent Systems concepts (pipeline, models, evaluation, explainability, and efficiency), see [docs/DATA_SCIENCE_INTELLIGENT_SYSTEMS.md](docs/DATA_SCIENCE_INTELLIGENT_SYSTEMS.md).

