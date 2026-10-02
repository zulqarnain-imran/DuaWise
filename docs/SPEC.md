# DuaWise — Research & Product Specification v1.0

**Project title (academic):** A Context-Aware Hybrid Recommendation Framework for Grounded Dua Retrieval from Islamic Texts

**Application name:** DuaWise — Intelligent Dua & Islamic Companion

**Level:** Final-year / undergraduate project
**Version:** 1.0
**Date:** 2026-10-03
**Status:** Master specification. Source of truth for all subsequent implementation work.

---

## 0. Document control

| Field | Value |
|---|---|
| Research level | Final-year / university project |
| UI language | English |
| Scripture language | Arabic (source text preserved, never machine-generated) |
| Platform | Web / PWA first, Android via wrapper later |
| Recommendation input | Free text **and** situation chips |
| Accounts | None required. Anonymous ID + local history |
| Scholarly validation | 2+ Islamic scholars (annotation + evaluation) |

**Verification markers used in this document:**

- `[V]` Verified against primary source on 2026-10-03
- `[U]` Unverified — must be confirmed during implementation
- `[A]` Action required

Any claim without `[V]` must not be printed in the paper as established fact.

---

## 1. Problem statement

A user who is anxious about money, grief-stricken, preparing for travel, or facing illness
typically cannot determine *which* dua is appropriate. Existing dua applications address this
with **browsing**: a hierarchy of categories ("Distress", "Financial Difficulty") that the user
must already know in order to find their need. This fails precisely at the moment of need,
because a distressed user does not know the category taxonomy.

Keyword search fails for the same reason. A user typing `"I am worried about money"` shares
almost no vocabulary with a dua recorded under the heading *"Dua for expanding one's livelihood"*.

This project builds a **retrieval system**: given a natural-language description of a user's
situation, retrieve and rank the most contextually relevant duas from an authentic, source-traceable
corpus, and show the user *why* each was recommended together with its documented religious source.

The system is a **retrieval and ranking tool**. It is not a religious authority, and it never
generates religious text. See §23.4.

---

## 2. Research gap

Prior work exists on every component in isolation:

| Area | Prior work | What it does not do |
|---|---|---|
| Qur'anic semantic retrieval | QSST (2020), hybrid SBERT+TF-IDF recommenders | Targets verses, not duas |
| Emotion-aware Qur'anic analysis | Emotionally-Labeled Qur'anic Verses (ELQV) | Verse-level emotion, not supplication context |
| Qur'anic verse recommendation | Hybrid SBERT-TFIDF + LLM explanation (ICDSA 2025) | Verses; no situation/emotion/intent decomposition |
| Grounded Islamic QA / RAG | Agentic RAG for Islamic QA, IslamicFaithQA (ACL Findings 2026) | Question answering; assumes a correct dua already selected |
| Religious NLP generally | Arabic/Islamic corpora, morphology tooling | No user-facing recommendation layer |

**Gap:** there is no dedicated **context-aware dua recommendation** framework that combines
(a) semantic understanding of a user's described situation, (b) multi-dimensional context
(situation / emotion / intention / occasion / time), (c) an expert-annotated dua ontology, and
(d) source-grounded presentation with human evaluation of religious relevance.

**This is a final-year project, so the gap is claimed narrowly:** we do not claim to be the first
semantic Islamic retrieval system, and we do not claim novelty in embedding models. Our
contribution is the *integration and the annotated dataset*, evaluated comparatively.

---

## 3. Research questions

**RQ1.** To what extent does a hybrid lexical + semantic retriever outperform a lexical-only
baseline for matching free-text user situations to duas?

**RQ2.** Do structured context dimensions (situation, emotion, intention, occasion, time)
contribute measurable additional retrieval quality over unstructured semantic similarity alone?

**RQ3.** Are machine rankings of dua relevance acceptable to qualified Islamic scholars?

**RQ4 (secondary).** Which failure modes dominate — vocabulary mismatch, annotation noise,
or genuinely ambiguous queries (multiple defensible dua sets)?

---

## 4. Objectives

| # | Objective | Success measure |
|---|---|---|
| O1 | Build an annotated Dua corpus with multi-dimensional context labels | ≥300 duas, ≥2 annotators, Cohen's κ reported |
| O2 | Build a query evaluation set with graded relevance | ≥300 realistic user queries, expert-labelled |
| O3 | Implement and compare 5 retrieval configurations | Table of metrics per model |
| O4 | Learn or validate ranking weights | Weights justified by data, not asserted |
| O5 | Obtain expert validation of output quality | ≥2 scholars rate a sample; disagreements analysed |
| O6 | Deploy a working web application | Live URL, reproducible build |
| O7 | Document licensing and ethical constraints | §7 and §23 complete before public release |

