"""Fetch full chapter-level detail from the Hisn al-Muslim API (segments + references).

The book-level list endpoint omits segments, so chapter detail must be requested
individually. Snapshots into data/raw/hisnul_chapters.json.

Usage:  python scripts/fetch_hisnul_chapters.py
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BASE = "https://dua-api.hisnul.workers.dev"
UA = "DuaWise-research/1.0 (academic dua retrieval study)"


def get(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - retry any transport error
            if attempt == 3:
                raise RuntimeError(f"failed {url}: {exc}") from exc
            time.sleep(1.2 * (attempt + 1))
    raise AssertionError("unreachable")


def main() -> int:
    books = json.loads((RAW / "hisnul_source.json").read_text(encoding="utf-8"))["books"]
    out: dict[str, object] = {"fetched_at": datetime.now(timezone.utc).isoformat(), "books": []}
    total = 0
    for book in books:
        bid = book["book_id"]
        chapters: list[dict] = []
        for meta in book["chapters"]:
            cid = meta["chap_id"]
            payload = get(f"{BASE}/api/books/{bid}/chapters/{cid}/duas?page=1&limit=100")
            duas = payload.get("data") or []
            total += len(duas)
            chapters.append(
                {
                    "chap_id": cid,
                    "chapname_bn": meta["chapname"],
                    "dua_count": meta["dua_count"],
                    "duas": duas,
                }
            )
            time.sleep(0.15)
        out["books"].append({"book_id": bid, "chapters": chapters})
        print(f"book {bid}: {len(chapters)} chapters, running total {total} duas")
    body = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True)
    (RAW / "hisnul_chapters.json").write_text(body + "\n", encoding="utf-8")
    print(f"wrote data/raw/hisnul_chapters.json  sha256={hashlib.sha256(body.encode()).hexdigest()[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())