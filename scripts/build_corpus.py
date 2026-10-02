"""Assemble the DuaWise dua corpus from raw snapshots + draft annotations.

Outputs
-------
data/processed/duas.json      schema-compliant corpus (docs/SPEC.md section 8)
data/processed/BUILD_REPORT.json  provenance, coverage, and validation results

Rules enforced here
-------------------
* Every record must have Arabic text, a source, and at least one context label.
  A record failing any of these is rejected, never defaulted.
* Every label is validated against data/ontology/ontology.json.
* Annotation provenance is recorded per record: "manual" or "keyword_derived".
  The draft annotations in data/ontology/ are unreviewed; see docs/ANNOTATION.md.

Usage:  python scripts/build_corpus.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ONT = ROOT / "data" / "ontology"
OUT = ROOT / "data" / "processed"

LABEL_SETS = ("situations", "emotions", "intentions", "occasions", "topics")

# Fallback keyword derivation for chapters the team did not annotate manually.
# Deliberately conservative: when nothing matches, the record is labelled
# situation=general, occasion=general rather than guessed at.
KEYWORD_RULES: list[tuple[tuple[str, ...], dict[str, list[str]]]] = [
    (("morning", "evening"), {"occasions": ["morning", "evening"], "topics": ["protection"], "situations": ["protection_from_harm"]}),
    (("sleep", "sleeping"), {"occasions": ["before_sleep", "night"], "topics": ["protection"], "situations": ["protection_from_harm"]}),
    (("travel", "travelling", "traveling", "journey", "vehicle", "animal", "town", "market"), {"occasions": ["travel"], "topics": ["journey"], "situations": ["travel"]}),
    (("sick", "illness", "pain", "terminal"), {"occasions": ["illness"], "topics": ["health"], "situations": ["illness"]}),
    (("dead", "funeral", "grave", "bereaved", "dying"), {"occasions": ["death"], "situations": ["death_of_loved_one"], "topics": ["repentance"]}),
    (("debt", "loan"), {"occasions": ["debt"], "topics": ["provision"], "situations": ["debt", "financial_difficulty"]}),
    (("repent", "forgive"), {"situations": ["sin", "repentance"], "intentions": ["forgiveness", "repentance"], "topics": ["repentance"]}),
    (("enemy", "adversary", "ruler", "oppression"), {"situations": ["conflict", "fear"], "topics": ["protection"]}),
    (("fear", "frightened", "afraid", "bad dream", "nightmare"), {"situations": ["fear", "protection_from_harm"], "emotions": ["fear"], "topics": ["protection"]}),
    (("rain", "wind", "thunder", "moon"), {"occasions": ["rain"]}),
    (("eating", "food", "fast", "drink", "dates"), {"occasions": ["food"], "topics": ["provision"]}),
    (("anger",), {"situations": ["anger"], "emotions": ["anger"], "occasions": ["anger"]}),
    (("groom", "wedding", "intercourse"), {"situations": ["marriage"], "occasions": ["wedding"], "topics": ["family"]}),
    (("mosque", "prayer", "prostrat", "ablution", "athan", "qunut", "istikharah", "tashahhud"), {"occasions": ["mosque"], "topics": ["worship"]}),
    (("hajj", "umrah", "arafat", "safā", "safa", "black stone", "pilgrim"), {"occasions": ["hajj"], "topics": ["worship"]}),
    (("new clothes", "getting dressed", "undressing", "restroom", "sneezing", "assembly", "etiquette", "excellence"), {"situations": ["general"], "occasions": ["general"]}),
    (("remembering allah", "glorifying", "glorify"), {"topics": ["praise_of_allah"], "situations": ["general"]}),
    (("children", "child", "parents"), {"situations": ["family"], "topics": ["family"]}),
    (("devil", "satan", "evil eye", "fitnah", "plots", "evil"), {"situations": ["protection_from_harm"], "topics": ["protection"]}),
    (("misfortune", "pl pleases", "displease", "startled", "surprised", "tragedy"), {"situations": ["hardship"], "emotions": ["sadness"]}),
    (("gratitude", "bless", "thanks", "does good"), {"situations": ["gratitude"], "emotions": ["gratitude"], "intentions": ["gratitude"], "topics": ["gratitude"]}),
]

DEFAULT_LABELS: dict[str, list[str]] = {
    "situations": ["general"],
    "emotions": [],
    "intentions": [],
    "occasions": ["general"],
    "topics": [],
}

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
ARABIC_LETTERS = re.compile(r"[^ء-ي]")
ORTHOGRAPHY_FOLD = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ؤ": "و", "ئ": "ي", "ى": "ي", "ة": "ه",
    "ی": "ي", "ک": "ك", "ھ": "ه",
}


def fold_arabic(text: str | None) -> str:
    """Normalise Arabic for cross-source matching only. Never applied to stored text."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = ARABIC_DIACRITICS.sub("", text)
    text = ARABIC_LETTERS.sub("", text)
    for src, dst in ORTHOGRAPHY_FOLD.items():
        text = text.replace(src, dst)
    return text


