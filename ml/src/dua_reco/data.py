"""Corpus, ontology and query loading."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .config import Settings

LABEL_SETS = ("situations", "emotions", "intentions", "occasions", "topics")


def _read(path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


@dataclass(frozen=True)
class Dua:
    dua_id: str
    title: str
    arabic: str
    translation: str
    source_work: str
    source_reference: str
    hadith_reference: str | None
    reference_status: str
    situations: frozenset[str]
    emotions: frozenset[str]
    intentions: frozenset[str]
    occasions: frozenset[str]
    topics: frozenset[str]
    time_context: str
    recitation_count: int | None
    review_states: dict[str, str]
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def retrieval_text(self) -> str:
        """Text used for the retrieval embedding.

        Deliberately excludes the context labels. If they were included, the
        semantic baseline would already carry structured-context information and
        the M2 -> M4 comparison would no longer isolate the context contribution.
        """
        parts = [self.title, self.translation]
        if self.hadith_reference:
            parts.append("")
        return " ".join(p for p in parts if p).strip()

    @property
    def label_dict(self) -> dict[str, frozenset[str]]:
        return {
            "situations": self.situations,
            "emotions": self.emotions,
            "intentions": self.intentions,
            "occasions": self.occasions,
            "topics": self.topics,
        }


@dataclass(frozen=True)
class Query:
    query_id: str
    text: str
    gold_relevance: dict[str, int]
    implied_occasion: str | None
    lexical_mismatch: bool
    ambiguous: bool
    intended_context: dict[str, list[str]]

    @property
    def relevant_ids(self) -> set[str]:
        return {k for k, v in self.gold_relevance.items() if v > 0}


class Corpus:
    def __init__(self, duas: list[Dua], meta: dict[str, Any]):
        self.duas = duas
        self.meta = meta
        self.by_id = {d.dua_id: d for d in duas}

    def __len__(self) -> int:
        return len(self.duas)

    def __iter__(self):
        return iter(self.duas)


def load_corpus(cfg: Settings | None = None) -> Corpus:
    from .config import settings as default_settings

    cfg = cfg or default_settings
    payload = _read(cfg.corpus_path)
    duas = [
        Dua(
            dua_id=d["dua_id"],
            title=d["title"],
            arabic=d["arabic"],
            translation=d["translation"],
            source_work=d["source_work"],
            source_reference=d["source_reference"],
            hadith_reference=d.get("hadith_reference"),
            reference_status=d["reference_status"],
            situations=frozenset(d["situations"]),
            emotions=frozenset(d["emotions"]),
            intentions=frozenset(d["intentions"]),
            occasions=frozenset(d["occasions"]),
            topics=frozenset(d["topics"]),
            time_context=d.get("time_context", "anytime"),
            recitation_count=d.get("recitation_count"),
            review_states=d.get("review_states", {}),
            raw=d,
        )
        for d in payload["duas"]
    ]
    return Corpus(duas, {k: v for k, v in payload.items() if k != "duas"})


def load_queries(cfg: Settings | None = None) -> list[Query]:
    from .config import settings as default_settings

    cfg = cfg or default_settings
    payload = _read(cfg.queries_path)
    return [
        Query(
            query_id=q["query_id"],
            text=q["text"],
            gold_relevance=q["gold_relevance"],
            implied_occasion=q.get("implied_occasion"),
            lexical_mismatch=bool(q.get("lexical_mismatch")),
            ambiguous=bool(q.get("ambiguous")),
            intended_context=q.get("intended_context", {}),
        )
        for q in payload["queries"]
    ]


def load_ontology(cfg: Settings | None = None) -> dict[str, list[dict[str, Any]]]:
    from .config import settings as default_settings

    cfg = cfg or default_settings
    payload = _read(cfg.ontology_path)
    return {k: payload[k] for k in LABEL_SETS}


_PROBE_CACHE: dict[str, dict[str, dict[str, str]]] = {}


def load_label_texts(cfg: Settings | None = None) -> dict[str, dict[str, str]]:
    """Natural-language probe for each ontology term, used by the zero-shot classifier.

    A term's probe is built from its definition plus its include/exclude examples,
    so the classifier sees the annotation guide's wording rather than the bare slug.

    Cached on the ontology path rather than on ``Settings``: Settings holds a dict
    and is therefore unhashable, so lru_cache on the config object raises.
    """
    from .config import settings as default_settings

    cfg = cfg or default_settings
    cache_key = str(cfg.ontology_path)
    if cache_key in _PROBE_CACHE:
        return _PROBE_CACHE[cache_key]

    ontology = load_ontology(cfg)
    out: dict[str, dict[str, str]] = {}
    for label_set, terms in ontology.items():
        probes: dict[str, str] = {}
        for term in terms:
            bits = [term["definition"]]
            if term.get("includes"):
                bits.append("For example: " + ", ".join(term["includes"]) + ".")
            if term.get("excludes"):
                bits.append("Not for: " + ", ".join(term["excludes"]) + ".")
            probes[term["term_id"]] = " ".join(bits)
        out[label_set] = probes
    _PROBE_CACHE[cache_key] = out
    return out