"""One-off probe: inspect the real response shape of the source APIs.

Run:  python scripts/inspect_sources.py
"""

from __future__ import annotations

import json
import sys
import urllib.request

HISNUL_BASE = "https://dua-api.hisnul.workers.dev"
QURAN_BY_KEY = "https://api.quran.com/api/v4/verses/by_key/{key}"


def get_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "DuaWise-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    out: dict[str, object] = {}

    out["hisnul_books"] = get_json(f"{HISNUL_BASE}/api/books")

    chapters = get_json(f"{HISNUL_BASE}/api/books/1/chapters")
    out["hisnul_chapters_sample"] = {
        "shape": list(chapters.keys()),
        "pagination": chapters.get("pagination"),
        "first_two": (chapters.get("data") or [])[:2],
    }

    duas = get_json(f"{HISNUL_BASE}/api/books/1/chapters/1/duas")
    out["hisnul_chapter1_duas"] = {
        "total": duas.get("total"),
        "first": (duas.get("data") or [])[:1],
    }

    q = get_json(QURAN_BY_KEY.format(key="2:255") + "?language=en&words=false&translations=20")
    out["quran_verse"] = q.get("verse")

    dest = sys.argv[1] if len(sys.argv) > 1 else "data/raw/_probe.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())