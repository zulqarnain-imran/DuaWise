"""Fetch immutable source snapshots into data/raw/.

Sources
-------
Quran.com API v4 (no auth)  -> authentic Uthmani Arabic + Saheeh International translation
dua-api.hisnul.workers.dev  -> Hisn al-Muslim / Quranic duas: Arabic + hadith reference (MIT)

Design rules (docs/SPEC.md sections 3 and 7):
  * Sources are snapshotted once. Nothing in the experiment loop calls the network.
  * A manifest records URL, fetch time and content hash so a run can be traced to exact bytes.
  * Nothing is normalised destructively. Arabic diacritics are preserved verbatim.

Usage:  python scripts/fetch_corpus.py
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

HISNUL_BASE = "https://dua-api.hisnul.workers.dev"
QURAN_VERSE_URL = "https://api.quran.com/api/v4/verses/by_key/{key}"
SAHEEH_TRANSLATION_ID = 20  # Saheeh International

USER_AGENT = "DuaWise-research/1.0 (academic dua retrieval study)"

# Quranic verses treated as duas. Choice of verse is ours; wording is never ours.
QURAN_DUA_VERSES: list[str] = [
    # protection / refuge
    "2:255",  # Ayat al-Kursi
    "3:173",
    "7:23",
    "9:51",
    "12:53",
    "39:53",
    "40:7",
    "40:60",
    "41:10",
    "41:38",
    "66:8",
    "3:155",
    "3:173",
    "16:127",
    # hardship / patience / ease
    "2:152",
    "2:153",
    "2:155",
    "2:201",
    "2:214",
    "2:286",
    "3:139",
    "3:144",
    "3:146",
    "3:147",
    "3:188",
    "8:10",
    "12:87",
    "12:88",
    "20:115",
    "20:116",
    "20:121",
    "21:83",
    "21:87",
    "65:2",
    "65:3",
    "94:5",
    "94:6",
    # anxiety / sadness / grief
    "2:250",
    "3:159",
    "6:17",
    "10:57",
    "20:114",
    "20:119",
    "93:3",
    "93:5",
    "93:6",
    # provision / livelihood / debt
    "2:268",
    "28:24",
    "29:60",
    "51:22",
    "51:58",
    # knowledge / study
    "18:10",
    "20:114",
    "24:35",
    "25:63",
    "38:24",
    "39:9",
    # forgiveness / repentance
    "2:222",
    "23:118",
    "25:70",
    "39:53",
    "51:10",
    "71:10",
    "71:11",
    "71:12",
    # marriage / family / children
    "2:127",
    "2:186",
    "2:187",
    "18:24",
    "25:65",
    "25:74",
    "20:114",
    # illness / healing
    "3:8",
    "3:169",
    "17:33",
    "26:84",
    "52:48",
    "59:8",
    # fear / exam / journey
    "2:255",
    "20:114",
    "29:69",
    "62:10",
    # death / loss
    "2:156",
    "3:169",
    "3:185",
    "9:21",
    "35:41",
    # gratitude / praise
    "2:172",
    "14:7",
    "16:18",
    "27:40",
    "31:12",
    "34:26",
    "39:53",
    "40:15",
    "55:13",
    # guidance / understanding
    "1:6",
    "2:114",
    "6:80",
    "20:114",
    "39:22",
    "41:44",
    "45:37",
]


def http_get_json(url: str, timeout: int = 30) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed after 3 attempts: {url} ({last})")


def strip_footnotes(text: str) -> str:
    """Remove Saheeh International footnote markers such as <sup foot_note=1>1</sup>."""
    import re

    text = re.sub(r"<sup[^>]*>.*?</sup>", "", text)
    return text.strip()


def fetch_quran() -> dict[str, Any]:
    keys = sorted(set(QURAN_DUA_VERSES))
    verses: list[dict[str, Any]] = []
    for key in keys:
        url = QURAN_VERSE_URL.format(key=key) + (
            f"?language=en&words=false&translations={SAHEEH_TRANSLATION_ID}"
            "&fields=text_uthmani"
        )
        verse = http_get_json(url).get("verse") or {}
        translations = verse.get("translations") or []
        english = next(
            (strip_footnotes(t["text"]) for t in translations if t.get("resource_id") == SAHEEH_TRANSLATION_ID),
            None,
        )
        if not verse.get("text_uthmani") or not english:
            print(f"  ! incomplete verse {key}, skipped")
            continue
        surah, ayah = key.split(":")
        verses.append(
            {
                "verse_key": key,
                "surah": int(surah),
                "ayah": int(ayah),
                "arabic": verse["text_uthmani"],
                "translation": english,
                "translation_attribution": "Saheeh International (resource 20), via Quran.com API v4",
                "juz": verse.get("juz_number"),
                "page": verse.get("page_number"),
                "source_url": url,
            }
        )
        print(f"  verse {key} ok")
    return {"verses": verses}


def fetch_hisnul_book(book_id: int) -> dict[str, Any]:
    chapters = http_get_json(f"{HISNUL_BASE}/api/books/{book_id}/chapters").get("data") or []
    duas: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = http_get_json(f"{HISNUL_BASE}/api/books/{book_id}/duas?page={page}&limit=100")
        batch = payload.get("data") or []
        duas.extend(batch)
        pages = (payload.get("pagination") or {}).get("pages") or 1
        if page >= pages:
            break
        page += 1
    return {"book_id": book_id, "chapters": chapters, "duas": duas}


def fetch_hisnul() -> dict[str, Any]:
    books = [fetch_hisnul_book(b) for b in (1, 2, 3)]
    return {"books": books}


def write_snapshot(name: str, payload: Any) -> str:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / name
    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(body + "\n", encoding="utf-8")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).isoformat()
    print("Fetching Quran.com v4 verses ...")
    quran = fetch_quran()
    print(f"  {len(quran['verses'])} verses")
    print("Fetching Hisn al-Muslim API ...")
    hisnul = fetch_hisnul()
    total = sum(len(b["duas"]) for b in hisnul["books"])
    print(f"  {total} duas across {len(hisnul['books'])} books")

    manifest = {
        "fetched_at": fetched_at,
        "sources": {
            "quran": {
                "base": QURAN_VERSE_URL,
                "translation_id": SAHEEH_TRANSLATION_ID,
                "verse_count": len(quran["verses"]),
            },
            "hisnul": {"base": HISNUL_BASE, "dua_count": total},
        },
        "sha256": {
            "quran_duas_source.json": write_snapshot("quran_duas_source.json", quran),
            "hisnul_source.json": write_snapshot("hisnul_source.json", hisnul),
        },
        "licensing": {
            "quran": "Quran text and Saheeh International translation retrieved via Quran.com API v4. Redistribution terms must be checked with Quran Foundation before release (docs/SPEC.md 7.1).",
            "hisnul": "dua-api.hisnul.workers.dev, MIT licensed code; religious text asserted public domain by upstream, NOT independently verified (docs/SPEC.md 7.1).",
        },
        "review_status": "UNVERIFIED. Arabic text must be checked against printed sources and translations reviewed by a qualified scholar before any public release.",
    }
    (RAW / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote data/raw/MANIFEST.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())