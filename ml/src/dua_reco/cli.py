"""Command line interface: index, recommend, evaluate, tune, context."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import settings
from .data import load_queries
from .embeddings import Encoder
from .evaluate import evaluate, evaluate_query, paired_bootstrap, stratified_split, wilcoxon_signed_rank
from .explain import explain_all
from .retrieval import Recommender
from .tuning import coordinate_ascent, save_tuning


def _utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _dump(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _recommender(cfg=settings) -> Recommender:
    return Recommender(encoder=Encoder(cfg), cfg=cfg)


def cmd_index(args: argparse.Namespace) -> int:
    recommender = _recommender()
    _dump({
        "corpus_size": len(recommender.duas),
        "embedding_model": recommender.encoder.model_name,
        "fallback_encoder": recommender.encoder.using_fallback,
        "embedding_dim": int(recommender.embedding_matrix.shape[1]),
        "tfidf_features": int(recommender.tfidf_matrix.shape[1]),
        "artifact": str(settings.embedding_cache),
        "corpus_meta": recommender.corpus.meta,
    })
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    recommender = _recommender()
    results, context = recommender.recommend(
        args.query,
        args.k,
        occasion=args.occasion,
        favourites=frozenset(args.favourite or ()),
    )
    payload = {
        "query": args.query,
        "extracted_context": context.to_dict(),
        "results": [r.as_dict() for r in results],
        "explanations": explain_all(results, context),
        "weights": recommender.weights,
        "disclaimer": (
            "DuaWise surfaces Duas from cited sources for personal reflection. "
            "It does not generate religious text or issue rulings."
        ),
    }
    if args.explain_only:
        _dump(payload["explanations"])
    else:
        _dump(payload)
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    recommender = _recommender()
    for text in args.text:
        context = recommender.extract_context(text, args.occasion)
        _dump({"text": text, **context.to_dict()})
    return 0


def _metrics(recommender: Recommender, queries, model: str, k: int) -> tuple[dict, list[float]]:
    def rank(text: str, n: int) -> list[str]:
        return [r.dua.dua_id for r in recommender.rank(model, text, n)]

    metrics = evaluate(queries, rank, k=k, exclude_ambiguous=True)
    per_query = [
        evaluate_query(q, rank(q.text, k), k).ndcg
        for q in queries
        if not q.ambiguous
    ]
    return metrics, per_query


def cmd_evaluate(args: argparse.Namespace) -> int:
    recommender = _recommender()
    queries = load_queries()
    train, validation = stratified_split(queries, settings.validation_fraction, settings.seed)

    # The headline number must be the held-out split. Scoring the full set after
    # tuning on part of it is optimistic, so both are reported side by side.
    subsets = {
        "validation_heldout": validation,
        "train_tuned": train,
        "all": queries,
    }
    selected = subsets[args.split]

    rows: dict[str, dict] = {}
    per_query: dict[str, list[float]] = {}
    for model in args.models:
        metrics, ndcgs = _metrics(recommender, selected, model, args.k)
        rows[model] = metrics
        per_query[model] = ndcgs

    comparison = None
    if "M2" in per_query and "M4" in per_query and len(per_query["M2"]) == len(per_query["M4"]):
        comparison = {
            "M4_vs_M2": paired_bootstrap(per_query["M4"], per_query["M2"], seed=settings.seed),
            "M4_vs_M2_wilcoxon": wilcoxon_signed_rank(
                [x - y for x, y in zip(per_query["M4"], per_query["M2"])]
            ),
        }
        if "M3" in per_query:
            comparison["M4_vs_M3"] = paired_bootstrap(
                per_query["M4"], per_query["M3"], seed=settings.seed
            )
        if "M1" in per_query:
            comparison["M4_vs_M1"] = paired_bootstrap(
                per_query["M4"], per_query["M1"], seed=settings.seed
            )

    payload = {
        "split": args.split,
        "k": args.k,
        "query_count": len(selected),
        "excluded_ambiguous": sum(1 for q in selected if q.ambiguous),
        "embedding_model": recommender.encoder.model_name,
        "fallback_encoder": recommender.encoder.using_fallback,
        "weights": recommender.weights,
        "weights_tuned": recommender.tuned_weights is not None,
        "results": rows,
        "significance": comparison,
        "caveats": [
            "Gold relevance labels are derived from the same draft annotations the "
            "context features use, so M4 is advantaged by construction.",
            "These numbers measure internal consistency and are not expert-validated.",
            "Only the 'validation_heldout' split is free of tuning bias.",
        ],
    }
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {args.out}")
    _dump(payload)
    return 0


def cmd_tune(args: argparse.Namespace) -> int:
    recommender = _recommender()
    queries = load_queries()
    train, validation = stratified_split(queries, settings.validation_fraction, settings.seed)
    logging.info("train seeds=%d queries=%d | validation queries=%d",
                 len({q.query_id.split('p')[0] for q in train}), len(train), len(validation))

    weights, history = coordinate_ascent(recommender, train, args.k, rounds=args.rounds)
    train_metrics, _ = _metrics(recommender, train, "M4", args.k)
    validation_metrics, _ = _metrics(recommender, validation, "M4", args.k)
    path = save_tuning(recommender, weights, history, train_metrics, validation_metrics)

    baseline_train, _ = _metrics(recommender, train, "M3", args.k)
    baseline_validation, _ = _metrics(recommender, validation, "M3", args.k)
    _dump({
        "tuned_weights": weights,
        "train": train_metrics,
        "validation": validation_metrics,
        "untuned_M3_train": baseline_train,
        "untuned_M3_validation": baseline_validation,
        "artifact": str(path),
    })
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dua-reco", description="DuaWise recommendation engine")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("index", help="build and inspect the retrieval index").set_defaults(func=cmd_index)

    rec = sub.add_parser("recommend", help="rank Duas for a free-text query")
    rec.add_argument("query")
    rec.add_argument("-k", type=int, default=settings.k)
    rec.add_argument("--occasion")
    rec.add_argument("--favourite", action="append", help="dua_id to boost; repeatable")
    rec.add_argument("--explain-only", action="store_true")
    rec.set_defaults(func=cmd_recommend)

    ctx = sub.add_parser("context", help="show extracted context labels for text")
    ctx.add_argument("text", nargs="+")
    ctx.add_argument("--occasion")
    ctx.set_defaults(func=cmd_context)

    ev = sub.add_parser("evaluate", help="score M1-M4 on the query set")
    ev.add_argument("--k", type=int, default=settings.k)
    ev.add_argument("--models", nargs="+", default=["M1", "M2", "M3", "M4"])
    ev.add_argument(
        "--split",
        choices=["validation_heldout", "train_tuned", "all"],
        default="validation_heldout",
        help="held-out seeds are the honest headline number",
    )
    ev.add_argument("--out")
    ev.set_defaults(func=cmd_evaluate)

    tune = sub.add_parser("tune", help="tune M4 fusion weights on the training split")
    tune.add_argument("--k", type=int, default=settings.k)
    tune.add_argument("--rounds", type=int, default=3)
    tune.set_defaults(func=cmd_tune)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Arabic text raises UnicodeEncodeError on the default Windows console codec,
    # so reconfigure both streams before any output is produced.
    _utf8()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
