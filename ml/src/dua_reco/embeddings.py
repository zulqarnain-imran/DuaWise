"""Sentence embeddings with on-disk caching.

The corpus embedding is computed once and reused. Nothing in the request path
downloads a model or re-encodes the corpus.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import numpy as np

from .config import Settings, settings as default_settings

log = logging.getLogger(__name__)

try:  # sentence-transformers is the intended path
    from sentence_transformers import SentenceTransformer

    _HAS_ST = True
except Exception as exc:  # pragma: no cover - exercised only in degraded installs
    log.warning("sentence-transformers unavailable (%s)", exc)
    _HAS_ST = False


def _embedding_dim(model: SentenceTransformer) -> int:
    """sentence-transformers renamed this accessor; support both without warning."""
    getter = getattr(model, "get_embedding_dimension", None) or model.get_sentence_embedding_dimension
    return int(getter())


class Encoder:
    """Wraps a sentence encoder. Falls back to a deterministic hashing encoder.

    The fallback exists so the evaluation harness still runs on machines without
    torch. It is NOT a semantic encoder: it gives high lexical overlap, which
    flatters the lexical baseline and depresses the semantic one. Any run using
    it is marked ``fallback_encoder`` in the experiment log.
    """

    def __init__(self, cfg: Settings | None = None, allow_fallback: bool = True):
        self.cfg = cfg or default_settings
        self.allow_fallback = allow_fallback
        self.model_name = self.cfg.embedding_model
        self.using_fallback = False
        self._model = None
        if _HAS_ST:
            self._model = SentenceTransformer(self.model_name)
            self.dim = _embedding_dim(self._model)
        elif allow_fallback:
            self.using_fallback = True
            self.dim = self.cfg.embedding_dim
            log.warning("using hashing fallback encoder - results are NOT semantically valid")
        else:
            raise RuntimeError("sentence-transformers is required but not installed")

    def encode(self, texts: list[str]) -> np.ndarray:
        if self._model is not None:
            return np.asarray(
                self._model.encode(
                    texts,
                    batch_size=self.cfg.embedding_batch_size,
                    normalize_embeddings=self.cfg.normalize_embeddings,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )
        return self._hash_encode(texts)

    def _hash_encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in text.lower().split():
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                index = int.from_bytes(digest, "big") % self.dim
                sign = 1.0 if digest[0] % 2 == 0 else -1.0
                out[row, index] += sign
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        np.divide(out, np.maximum(norms, 1e-9), out=out)
        return out


def build_or_load_corpus_matrix(
    encoder: Encoder, texts: list[str], cache_path: Path | None = None
) -> np.ndarray:
    cache_path = cache_path or encoder.cfg.embedding_cache
    key = hashlib.sha256(
        (encoder.model_name + "\x00" + "\x00".join(texts)).encode("utf-8")
    ).hexdigest()[:16]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        blob = np.load(cache_path, allow_pickle=False)
        if str(blob["key"]) == key and blob["matrix"].shape[0] == len(texts):
            log.info("loaded cached corpus embeddings (%d x %d)", *blob["matrix"].shape)
            return blob["matrix"]
        log.info("cache key mismatch, recomputing")
    matrix = encoder.encode(texts)
    np.savez_compressed(cache_path, matrix=matrix, key=np.array(key), model=np.array(encoder.model_name))
    log.info("cached corpus embeddings -> %s", cache_path)
    return matrix