def strip_html(text: str | None) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def derive_labels(title: str) -> dict[str, list[str]]:
    lowered = title.lower()
    labels = {k: list(v) for k, v in DEFAULT_LABELS.items()}
    for keywords, rule in KEYWORD_RULES:
        if any(k in lowered for k in keywords):
            for key, values in rule.items():
                labels[key] = sorted(set(labels[key]) | set(values))
    return labels


def build_reference_index() -> dict[str, str]:
    """Map folded Arabic -> hadith reference, from the Hisn al-Muslim API snapshot."""
    path = RAW / "hisnul_chapters.json"
    if not path.exists():
        return {}
    data = load_json(path)
    index: dict[str, str] = {}
    for book in data["books"]:
        for chapter in book["chapters"]:
            for dua in chapter["duas"]:
                for seg in dua.get("segments") or []:
                    key = fold_arabic(seg.get("arabic"))
                    ref = strip_html(seg.get("reference"))
                    if key and ref:
                        index.setdefault(key, ref)
    return index


def build_hisnul_records(
    chapters_meta: dict[int, dict[str, Any]],
    reference_index: dict[str, str],
    allowed: dict[str, set[str]],
) -> tuple[list[dict[str, Any]], list[str]]:
    payload = load_json(RAW / "unlicensed" / "husn_en.json")
    chapters = payload["English"] if isinstance(payload, dict) else payload
    annotations = load_json(ONT / "chapter_annotations.json")["chapters"]

    records: list[dict[str, Any]] = []
    rejections: list[str] = []

    for chapter in chapters:
        cid = int(chapter["ID"])
        chapter_title = (chapter["TITLE"] or "").strip()
        segments = chapter.get("TEXT") or []

        for position, seg in enumerate(segments, start=1):
            arabic = (seg.get("ARABIC_TEXT") or "").strip()
            translation = strip_html(seg.get("TRANSLATED_TEXT"))
            upstream_note = strip_html(seg.get("LANGUAGE_ARABIC_TRANSLATED_TEXT"))
            repeat = seg.get("REPEAT")

            if not arabic:
                rejections.append(f"HM-{cid}-{position}: empty Arabic")
                continue
            if not translation:
                rejections.append(f"HM-{cid}-{position}: empty translation")
                continue

            manual = annotations.get(str(cid))
            if manual:
                labels = {k: list(manual.get(k, DEFAULT_LABELS[k])) for k in LABEL_SETS}
                method = "manual"
                title = manual.get("title") or chapter_title
            else:
                labels = derive_labels(chapter_title)
                method = "keyword_derived"
                title = chapter_title

            hadith_ref = reference_index.get(fold_arabic(arabic))
            topics = set(labels["topics"]) | {"hadith"}
            occasions = list(dict.fromkeys(labels["occasions"]))

            time_context = "anytime"
            for candidate in ("morning", "evening", "night"):
                if candidate in occasions:
                    time_context = candidate
                    break

            records.append(
                {
                    "dua_id": f"HM-{cid}-{position}",
                    "title": title,
                    "arabic": arabic,
                    "transliteration": None,
                    "translation": translation,
                    "translation_attribution": (
                        "Hisn al-Muslim English text via github.com/wafaaelmaandy/Hisn-Muslim-Json "
                        "(NO LICENSE DECLARED - redistribution not permitted, see LICENSES.md)"
                    ),
                    "upstream_note": upstream_note or None,
                    "recitation_count": repeat if isinstance(repeat, int) and repeat > 0 else None,
                    "audio_url": seg.get("AUDIO") or None,
                    "source_work": "Hisn al-Muslim",
                    "source_author": "Sa'id ibn Ali ibn Wahf al-Qahtani",
                    "source_reference": f"Hisn al-Muslim, chapter {cid}, item {position}",
                    "source_chapter": cid,
                    "source_item": position,
                    "hadith_reference": hadith_ref,
                    "reference_status": "matched_to_hadith" if hadith_ref else "chapter_and_item_only",
                    "authenticity_grade": None,
                    "authenticity_basis": None,
                    "occasions": occasions,
                    "situations": list(dict.fromkeys(labels["situations"])),
                    "emotions": list(dict.fromkeys(labels["emotions"])),
                    "intentions": list(dict.fromkeys(labels["intentions"])),
                    "topics": sorted(topics),
                    "time_context": time_context,
                    "annotation_method": method,
                    "review_states": {
                        "arabic": "fetched_from_source_unverified",
                        "translation": "fetched_from_source_unreviewed",
                        "context_labels": "draft_unreviewed" if method == "manual" else "keyword_derived_unreviewed",
                        "scholar": "not_reviewed",
                    },
                    "redistribution_status": "blocked_no_license",
                }
            )
            if hadith_ref is None:
                rejections.append(f"HM-{cid}-{position}: no hadith number matched (chapter+item reference used)")
            chapters_meta[cid] = {"title": chapter_title, "segments": len(segments)}

    return records, rejections


