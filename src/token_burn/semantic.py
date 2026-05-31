from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from .types import Turn

_CACHE_PATH = Path.home() / '.cache' / 'token-burn' / 'embeddings.npz'
_MODEL = 'BAAI/bge-small-en-v1.5'


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _load_cache() -> dict[str, np.ndarray]:
    if not _CACHE_PATH.exists():
        return {}
    try:
        data = np.load(str(_CACHE_PATH))
        hashes = data['hashes']
        embeddings = data['embeddings']
        if len(hashes) == 0:
            return {}
        return {str(h): embeddings[i] for i, h in enumerate(hashes)}
    except Exception:
        return {}


def _save_cache(cache: dict[str, np.ndarray]) -> None:
    if not cache:
        return
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    hashes = np.array(list(cache.keys()))
    embeddings = np.array(list(cache.values()), dtype=np.float32)
    np.savez(str(_CACHE_PATH), hashes=hashes, embeddings=embeddings)


def embed_prompts(texts: list[str]) -> np.ndarray:
    from fastembed import TextEmbedding  # optional dep

    cache = _load_cache()
    results: dict[int, np.ndarray] = {}
    to_embed: list[tuple[int, str]] = []

    for i, text in enumerate(texts):
        h = _sha256(text)
        if h in cache:
            results[i] = cache[h]
        else:
            to_embed.append((i, text))

    if to_embed:
        model = TextEmbedding(model_name=_MODEL)
        idxs, raw_texts = zip(*to_embed)
        vecs = list(model.embed(list(raw_texts)))
        for idx, text, vec in zip(idxs, raw_texts, vecs):
            arr = np.array(vec, dtype=np.float32)
            cache[_sha256(text)] = arr
            results[idx] = arr
        _save_cache(cache)

    return np.array([results[i] for i in range(len(texts))], dtype=np.float32)


def auto_k(n: int) -> int:
    return max(2, min(20, int(math.sqrt(n / 2))))


def cluster_prompts(embeddings: np.ndarray, k: int) -> np.ndarray:
    from sklearn.cluster import KMeans  # optional dep

    km = KMeans(n_clusters=k, random_state=42, n_init='auto')
    return km.fit_predict(embeddings).astype(int)


def nearest_to_centroid(
    embeddings: np.ndarray,
    labels: np.ndarray,
    prompts: list[str],
    n: int = 3,
) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    for label in sorted(set(labels.tolist())):
        mask = labels == label
        cluster_embs = embeddings[mask]
        cluster_prompts_list = [p for p, m in zip(prompts, mask.tolist()) if m]
        centroid = cluster_embs.mean(axis=0)
        norms = np.linalg.norm(cluster_embs, axis=1, keepdims=True)
        normed = cluster_embs / np.where(norms > 0, norms, 1.0)
        c_norm = centroid / max(float(np.linalg.norm(centroid)), 1e-8)
        sims = normed @ c_norm
        top = np.argsort(-sims)[:n]
        result[label] = [cluster_prompts_list[i] for i in top]
    return result


def analyze(
    turns: list[Turn],
    k: int | None = None,
) -> tuple[dict[int, list[str]], dict[int, int], int]:
    prompts = [
        t.user_text.strip()
        for t in turns
        if len(t.user_text.strip().split()) >= 3
    ]
    if not prompts:
        return {}, {}, 0

    k_used = k if k is not None else auto_k(len(prompts))
    k_used = min(k_used, len(prompts))

    embeddings = embed_prompts(prompts)
    labels = cluster_prompts(embeddings, k_used)
    examples = nearest_to_centroid(embeddings, labels, prompts)

    counts: dict[int, int] = defaultdict(int)
    for label in labels.tolist():
        counts[label] += 1

    sorted_labels = sorted(counts, key=lambda l: -counts[l])
    return (
        {i: examples[lbl] for i, lbl in enumerate(sorted_labels)},
        {i: counts[lbl] for i, lbl in enumerate(sorted_labels)},
        k_used,
    )
