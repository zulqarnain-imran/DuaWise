"""Build the evaluation query set with graded relevance labels.

Gold labels are DERIVED from the corpus context annotations, not independently
assigned. That circularity is real and is disclosed in docs/EXPERIMENTS.md: it
inflates the context-aware model. The independent check is expert evaluation.

Grading rule
------------
For a query with situations S, emotions E, intentions I:
  grade 3 - the dua carries the query's primary situation AND its primary
            intention, and its occasion is compatible.
  grade 2 - the dua carries the query's primary situation only, or a secondary
            intention with a matching emotion.
  grade 1 - the dua shares only an emotion or a topic with the query.
  grade 0 - not relevant (implicit).

Usage:  python scripts/build_queryset.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "data" / "evaluation"
OUT = ROOT / "data" / "processed"

LABEL_SETS = ("situations", "emotions", "intentions", "occasions", "topics")
TYPO_FIX = {"death_of_lived_one": "death_of_loved_one"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def grade(query: dict, dua: dict) -> int:
    """Graded relevance. Requires genuine situation overlap for grade >= 1.

    An earlier permissive version graded on emotion+topic alone and produced ~73
    gold items per query out of a 358-record corpus, which saturates NDCG for
    every model and measures nothing.
    """
    q_sit = set(query["situations"])
    q_occ = {query["occasion"]} if query.get("occasion") else set()

    # An occasion-driven query ("it's Friday, what should I recite") carries no real
    # situation signal. Grading it by situation matches every record labelled "general"
    # and produces a degenerate gold set, so grade it on occasion compatibility instead.
    if q_sit <= {"general"} and q_occ:
        # Only duas explicitly tagged with the occasion count. Treating "general"
        # as a grade-2 match made ~274 of 358 records relevant, which is degenerate.
        return 3 if q_occ & set(dua["occasions"]) else 0

    q_sit_secondary = set(query.get("secondary_situations", []))
    q_emo = set(query["emotions"])
    q_int = set(query["intentions"])
    q_int_secondary = set(query.get("secondary_intentions", []))

    d_sit = set(dua["situations"])
    d_emo = set(dua["emotions"])
    d_int = set(dua["intentions"])
    d_occ = set(dua["occasions"])

    sit_primary = q_sit & d_sit
    sit_secondary = q_sit_secondary & d_sit
    int_primary = q_int & d_int
    int_secondary = q_int_secondary & d_int
    emo_match = q_emo & d_emo
    occ_compatible = (not q_occ) or bool(q_occ & d_occ) or "general" in d_occ

    if sit_primary and int_primary and occ_compatible:
        return 3
    if (sit_primary and (emo_match or int_secondary)) or (sit_secondary and (int_primary or emo_match)):
        return 2
    if (sit_secondary or int_secondary) and occ_compatible:
        return 1
    if sit_primary and not occ_compatible:
        return 1
    return 0


def main() -> int:
    corpus = load(OUT / "duas.json")
    ontology = load(ROOT / "data" / "ontology" / "ontology.json")
    allowed = {k: {t["term_id"] for t in ontology[k]} for k in LABEL_SETS}
    seed = load(EVAL / "query_seed.json")
    paraphrases = load(EVAL / "query_paraphrases.json")["paraphrases"]

    duas = corpus["duas"]
    queries: list[dict] = []

    for raw in seed["queries"]:
        base = dict(raw)
        for field in ("situations", "emotions", "intentions"):
            base[field] = [TYPO_FIX.get(t, t) for t in base.get(field, [])]
        for field in LABEL_SETS:
            for term in base.get(field, []):
                if term not in allowed[field]:
                    print(f"  ! {base['qid']}: '{term}' invalid {field}")
                    return 1

        variants = [(base["qid"], base["text"], base)] + [
            (f"{base['qid']}p{i}", text, base) for i, text in enumerate(paraphrases.get(base["qid"], []), start=1)
        ]

        for qid, text, template in variants:
            gold: dict[str, int] = {}
            for dua in duas:
                g = grade(template, dua)
                if g > 0:
                    gold[dua["dua_id"]] = g
            if not gold:
                print(f"  ! {qid}: no gold labels derived, skipped")
                continue
            queries.append(
                {
                    "query_id": qid,
                    "text": text,
                    "seed_id": base["qid"],
                    "is_paraphrase": qid != base["qid"],
                    "implied_occasion": template.get("occasion"),
                    "lexical_mismatch": bool(template.get("lexical_mismatch")),
                    "ambiguous": bool(template.get("ambiguous")),
                    "intended_context": {
                        "situations": template.get("situations", []),
                        "emotions": template.get("emotions", []),
                        "intentions": template.get("intentions", []),
                    },
                    "gold_relevance": dict(sorted(gold.items())),
                    "label_source": "derived_from_draft_annotations",
                }
            )

    graded = [len(q["gold_relevance"]) for q in queries]
    payload = {
        "version": "1.0.0",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "corpus_version": corpus["version"],
        "query_count": len(queries),
        "gold_source": "derived_from_draft_annotations",
        "expert_labelled": False,
        "limitations": [
            "Gold labels are derived from the same draft annotations the ranker consumes; this inflates context-aware models.",
            "No independent annotator has reviewed these queries or their gold labels.",
            "Annotator agreement (Cohen's kappa) has not been computed; the corpus labels are single-annotator.",
        ],
        "queries": queries,
    }
    (EVAL / "queries.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = {
        "query_count": len(queries),
        "base_queries": sum(1 for q in queries if not q["is_paraphrase"]),
        "paraphrases": sum(1 for q in queries if q["is_paraphrase"]),
        "lexical_mismatch": sum(1 for q in queries if q["lexical_mismatch"]),
        "ambiguous": sum(1 for q in queries if q["ambiguous"]),
        "with_occasion": sum(1 for q in queries if q["implied_occasion"]),
        "mean_gold_per_query": round(sum(graded) / max(len(graded), 1), 2),
        "min_gold": min(graded),
        "max_gold": max(graded),
        "queries_with_no_grade3": sum(1 for q in queries if 3 not in q["gold_relevance"].values()),
    }
    (EVAL / "QUERY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    print("wrote data/evaluation/queries.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())