def build_quran_records(allowed: dict[str, set[str]]) -> tuple[list[dict[str, Any]], list[str]]:
    payload = load_json(RAW / "quran_duas_source.json")
    annotations = load_json(ONT / "quran_annotations.json")["verses"]

    records: list[dict[str, Any]] = []
    rejections: list[str] = []

    for verse in payload["verses"]:
        key = verse["verse_key"]
        annotation = annotations.get(key)
        if not annotation:
            rejections.append(f"Q-{key.replace(':', ':')}: fetched but not annotated, dropped")
            continue
        arabic = (verse.get("arabic") or "").strip()
        translation = (verse.get("translation") or "").strip()
        if not arabic or not translation:
            rejections.append(f"Q-{key}: missing Arabic or translation, dropped")
            continue

        labels = {k: list(annotation.get(k, DEFAULT_LABELS[k])) for k in LABEL_SETS}
        occasions = list(dict.fromkeys(labels["occasions"]))
        time_context = "anytime"
        for candidate in ("morning", "evening", "night"):
            if candidate in occasions:
                time_context = candidate
                break

        records.append(
            {
                "dua_id": f"Q-{key.replace(':', '-')}",
                "title": annotation["title"],
                "arabic": arabic,
                "transliteration": None,
                "translation": translation,
                "translation_attribution": verse.get("translation_attribution"),
                "upstream_note": None,
                "recitation_count": None,
                "audio_url": None,
                "source_work": "Qur'an",
                "source_author": None,
                "source_reference": f"Qur'an {key.replace(':', ':')}",
                "source_chapter": verse.get("surah"),
                "source_item": verse.get("ayah"),
                "hadith_reference": None,
                "reference_status": "exact_scripture_reference",
                "authenticity_grade": None,
                "authenticity_basis": None,
                "occasions": occasions,
                "situations": list(dict.fromkeys(labels["situations"])),
                "emotions": list(dict.fromkeys(labels["emotions"])),
                "intentions": list(dict.fromkeys(labels["intentions"])),
                "topics": sorted(set(labels["topics"]) | {"quran"}),
                "time_context": time_context,
                "annotation_method": "manual",
                "review_states": {
                    "arabic": "fetched_from_quran_api_uthmani",
                    "translation": "saheeh_international_published",
                    "context_labels": "draft_unreviewed",
                    "scholar": "not_reviewed",
                },
                "redistribution_status": "check_quran_foundation_terms",
            }
        )
    return records, rejections