---

## 5. Scope

### 5.1 In scope (v1)

- Corpus of 300–500 duas with full source attribution
- Expert-annotated context metadata (§9)
- 5 retrieval models + evaluation harness (§14, §15)
- Web/PWA application: recommendation, browse, search, favorites, history, daily dua,
  occasion-aware reminders, Quran reader
- Hadith module: browse a curated, cited set (see risk R3)
- Public code + documentation

### 5.2 Explicitly out of scope (v1)

- Generating or paraphrasing religious text
- Collaborative filtering (insufficient user base; cold-start unsolved)
- Urdu / Arabic / multilingual query input
- Voice input
- Cross-encoder reranking (stretch goal only, §15 M5)
- User accounts and cloud sync
- Mobile-native applications

---

## 6. Contributions

1. **Context-Aware Dua Dataset** — an open dataset of authentic duas annotated with situation,
   emotion, intention, topic, occasion, and time dimensions, with inter-annotator agreement reported.
2. **Hybrid Context-Aware Ranking Model** — lexical + semantic + structured context signals,
   with weights derived from validation data rather than asserted.
3. **Scholar-Validated Evaluation** — comparison of automatic metrics against human religious
   judgement, including cases where the two disagree.
4. **Grounded Application** — every recommendation carries its source, reference, Arabic original,
   translation, and (where applicable) authenticity grade, with a user-facing explanation of why
   it was selected.

---

## 7. Data sources and licensing

**Licensing is a release blocker. Nothing ships until §7.3 is satisfied.**

### 7.1 Candidate sources

