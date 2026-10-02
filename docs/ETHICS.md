# Ethics and annotation protocol

DuaWise handles religious text. The constraints below are treated as
requirements, not aspirations, and several of them are enforced in code.

## Non-negotiable rules

1. **Never generate religious text.** The system never produces a Dua, never
   paraphrases one, and never completes a fragment. It retrieves verbatim text from
   cited sources and says nothing further. Enforced structurally: there is no
   generative component anywhere in the pipeline.

2. **Never guarantee outcomes.** No output implies that reciting a Dua will produce
   a result. Wording in the UI and explanations avoids efficacy claims.

3. **Never issue religious rulings.** The system does not adjudicate what is
   permitted, recommended, or authentic. Surfacing a text from a collection is not
   an endorsement of its position.

4. **Always show the source.** Every result carries its work, reference, and
   reference-resolution status. A suggestion without attribution is a defect.
   Enforced by `Dua.as_dict()` and rendered by `DuaCard`.

5. **Never hide uncertainty.** The corpus annotation status (`DRAFT_UNREVIEWED`) is
   surfaced in the API response and shown to users on each card.

## Unreviewed status

Every record carries a `review_states` block:

```json
{
  "arabic": "fetched_from_source_unverified",
  "translation": "fetched_from_source_unreviewed",
  "context_labels": "draft_unreviewed",
  "scholar": "not_reviewed"
}
```

`scholar: not_reviewed` means no qualified Islamic scholar has checked the entry.
The UI displays an explicit notice when this is true. No record may claim
scholar review until a named reviewer has signed off.

## Annotation protocol

The controlled vocabulary lives in `data/ontology/ontology.json`. Each term carries a
`definition` plus `includes` and `excludes` examples. The `excludes` list is what
makes the vocabulary usable: it resolves the boundary cases that otherwise get
annotated inconsistently (for example, `sadness` explicitly excludes grief over a
death, which belongs to `death_of_loved_one`).

### Label sets

- **situations** (31 terms) — what is happening. The primary retrieval signal.
- **emotions** (16) — how the user feels.
- **intentions** (15) — what the user is seeking.
- **occasions** (23) — time and day, including `general`.
- **topics** (18) — subject matter.

### How annotations were produced

- 263 records annotated manually against the definitions in the annotation guide.
- 95 records derived by keyword matching over the English text, because manual
  annotation did not scale to the whole corpus.

The keyword-derived records are weaker and are flagged as
`context_labels: keyword_derived_unreviewed` so they can be filtered out or
prioritised for review.

### Rules for a reviewer

1. Label from the **Dua's own text and stated purpose**, never from the situation
   the reviewer imagines. A Dua recited for a general benefit is `general`, not
   guessed at from context.
2. Prefer the most specific applicable term, but do not invent new terms mid-pass.
   New vocabulary is a schema change requiring review of every affected record.
3. Record a disagreement rather than resolving it silently. Two scholars
   disagreeing is a finding to report, not an error to hide.
4. Relevance judgements for evaluation must be made **blind** to model output and,
   ideally, by someone who did not write the queries.

## Known problems with the current annotations

Stated plainly because they affect how the results should be read:

- Annotations are drafts from a single author with no religious training. They are
  the weakest part of the project.
- Gold relevance labels for the evaluation set are derived from these same
  annotations, which makes the evaluation partly circular and inflates the
  context-aware model's measured advantage. See `docs/EXPERIMENTS.md`.
- Some Hadith reference strings arrive from the upstream API in Bengali script and
  are untranslated.
- The keyword-derived pass produces confident-looking labels on records where the
  English text merely mentions a topic in passing.

## Privacy

- Queries are held in browser memory for the duration of the request and are not
  persisted by the application.
- Saved Duas live in `localStorage` only. There is no account system.
- No analytics, no third-party scripts, no fingerprinting.
- The service worker explicitly does not cache recommendation requests, so a stale
  ranking cannot be presented as current and query text is not retained offline.

## Required before any public launch

1. Two or more qualified Islamic scholars review the ontology and a sample of
   annotations, with disagreements recorded.
2. Reference strings are verified against the printed source collections.
3. An independent, blind relevance-labelled evaluation set replaces the
   circularly-derived one.
4. Both data licence blockers in `docs/LICENSES.md` are cleared.
