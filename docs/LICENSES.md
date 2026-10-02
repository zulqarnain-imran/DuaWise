# Licensing and redistribution status

**Current status: this corpus is NOT cleared for public redistribution.**

This file records the licence position for every external source used, because a
religious-text app that cannot lawfully ship its own corpus is not deployable.
Two blockers remain open and are marked accordingly.

## Sources

| Source | Endpoint / repository | Licence | Status |
| --- | --- | --- | --- |
| Qur'an text (Uthmani) | `api.quran.com/api/v4` | Terms of use unconfirmed for redistribution | **BLOCKER** |
| Saheeh International translation | Quran.com translation resource `20` | King Fahd Complex licence; redistribution terms unconfirmed | **BLOCKER** |
| Hisn al-Muslim metadata, Arabic, references | `dua-api.hisnul.workers.dev` | No licence declared | Unclear; used as an attribution source only |
| Hisn al-Muslim English translation | `github.com/wafaaelmaandy/Hisn-Muslim-Json` | **No licence file** | **BLOCKER** |
| Embedding model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Apache-2.0 (model card) | OK |
| Application code | this repository | See `LICENSE` | MIT |

## Open blockers in detail

### 1. Hisn al-Muslim English text has no licence

`wafaaelmaandy/Hisn-Muslim-Json` publishes no `LICENSE` file. Under default
copyright, absence of a licence means all rights reserved: the text may be read but
not redistributed. The 264 Hisn al-Muslim records in
`data/processed/duas.json` currently include translations from this repository.

It is used anyway for **research evaluation only**, which is defensible locally,
but it blocks any public deployment until one of the following happens:

- The repository author is contacted and grants explicit redistribution permission.
- A permissively licensed alternative is substituted.
- Only the Arabic text plus a self-produced translation is shipped, with the
  Arabic verified against a licensed edition.

### 2. Qur'an text and translation redistribution terms

api.quran.com serves the text without authentication, which makes it convenient,
not permissive. Serving the words publicly is a separate question from serving them
to a requester. The King Fahd Complex licence for the Saheeh International
translation permits non-commercial quotation with attribution, but a hosted
recommendation engine that returns the text to arbitrary users needs terms
confirmed in writing.

Production use additionally requires registered API credentials; the unauthenticated
endpoint used in `scripts/fetch_corpus.py` is for research snapshots.

## Consequence for deployment

`data/processed/duas.json` is committed for reproducibility and is fine to use in
a local or academic setting. **Do not deploy a public instance until both blockers
are cleared.** The engineering work is complete and the service runs locally; only
the data licence stands between this and a public release.

## What is safe to ship now

- All code in `apps/web/` and `ml/src/` (MIT, see `LICENSE`).
- The controlled vocabulary in `data/ontology/` — original work.
- The query set in `data/evaluation/` — original work.
- Aggregate, non-extractive metrics from `docs/EXPERIMENTS.md`.