| Source | Use | License status | Verification |
|---|---|---|---|
| **OpenDua** (Human-Development-Fund) | Primary dua corpus; ordered text blocks, source identity, collection structure, audio, review states | SDK MIT. **Editorial text + dataset structure CC BY 4.0. Underlying religious texts are explicitly NOT claimed under CC BY 4.0. Audio/recitation terms are separate.** A versioned rights registry (`rights()`) is authoritative | `[V]` via OpenDua SDK README, 2026-10-03 |
| **OpenDua API** | Programmatic access | Public read API, no auth. **v2 is a release candidate (SDK 0.2.0-rc.1), staging host `api.staging.opendua.org`, not on npm, schema may change, staging content does not imply scholarly approval.** Dataset is versioned via `datasetVersion` | `[V]` via SDK README |
| OpenDua entry count / chapter count | Sizing the corpus | Plan claimed "267 entries / 132 chapters" — **could not be confirmed**; `/metadata` and `/rights` returned 404 from this environment | `[U]` `[A]` verify in Phase 3 |
| **Quran Foundation / Quran.com API** | Quran reader: chapters, verses, translations, tafsir, audio, recitations, juz, hizb, ruku, manzil, search | Content APIs v4 confirmed. **Requires app credentials; must be called from backend, never from browser/mobile code.** Docs: `api-docs.quran.foundation` | `[V]` 2026-10-03 |
| **sunnah.com API** | Hadith module | **Requires API key requested by opening a GitHub issue.** Access requests sit in a long backlog. Offline dump "not available yet". Partial data, still under manual verification | `[V]` via sunnah.com/developers |
| Hisn al-Muslim transcriptions (various GitHub repos) | Fallback / cross-check | Mixed and mostly unclear: `rn0x/hisn_almuslim_json` (no license assigned), `ThelightHub/dua-api` (MIT, 421 duas, asserts public-domain religious text), `sehalhussain/Hadith-Dua-assets` (scraped sunnah.com, no clear license) | `[U]` — do not use without independent license review |
| ELQV (Emotionally-Labeled Qur'anic Verses) | Optional emotion-label transfer | Claimed as 2,100 specialist-annotated verses, 4 emotion categories, with Arabic + English translations. **Not yet located or license-checked** | `[U]` `[A]` |

### 7.2 Mandatory source rules

- **Snapshot, do not depend.** Because OpenDua v2 is a staging release candidate, the corpus is
  downloaded **once** and committed to `data/raw/` as an immutable snapshot with the
  `datasetVersion` recorded. All experiments read the snapshot. A live API call must never occur
  inside an experiment loop.
- **Rights registry is snapshotted too.** Store `rights()` output alongside the corpus so that
  redistribution obligations are reconstructable later.
- **No scraping of Islamic websites.** Authenticity, copyright, and correction-tracking are all
  unresolvable under scraping.
- **Citation per dua is mandatory.** Every record carries source work, entry number, and the
  attribution exactly as given by the source. Missing reference = record rejected, not defaulted.

### 7.3 Release gate

Before any public repository is published:

- [ ] Every dua's licensing status recorded per field (Arabic text, translation, transliteration, audio)
- [ ] Translations redistributed only with explicit permission, or replaced with permissively-licensed alternatives
- [ ] Audio either excluded from the repo or redistributed under terms confirmed from the rights registry
- [ ] `LICENSES.md` written, listing each source, its terms, and what we redistribute
- [ ] Scholar review of the Arabic text of a sample (≥10%) against the printed source

---

## 8. Dataset schema

`data/duas/duas_annotated.json` — one record per dua.

```
dua_id                  stable, never reused
title
arabic                  source text, diacritics preserved, never normalised destructively
transliteration
translation
translation_attribution REQUIRED — translator and work, or null if unknown
source_work             e.g. "Hisn al-Muslim"
source_entry            entry number / chapter as given by the source
source_url              canonical reference
authenticity_grade      string or null; only where the source states one
authenticity_basis      who assigned the grade
occasions               [occasion_id]      multi-label
situations              [situation_id]     multi-label
emotions                [emotion_id]       multi-label
intentions              [intention_id]     multi-label
topics                  [topic_id]         multi-label
time_context            [morning|evening|night|anytime]
recitation_count        int or null
audio_ref               object key or null — resolved at runtime, never a hardcoded URL
blocks[]                ordered source-of-truth blocks (recitation / instruction / narration / note)
review_states           source, translation, scholar, audio review status
annotation              per-label annotator ids, agreement, adjudication notes
embedding_ref           index into duas_embeddings.npy — never stored inline
```

**Multi-label, not single-label.** A dua for travel is also a dua for protection and for fear.
Single-label annotation would destroy exactly the signal the project is trying to model.

---

## 9. Dua ontology

A controlled vocabulary. Every term carries a written definition and inclusion/exclusion rules
in the annotation guidelines (§10). Terms are proposals until scholar-reviewed.

**Situation** — sadness, stress, anxiety, fear, financial_difficulty, debt, unemployment,
illness, death_of_loved_one, travel, marriage, family_conflict, study, work, sin, repentance,
loneliness, conflict, grief, uncertainty_about_future, protection_from_harm, new_home, pregnancy

**Emotion** — sadness, fear, anxiety, hope, gratitude, joy, anger, regret, loneliness, peace,
humility, desperation, patience

**Intention** — guidance, forgiveness, protection, healing, sustenance, patience, knowledge,
ease, gratitude, repentance, gratitude_for_safety, expiation, ward_off_harm

**Occasion** — daily, morning, evening, night, before_sleep, after_sleep, friday, ramadan,
eid_al_fitr, eid_al_adha, hajj, umrah, wedding, travel, rain, illness, new_home, death, debt,
exam

**Topic** — quran, hadith, praise_of_allah, protection, provision, health, family, knowledge,
patience, repentance, gratitude

**Rules**
- Situation = *the user's circumstance*. Emotion = *the user's feeling*. Topic = *the subject matter
  of the dua*. These three are routinely confused; the guidelines must separate them with examples.
- Intention describes the purpose the dua serves, not the user's motive.
- Every label must be supportable by a line in the source's own context block. If the source does
  not say why the dua is prescribed, that is recorded as `occasion: general` and flagged for
  scholar adjudication — **not** filled in by inference from the Arabic.

---

## 10. Annotation protocol

### 10.1 Process

1. Draft ontology + guidelines; **scholar review of the guidelines themselves** before annotating.
2. Two annotators independently label all 300–500 duas, blind to each other.
3. Compute agreement per label set.
4. Adjudicate disagreements with both annotators; record the adjudicated label and the reason.
5. Freeze as `duas_annotated.json` v1.0. Later changes are new versions, not silent edits.

### 10.2 Agreement

Cohen's κ for two annotators, per label set. Report the confusion matrix for every label set where
κ < 0.6 — low agreement is itself a finding and must not be hidden. If three or more annotators are
used, use Fleiss' κ instead.

**Interpretation guide:** κ ≥ 0.8 strong, 0.6–0.8 moderate, < 0.6 weak. Weak agreement on the
`emotion` set is *expected* and is a legitimate result to report.

### 10.3 Annotation guidelines must specify

- One worked example per label, with reasoning
- The situation/emotion/topic disambiguation rules from §9
- The "no source support → do not label" rule
- How to handle duas with multiple distinct recitations
- Adjudication escalation path

---

## 11. Query evaluation dataset

`data/evaluation/queries.json` — ≥300 realistic user situations, at least 60% written by people
who did not build the system.

```
query_id
text                     e.g. "I'm worried about how I'll pay my rent this month"
implied_time             morning | evening | none
implied_occasion         friday | ramadan | none
chip_label               situation chip that should fire, or null
gold_relevance           { dua_id: grade }   grade ∈ {3 highly, 2 relevant, 1 marginal, 0 not}
annotator_ids
notes
```

**Graded relevance, not a single answer.** Many queries have several defensible dua sets. A
binary "correct answer" would mislabel good systems as wrong. Graded labels make NDCG meaningful.

**Query design requirements**
- Include paraphrase-heavy queries that share no keywords with their gold duas (this is where
  TF-IDF must visibly fail — it is the strongest evidence for the project's premise)
- Include at least 20 deliberately ambiguous queries, excluded from headline metrics and reported
  separately as the ambiguity ceiling
- Include ~10% chip-only queries for the chips path
- Stratify across the ontology so no single situation dominates

---

## 12. System architecture

```
                        USER (web / PWA)
                              │
              free text  ─────┴─────  situation chips
                              │
                    app context (local): time, Hijri date,
                    occasion, dismissed ids, opt-in history
                              │
                              ▼
                   Next.js route handler (server)
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
     Context extraction   Quran service    Hadith service
     (emotion / situation │ (Foundation    (curated set /
      / intention)         │  API, backend  API if key granted)
              │            │  credentials)        │
              ▼            ▼                ▼
      Recommendation    cached proxy     static JSON
        engine           + local cache
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
 embeddings  metadata   context
 (npy/idx)   filters    scores
   └──────────┼──────────┘
              ▼
      Context-aware ranker ──► top-K duas
              │                    │
              ▼                    ▼
      recommendation_log     source verification
      (anonymised)           (reference present?)
                                        │
                                        ▼
                                 PWA UI + notifications
```

**Serving the model.** Corpus embeddings are precomputed offline and shipped as an artifact.
Per-request work is one query embedding plus a cosine scan over ~500 vectors — trivial. No model
server, no cold start, no per-request model download.

**Deployment constraint:** embedding the corpus means shipping a ~500 × 768 float array
(~1.5 MB as float32). Options: bundle it, or run embedding in a serverless Python function. Decide
in Phase 10 by measuring; do not guess now.

---

## 13. ML pipeline

```
User query
   │
   ├─► normalise (case, punctuation, stopwords, light stemming)
   │
   ├─► EMBED (multilingual sentence-transformers / SBERT)
   │        model + version pinned in config, never "latest"
   │
   ├─► CLASSIFY  emotion, situation, intention
   │        method A: zero-shot label matching over ontology text
   │        method B: fine-tuned classifier on annotated duas
   │        method B is a stretch goal — method A is the v1 baseline
   │
   ├─► CANDIDATE RETRIEVAL (union, not intersection)
   │        semantic top-N  (cosine)
   │        lexical  top-N  (TF-IDF cosine)
   │        metadata  top-N (label overlap)
   │
   ├─► FUSE  reciprocal rank fusion OR weighted score sum (§14)
   │
   ├─► CONTEXT FILTER  occasion/time hard constraints, diversity, seen-item exclusion
   │
   ├─► RERANK  (optional M5)
   │
   └─► TOP-K + per-item score breakdown for the explain panel
```

**Filter as hard constraint, not a weight.** If it is Ramadan, Ramadan-tagged duas should be
promoted by a filter, not nudged by a 0.05 occasion weight competing against a 0.35 semantic
weight. This is a deliberate correction to the weight scheme in the original plan.

---

## 14. Ranking model

```
score(d) = w_sem·semantic
         + w_lex·lexical
         + w_sit·situation_match
         + w_emo·emotion_match
         + w_int·intention_match
         + w_occ·occasion_match
         + w_pref·user_preference
         + w_div·diversity
```

**Weights must be learned, not declared.** The plan's hand-picked numbers (0.35/0.15/…) are a
starting point only. Procedure:

1. Initialise with uniform or hand-set weights.
2. Tune on a **validation split** of the query set (never the test split).
3. Method: coordinate ascent or a small learning-to-rank model over the same features.
4. Report final weights and their sensitivity — if results barely move when weights change, say so.

**Match functions.** For label overlap use normalised overlap (e.g. Jaccard or |A∩B|/|A∪B|), not a
binary flag; binary flags destroy ranking information. For multi-label situations, weight labels
by annotator agreement so contested labels count less.

**Personalisation term.** v1 is content-based only: a small bonus for locally favourited topics.
Collaborative filtering is out of scope (§5.2).

---

## 15. Models compared

| ID | Model | Purpose |
|---|---|---|
| **M1** | TF-IDF + cosine | Lexical baseline. Must exist; it is the control |
| **M2** | SBERT + cosine | Semantic baseline. Isolates the embedding contribution |
| **M3** | M1 + M2 fusion | Hybrid. Tests complementarity |
| **M4** | M3 + context dimensions | **Proposed model.** The research contribution |
| **M5** | M4 + cross-encoder rerank | Stretch goal; if skipped, say so in the paper |

M5 is a `ms-marco-MiniLM-L-6-v2` style reranker over the top-50 from M4. It is a genuine
research question whether reranking helps in a domain where the candidate set is only ~500 —
with 500 candidates, reranking may add nothing, and reporting that honestly is a valid result.

---

## 16. Evaluation methodology

**Automatic metrics** on the test split of `queries.json`:

- Precision@1, Precision@5
- Recall@5
- MRR
- NDCG@5 (primary metric — graded relevance)
- Hit@5

**Protocol requirements**
- Fixed random seed, recorded
- Train/validation/test split of queries, stratified by situation, split **before** any tuning
- Report mean ± std over ≥5 runs where any stochastic component exists
- Report M4's gain over M3 with a paired bootstrap or Wilcoxon signed-rank test over queries —
  with ~300 queries this is cheap and makes the claim defensible
- **Error analysis**: sample 30 errors, categorise by cause, report counts

**Leakage controls.** Query sets authored by the same people who wrote the ontology will inflate
results. Require ≥60% query authorship from people outside the annotation team, and state the
actual proportion achieved.

---

## 17. Expert evaluation protocol

Two or more qualified Islamic scholars, independent of the annotation labelling round where
possible (or at minimum blind to model identity).

1. Present a random sample of 50 queries.
2. For each, show **each model's top-5**, in randomised order, labelled by model only as
   "System A/B/C".
3. Ask for a graded relevance judgement (0–3) per dua, plus a free-text note where wrong.
4. Separately: ask whether the top-1 recommendation is *religiously appropriate* to present to a
   Muslim user — this is a different question from relevance, and is the one that matters most.
5. Analyse: agreement with automatic metrics, scholar–scholar disagreement, and any case where all
   systems were judged inappropriate.

**Reporting requirement.** Report cases where scholars reject a system's top-1. A religious
application whose evaluation only reports successes is not credible. If the scholars find a
systematically problematic pattern, that is a finding and drives a fix or a documented limitation.

---

## 18. Database schema (MongoDB Atlas)

```
users                  anonymousId, createdAt, locale, consentFlags
duas                   §8 record, minus embeddings
dua_embeddings         duaId, model, dim, vector, datasetVersion
ontology               type, termId, definition, inclusionRule, exclusionRule, reviewerIds
annotation_runs        runId, annotatorIds, guidelinesVersion, startedAt, completedAt
annotation_labels      duaId, annotatorId, labelSet, labels, timestamp
adjudications          duaId, labelSet, finalLabel, reason, adjudicatorId
queries                §11 record
quran_cache            surahKey, resourceId, payload, fetchedAt
hadiths                collection, bookNumber, hadithNumber, arabic, translation, grade, reference
islamic_events        eventId, hijriRule, gregorianRule, precedence
recommendation_logs    anonymisedId, queryId, queryText, detectedLabels, modelId,
                       candidates[], returned[], selectedDuaId, feedback, timestamp
favorites              anonymisedId, duaId, createdAt
history                anonymisedId, duaId, action, timestamp
notifications          anonymisedId, schedule, occasionFilter, enabled
feedback               recommendationLogId, rating, comment
```

`recommendation_logs` is the most valuable collection in the project — it is the raw material for
future work (§29). Log the full candidate set with per-component scores, not just the top-K, or
the ranking cannot be reconstructed offline.

---

## 19. API surface

```
POST   /api/recommend          { query | chip, context }        → ranked duas + score breakdown
POST   /api/search             { query }                        → explicit lexical/semantic search
GET    /api/duas               ?situation&occasion&topic&page
GET    /api/duas/:id
GET    /api/ontology
GET    /api/calendar           ?date=YYYY-MM-DD                 → hijri + occasion
POST   /api/feedback           { logId, rating }
GET    /api/quran/chapters
GET    /api/quran/verses/:key   → proxy to Quran Foundation, server-side credential
POST   /api/log                recommendation log write
```

**`/api/search` and `/api/recommend` are different problems and stay separate.**
Search = the user knows what they want. Recommend = the user describes a situation and the system
interprets it. Merging them corrupts both the product and the evaluation.

---

## 20. UI modules

1. **Recommend** — text input + situation chips; results as dua cards; "Why this?" panel;
   optional research/debug panel showing component scores
2. **Dua card** — title, Arabic, transliteration, translation, occasion, source, reference,
   authenticity grade if stated, related Quran/Hadith, actions: save, recite, audio, copy, share
3. **Browse** — by situation, occasion, topic, source work
4. **Search** — explicit, with filters
5. **Quran reader** — surah list, verse-by-verse, translation, tafsir, audio, repeat, bookmark,
   last-read position, font size, dark mode
6. **Hadith** — collection → book → hadith, narrator, reference, grade where stated
7. **Calendar** — Gregorian ↔ Hijri, upcoming occasions
8. **Daily Dua / reminders** — see §21
9. **Library** — favourites, history, settings
10. **Methodology & disclaimer** — a permanent, visible link to §23.4

**"Why this?" panel** shows intent-level reasons in plain language (detected situation, detected
intention, relevance phrasing, source). Raw ML scores are hidden behind a separate research toggle.

---

## 21. Islamic calendar and notifications

```
Gregorian date → Hijri date (Umm al-Qura based)
               → occasion detector
               → context
```

Occasions: Friday, Ramadan, Eid al-Fitr, Eid al-Adha, Hajj/Umrah window, plus dated events
(Arafah, Ashura, Mawlid) where the calendar supports it.

**Hijri conversion library:** use a vetted Umm al-Qura implementation (e.g. `hijri-converter` in
Python, `@umalqura/core` in JS). `[U]` — library choice and its documented accuracy must be
confirmed at implementation. Tabular Islamic calendars are ±1 day against local moon sighting;
state which convention the app uses and let the user override the date.

**Notifications are controlled, not random:**

```
morning/evening/Friday occasion fires
   → candidate set filtered to time/occasion-compatible duas
   → exclude recently shown and dismissed
   → apply user preferences
   → rank
   → sample from top-5 (not top-1) to preserve variety
```

This is *personalised stochastic recommendation*. Document the sampling step — it is a deliberate
design choice, not randomness for its own sake.

**Personalisation limits.** Behaviour-derived notifications must be opt-in, individually
disable-able, and must never reference sensitive inferred categories in notification text. A
notification that says "you seem to be struggling financially" is a privacy and dignity problem
regardless of accuracy.

---

## 22. Personalisation

v1: content-based, local-only.
- Favourites, recitation counts, dismissals, preferred times, topic preferences
- All stored locally (IndexedDB); server sync only if the user opts in
- Contribution to ranking is one term with a small weight
- Cold-start handled by the content-based signals alone

No collaborative filtering. With no user base it is unevaluable, and pretending otherwise would be
padding.

---

## 23. Privacy, security, ethics

### 23.1 Privacy
- Anonymous by default. No account required for any core function.
- Query text is the most sensitive field in the system. Default: store hashed/anonymised; store
  plaintext only with explicit opt-in, and never full text in analytics.
- Recommendation logs used for research must be de-identified and documented as such.
- Clear "delete all my data" control.

### 23.2 Security
- All API credentials server-side only. No Quran Foundation key in client bundles.
- Hadith API key server-side only.
- Rate limiting on public endpoints; the recommendation endpoint is cheap to abuse.
- No user-supplied content rendered as HTML without escaping.

### 23.3 Licensing compliance
Per §7. Release gate applies.

### 23.4 Religious responsibility — mandatory product requirement

The application must state, in a place a user actually sees (not buried in a footer):

> DuaWise is a retrieval tool. It identifies duas whose documented sources and contexts match the
> situation you describe. It does not generate religious text, it does not issue religious rulings,
> and it does not promise particular outcomes. For questions of religious importance, consult a
> qualified scholar.

**Hard prohibitions**
- Never generate or compose a dua
- Never state or imply that a dua will produce a specific worldly outcome
- Never present the ranking as "the Dua Allah wants you to read"
- Never display a recommendation without its source
- Every LLM-generated text is explanatory only, strictly downstream of a retrieved, verified dua,
  and must never contain religious text

### 23.5 Evaluation ethics
Scholars must be compensated or credited, must consent to their judgements being reported, and
must review the paper's claims about religious appropriateness before submission.

---

## 24. Deployment

- **App:** Next.js (App Router) + TypeScript + Tailwind, PWA, deployed on Vercel
- **Database:** MongoDB Atlas
- **ML:** Python offline pipeline (`ml/`), artefacts committed or cached; no always-on model server
- **Free-tier fit:** precomputed embeddings + a small corpus means the runtime cost is one API
  round trip plus a vector scan. Vercel Python functions are available (documented as Beta) if a
  Python runtime is needed, but the design should avoid depending on it.

**Explicit non-goal:** do not embed model weights in the client bundle.

---

## 25. Repository structure

```
dua-wise/
├── apps/
│   └── web/                     Next.js PWA
├── ml/
│   ├── src/dua_reco/            package: data, embeddings, models, rank, evaluate, explain
│   ├── notebooks/               exploration (exploratory only, not the pipeline)
│   └── tests/
├── data/
│   ├── raw/                     immutable source snapshots + rights registry
│   ├── processed/               cleaned, annotated, split
│   ├── ontology/
│   ├── evaluation/
│   └── artifacts/               embeddings, model versions, manifests
├── docs/
│   ├── SPEC.md                  this document
│   ├── DATASET.md               sources, licensing, provenance, changelog
│   ├── ANNOTATION.md            guidelines
│   ├── ONTOLOGY.md              terms + definitions
│   ├── ARCHITECTURE.md
│   ├── EXPERIMENTS.md           run log: config, seeds, results
│   └── ETHICS.md                §23 as a standalone document
├── paper/
├── scripts/
├── LICENSE
├── LICENSES.md
├── README.md
└── CONTRIBUTING.md
```

`EXPERIMENTS.md` is mandatory and append-only. A results table that cannot be traced to a
config, a seed, and a commit hash is not evidence.

---

## 26. Development roadmap

Each phase has an exit criterion. Do not start a phase until the previous one is met.

| Phase | Work | Exit criterion |
|---|---|---|
| 1 | Literature review | ≥15 papers read, matrix in `docs/`, gap statement written |
| 2 | Research questions | RQ1–RQ4 finalised, signed off by supervisor |
| 3 | Data source & licensing | §7.1 verified, OpenDua snapshot downloaded, `datasetVersion` pinned, `LICENSES.md` drafted |
| 4 | Dua dataset | Corpus cleaned and normalised, Arabic integrity checked |
| 5 | Ontology | Terms defined with inclusion/exclusion rules |
| 6 | Annotation | Guidelines scholar-approved; 2 annotators complete; κ reported per label set |
| 7 | Baselines | M1, M2 implemented and evaluated on the test split |
| 8 | Proposed model | M4 implemented; weights learned on validation split only |
| 9 | Evaluation | All metrics + error analysis + significance test; `EXPERIMENTS.md` written |
| 10 | Expert evaluation | ≥2 scholars complete protocol, results analysed |
| 11 | Web application | Recommend, browse, search, favourites, history working |
| 12 | Quran integration | Reader working via backend proxy |
| 13 | Hadith integration | Curated set live, or module deferred with documentation |
| 14 | Calendar + notifications | Occasion detection verified across a full lunar year |
| 15 | Feedback loop | Logging + "Why this?" panel live |
| 16 | Open source | Licence, `LICENSES.md`, `ETHICS.md`, README, contribution guide |
| 17 | Paper | Draft complete, scholar-reviewed claims |

**Phase 14 warning:** occasion logic cannot be validated in one month. A calendar bug that
misidentifies Ramadan is far worse than a missing feature. Test against a multi-year Hijri table.

---

## 27. Risks

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | OpenDua v2 is a staging RC; schema or availability changes | Corpus breaks | Snapshot to `data/raw/`, pin `datasetVersion`, never call the API in experiments |
| R2 | Translation licensing blocks redistribution | Cannot release | §7.3 gate; fall back to permissively-licensed translations or ship references without full text |
| R3 | Hadith API key denied or backlogged | Hadith module blocked | Do not make it a critical-path dependency; curate a small cited set; document deferral |
| R4 | Annotator availability drops | Whole project blocks | Recruit a third annotator early; keep guidelines precise enough to train a new annotator quickly |
| R5 | Low κ on emotion labels | Weakens M4's headline claim | Report it as a finding; weight labels by agreement; consider dropping the emotion term if it does not help |
| R6 | Results are not better than M2 | Central claim fails | This is a real possibility and must be reported honestly. The dataset and the framework remain valid contributions |
| R7 | Scope creep into a full Islamic platform | Nothing ships | §5.2 is binding |
| R8 | Query set authored by the project team | Inflated results | ≥60% external authorship, stated explicitly |
| R9 | Hijri conversion off by one day | Wrong occasion content | Multi-year table test; user date override |
| R10 | Scholarship treated as decoration rather than validation | Ethically hollow | Annotators and evaluators are credited and compensated; claims reviewed by them |

**R6 deserves emphasis.** The honest framing of this project is: *we built an annotated corpus, a
hybrid framework, and an honest evaluation of how much context-awareness actually helps.* If the
answer is "a little", that is a publishable-quality negative result for an undergraduate project.
Do not build the narrative around a result you have not observed.

---

## 28. Acceptance criteria

The project is complete when:

- [ ] Corpus of ≥300 duas, each with source, reference, Arabic, translation, attribution
- [ ] κ reported for every label set, with low-agreement sets explained
- [ ] ≥300 queries with graded expert relevance labels
- [ ] M1–M4 evaluated; M4's gain over M3 tested for significance
- [ ] Weights derived from validation data and documented
- [ ] ≥2 scholars completed evaluation; agreement with automatic metrics analysed
- [ ] Live deployed application covering recommend, browse, search, Quran, calendar, reminders
- [ ] Every recommendation displays its source
- [ ] Disclaimer visible in the UI (§23.4)
- [ ] `LICENSES.md` and `ETHICS.md` complete; release gate §7.3 passed
- [ ] No generated religious text anywhere in the system
- [ ] Repository reproducible: `EXPERIMENTS.md` traces every result to a commit

---

## 29. Future work (explicitly not v1)

- **Multilingual** — Urdu and Arabic query input with multilingual embeddings. Strong direction:
  far less prior work exists for Urdu Islamic retrieval.
- **Voice input** — Urdu or English speech-to-text feeding the same pipeline.
- **Behavioural personalisation** — the `recommendation_logs` collection already being collected
  in v1 makes this possible without new instrumentation.
- **Cross-domain retrieval** — return duas, Qur'anic verses, and hadith from separate trusted
  corpora for one query, i.e. grounded multi-source Islamic retrieval.
- **Personalisation with collaborative signals** — only once a real user base exists.
- **Weight sensitivity and learned ranking** — a learning-to-rank model over the same features.

---

## 30. Paper outline

1. Introduction — growth of digital Islamic resources; the retrieval problem; contribution
2. Related work — Qur'anic semantic retrieval, Islamic NLP, emotion classification, recommenders,
   religious AI. **Include a table contrasting each system against DuaWise on: dua-level, context
   dimensions, expert-annotated ontology, human evaluation, source grounding.**
3. Research gap and questions
4. Dataset — sources, licensing, cleaning, ontology, annotation, κ
5. Methodology — context extraction, representation, candidate retrieval, fusion, filtering, ranking
6. Experiments — models, splits, metrics, significance
7. Results — tables, error analysis, comparison to expert judgement
8. Application — deployed system, architecture
9. Religious and ethical considerations
10. Limitations — including R6 if applicable
11. Conclusion

---

## Appendix A — terminology

| Term | Meaning in this project |
|---|---|
| Dua | Supplication. Treated here as a fixed, sourced record — never generated |
| Occasion | *When* a dua is traditionally recited (morning, Friday, travel) |
| Situation | *The user's circumstance* (debt, illness, grief) |
| Emotion | *The user's feeling* (anxiety, gratitude) |
| Intention | The purpose the dua serves (forgiveness, protection) |
| Topic | Subject matter of the dua itself |
| Grounded | Every output traces to a specific source record; nothing is synthesised |
| Graded relevance | 0–3 judgement of how appropriate a dua is for a query |

## Appendix B — open questions for the supervisor

1. Is the annotation sample size (300–500 duas) acceptable, or is full corpus annotation expected?
2. Are two annotators with Islamic studies background acceptable, or is a qualified scholar
   required for annotation (not just evaluation)?
3. Is the target venue a university showcase, a student journal, or a conference?
4. Are there existing supervisor-provided datasets or corpora that should be used instead?
5. What is the submission deadline relative to the 17 phases above?