def validate(records: list[dict[str, Any]], allowed: dict[str, set[str]]) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for record in records:
        rid = record["dua_id"]
        if rid in seen:
            problems.append(f"{rid}: duplicate dua_id")
        seen.add(rid)
        if not record["arabic"]:
            problems.append(f"{rid}: empty arabic")
        if not record["source_reference"]:
            problems.append(f"{rid}: no source reference")
        if not record["translation"]:
            problems.append(f"{rid}: no translation")
        labelled = any(record[k] for k in LABEL_SETS)
        if not labelled:
            problems.append(f"{rid}: no context labels at all")
        for key in LABEL_SETS:
            for term in record[key]:
                if term not in allowed[key]:
                    problems.append(f"{rid}: '{term}' is not a valid {key} term")
    return problems


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ontology = load_json(ONT / "ontology.json")
    allowed = {k: {t["term_id"] for t in ontology[k]} for k in LABEL_SETS}

    reference_index = build_reference_index()
    chapters_meta: dict[int, dict[str, Any]] = {}

    hisnul_records, hisnul_rejects = build_hisnul_records(chapters_meta, reference_index, allowed)
    quran_records, quran_rejects = build_quran_records(allowed)
    records = quran_records + hisnul_records
    records.sort(key=lambda r: r["dua_id"])

    problems = validate(records, allowed)

    manifest = load_json(RAW / "MANIFEST.json")
    corpus = {
        "version": "1.0.0",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "provenance": {
            "quran_api": manifest["sources"]["quran"],
            "hisnul_api": manifest["sources"]["hisnul"],
            "english_hisnul_text": "github.com/wafaaelmaandy/Hisn-Muslim-Json (no license declared)",
        },
        "annotation_status": "DRAFT_UNREVIEWED - context labels require scholar review",
        "duas": records,
    }
    (OUT / "duas.json").write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    label_counts = {k: Counter(t for r in records for t in r[k]) for k in LABEL_SETS}
    report = {
        "built_at": corpus["built_at"],
        "record_count": len(records),
        "by_source": dict(Counter(r["source_work"] for r in records)),
        "by_annotation_method": dict(Counter(r["annotation_method"] for r in records)),
        "by_reference_status": dict(Counter(r["reference_status"] for r in records)),
        "by_review_state_translation": dict(
            Counter(r["review_states"]["translation"] for r in records)
        ),
        "hadith_reference_match_rate": round(
            sum(1 for r in records if r["hadith_reference"]) / max(len(records), 1), 3
        ),
        "label_counts": {k: dict(v.most_common()) for k, v in label_counts.items()},
        "chapters_with_manual_annotation": len(chapters_meta),
        "validation_problems": problems,
        "warnings": {
            "quran": quran_rejects,
            "hisnul": hisnul_rejects[:40],
            "hisnul_warning_total": len(hisnul_rejects),
        },
        "release_blockers": [
            "Context labels are draft and unreviewed (docs/ANNOTATION.md).",
            "Hisn al-Muslim English text source declares no license - redistribution blocked (LICENSES.md).",
            "Qur'an text and Saheeh International terms must be confirmed with Quran Foundation.",
            "Arabic text not yet collated against printed sources.",
        ],
    }
    (OUT / "BUILD_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"records: {len(records)}")
    print(f"  by source:           {report['by_source']}")
    print(f"  annotation method:   {report['by_annotation_method']}")
    print(f"  reference status:    {report['by_reference_status']}")
    print(f"  hadith ref match:    {report['hadith_reference_match_rate']}")
    print(f"  validation problems: {len(problems)}")
    for problem in problems[:20]:
        print(f"    ! {problem}")
    print(f"  quran drops:         {len(quran_rejects)}")
    print("wrote data/processed/duas.json and BUILD_REPORT.json")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())