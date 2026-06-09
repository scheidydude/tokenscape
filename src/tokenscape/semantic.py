from __future__ import annotations

import hashlib
import json
import math
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np

from .types import Turn

_CACHE_PATH = Path.home() / '.cache' / 'tokenscape' / 'embeddings.npz'
_LABEL_CACHE_PATH = Path.home() / '.cache' / 'tokenscape' / 'labels.json'
_SUMMARY_CACHE_PATH = Path.home() / '.cache' / 'tokenscape' / 'summaries.json'
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


def _label_cache_key(examples: list[str]) -> str:
    return hashlib.sha256('|'.join(sorted(examples)).encode()).hexdigest()


def _load_label_cache() -> dict[str, str]:
    if not _LABEL_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_LABEL_CACHE_PATH.read_text())
    except Exception:
        return {}


def _save_label_cache(cache: dict[str, str]) -> None:
    _LABEL_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LABEL_CACHE_PATH.write_text(json.dumps(cache, indent=2))


def label_cluster(examples: list[str], config: dict[str, str]) -> str | None:
    cache = _load_label_cache()
    key = _label_cache_key(examples)
    if key in cache:
        return cache[key]

    prompt = (
        'These are example prompts from a cluster of similar user requests:\n'
        + '\n'.join(f'- {e}' for e in examples)
        + '\n\nRespond with a 2-3 word label for this cluster. Just the label, nothing else.'
    )
    payload = json.dumps({
        'model': config['model'],
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 20,
        'temperature': 0.0,
    }).encode()

    try:
        req = urllib.request.Request(
            f"{config['base_url']}/chat/completions",
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {config['api_key']}",
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        label = data['choices'][0]['message']['content'].strip()
        cache[key] = label
        _save_label_cache(cache)
        return label
    except Exception:
        return None


def _load_summary_cache() -> dict[str, str]:
    if not _SUMMARY_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_SUMMARY_CACHE_PATH.read_text())
    except Exception:
        return {}


def _save_summary_cache(cache: dict[str, str]) -> None:
    _SUMMARY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SUMMARY_CACHE_PATH.write_text(json.dumps(cache, indent=2))


def generate_ai_summary(context: dict, config: dict[str, str], force: bool = False) -> str | None:
    import sys
    import urllib.error

    cache = _load_summary_cache()
    key = hashlib.sha256(
        json.dumps({**context, '__model__': config['model']}, sort_keys=True).encode()
    ).hexdigest()
    if not force and key in cache:
        print(f'AI Insights: using cached summary ({config["model"]})', file=sys.stderr)
        return cache[key]

    prompt = (
        'You are analyzing a developer\'s Claude Code usage statistics.\n\n'
        'Report data (JSON):\n'
        + json.dumps(context, indent=2)
        + '\n\nWrite a markdown analysis (200-300 words) with these 4 sections:\n'
        '1. **Usage Patterns** — what the data reveals about work habits\n'
        '2. **Token Efficiency** — cache hit rate, avg/turn, waste signals\n'
        '3. **Model Selection** — whether the right models are used for the right tasks\n'
        '4. **Recommended Actions** — 3-5 specific, actionable improvements\n\n'
        'Be specific. Reference actual numbers. No generic advice.'
    )
    payload = json.dumps({
        'model': config['model'],
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 2048,
        'temperature': 0.3,
        'stream': False,
        'chat_template_kwargs': {'enable_thinking': False},
    }).encode()

    req = urllib.request.Request(
        f"{config['base_url']}/chat/completions",
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {config['api_key']}",
        },
        method='POST',
    )
    print(f'AI Insights: requesting summary from {config["model"]}…', file=sys.stderr)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'HTTP {e.code} from {req.full_url}: {body}') from e
    msg = data['choices'][0]['message']
    summary = (msg.get('content') or msg.get('reasoning') or '').strip()
    if not summary:
        raise RuntimeError(f'Empty response from model. Full response: {json.dumps(data)[:500]}')
    cache[key] = summary
    _save_summary_cache(cache)
    print('AI Insights: done', file=sys.stderr)
    return summary


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
