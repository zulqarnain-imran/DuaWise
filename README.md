# DuaWise

A context-aware Dua recommendation engine and web app, built as a final-year
university research project.

Describe a situation in your own words and DuaWise retrieves a Dua from a cited
source, showing the Arabic, the translation, the reference, and which signals
drove the suggestion.

**Status: research prototype.** The engine runs locally. Public deployment is
blocked on data licensing and scholar review â€” see [Licensing](docs/LICENSES.md).

## What it does

- **Free-text search** with zero-shot extraction of situation, emotion, intention
  and occasion from the query.
- **Situation and occasion chips** from a controlled vocabulary, so a user who
  does not want to type can still browse.
- **Grounded output.** Every result carries its source work, reference, and
  reference-resolution status. Nothing is generated.
- **Explainable ranking.** Each card shows the score components that put it there.
- **Local-only history.** Saved Duas live in `localStorage`. No account, no
  analytics, no server-side query storage.

## Architecture

```
apps/web     Next.js 16 PWA (TypeScript, Tailwind) â€” UI only, no ranking logic
ml/src       Python research engine â€” owns all ranking, served over HTTP
data         corpus, controlled vocabulary, evaluation set, artifacts
docs         specification, experiment log, ethics, licensing
scripts      data ingestion and corpus/query-set construction
```

Ranking lives only in Python. The frontend never re-implements scoring, so the
numbers in the UI are the numbers in the thesis.

### Models

| | Approach |
| --- | --- |
| M1 | TF-IDF + cosine |
| M2 | Sentence embeddings (`paraphrase-multilingual-MiniLM-L12-v2`, 384-dim) |
| M3 | Weighted fusion of M1 and M2, tuned independently |
| M4 | M3 plus five structured context dimensions (the proposed model) |

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

All randomness is seeded. Corpus embeddings are cached and keyed by model name and
corpus content.

## Headline result, stated honestly

On 42 held-out queries, free of tuning bias:

| Model | nDCG@5 |
| --- | --- |
| M1 TF-IDF | 0.128 |
| M2 SBERT | 0.353 |
| M3 Hybrid | 0.345 |
| M4 Context-aware | 0.462 |

**M4's advantage over M2 is not statistically significant** (+0.108 nDCG@5,
95% CI [âˆ’0.014, +0.231], p = 0.080). The advantage over lexical retrieval is large
and robust (+0.334, p < 0.001). Hybrid fusion did not beat the semantic baseline.

Evaluation labels are derived from the same draft annotations M4 consumes as
features, which inflates M4 by construction. The full analysis, threats to
validity, and what would be needed to make the claim defensible are in
[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md).

## Testing

```bash
ml\.venv\Scripts\python.exe -m pytest ml\tests -q   # metric correctness
npm run lint --prefix apps/web
npm run typecheck --prefix apps/web
npm run build --prefix apps/web
```

The Python tests include regression tests for two bugs that produced wrong
published numbers: an uncentred paired bootstrap that reported p â‰ˆ 0.5 for any
effect size, and a split that could empty the training set.

## Constraints this project operates under

- Never generates religious text.
- Never guarantees outcomes or issues religious rulings.
- Always shows sources; never presents unreviewed annotation as expert-validated.
- Treats scholar review as a launch blocker, not a nice-to-have.

See [docs/ETHICS.md](docs/ETHICS.md).

## Known limitations

1. Corpus is 358 records, so absolute recall is low by construction.
2. All annotations are unreviewed drafts from one author.
3. The zero-shot context classifier sometimes extracts a secondary label that
   misleads ranking.
4. Upstream Hadith reference strings arrive in Bengali script, untranslated.
5. Two data licences are unresolved.
6. No accounts, no cross-device history, no admin or scholar-review interface.
