"""Configuration. Every tunable is declared here so runs are reproducible."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ML_ROOT.parent


@dataclass(frozen=True)
class Settings:
    # --- paths -------------------------------------------------------------
    data_dir: Path = REPO_ROOT / "data"
    corpus_path: Path = REPO_ROOT / "data" / "processed" / "duas.json"
    queries_path: Path = REPO_ROOT / "data" / "evaluation" / "queries.json"
    ontology_path: Path = REPO_ROOT / "data" / "ontology" / "ontology.json"
    artifacts_dir: Path = REPO_ROOT / "data" / "artifacts"

    # --- embedding model ---------------------------------------------------
    # Pinned. Never "latest": an unpinned model makes results irreproducible.
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384
    embedding_batch_size: int = 32
    normalize_embeddings: bool = True

    # --- candidate retrieval ----------------------------------------------
    candidate_pool: int = 100

    # --- fusion ------------------------------------------------------------
    fusion: str = "weighted"  # "weighted" | "rrf"
    rrf_k: int = 60

    # --- initial ranking weights (tuned on the validation split) -------------
    # These are starting values for coordinate ascent, not asserted truths.
    initial_weights: dict[str, float] = field(
        default_factory=lambda: {
            "semantic": 0.30,
            "lexical": 0.15,
            "situation": 0.20,
            "emotion": 0.10,
            "intention": 0.10,
            "occasion": 0.10,
            "topic": 0.05,
        }
    )

    # --- context extraction ------------------------------------------------
    context_top_k: int = 2
    context_threshold: float = 0.30

    # --- evaluation --------------------------------------------------------
    k: int = 5
    seed: int = 42
    validation_fraction: float = 0.25
    use_tuned_weights: bool = True

    @property
    def embedding_cache(self) -> Path:
        return self.artifacts_dir / f"embeddings_{self.embedding_model.replace('/', '_')}.npz"

    def ensure_dirs(self) -> None:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()

# Optional local override for experiments: DUAWISE_EMBED_MODEL=...
if override := os.environ.get("DUAWISE_EMBED_MODEL"):
    settings = Settings(embedding_model=override)