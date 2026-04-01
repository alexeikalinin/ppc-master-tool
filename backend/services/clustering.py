"""
Semantic keyword clustering using sentence-transformers + KMeans.
Groups keywords into semantic clusters and suggests minus-words per group.
"""

import re
from collections import Counter

from backend.models import Keyword, SemanticGroup

# Loaded lazily to avoid slow import at startup
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


# Common minus-words for Russian PPC
_BASE_MINUS_WORDS = [
    "бесплатно",
    "своими руками",
    "diy",
    "youtube",
    "wikipedia",
    "отзывы плохие",
    "жалоба",
    "мошенники",
    "вакансия",
    "работа",
    "скачать",
    "торрент",
    "бу",
    "секонд",
]


def cluster_keywords(keywords: list[Keyword]) -> list[SemanticGroup]:
    """
    Cluster unique keyword texts into 4–8 semantic groups.
    Falls back to simple frequency-based splitting if sentence-transformers fails.
    """
    if not keywords:
        return []

    # Deduplicate by text (keep highest-frequency entry)
    by_text: dict[str, Keyword] = {}
    for kw in keywords:
        if kw.text not in by_text or kw.frequency > by_text[kw.text].frequency:
            by_text[kw.text] = kw
    unique_kws = list(by_text.values())
    texts = [kw.text for kw in unique_kws]

    n_clusters = max(3, min(8, len(texts) // 3))

    try:
        groups = _cluster_with_transformers(texts, unique_kws, n_clusters)
    except Exception:
        groups = _cluster_simple(unique_kws, n_clusters)

    return groups


def _cluster_with_transformers(
    texts: list[str], kws: list[Keyword], n_clusters: int
) -> list[SemanticGroup]:
    from sklearn.cluster import KMeans
    import numpy as np

    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(embeddings)

    cluster_map: dict[int, list[Keyword]] = {}
    for idx, label in enumerate(labels):
        cluster_map.setdefault(int(label), []).append(kws[idx])

    groups: list[SemanticGroup] = []
    for label, members in sorted(cluster_map.items()):
        members_sorted = sorted(members, key=lambda k: k.frequency, reverse=True)
        name = _group_name(members_sorted)
        minus = _suggest_minus_words(members_sorted)
        groups.append(
            SemanticGroup(name=name, keywords=members_sorted, minus_words=minus)
        )
    return groups


def _cluster_simple(kws: list[Keyword], n_clusters: int) -> list[SemanticGroup]:
    """Fallback: split alphabetically into equal buckets."""
    sorted_kws = sorted(kws, key=lambda k: k.text)
    size = max(1, len(sorted_kws) // n_clusters)
    groups: list[SemanticGroup] = []
    for i in range(0, len(sorted_kws), size):
        chunk = sorted_kws[i : i + size]
        name = _group_name(chunk)
        groups.append(
            SemanticGroup(name=name, keywords=chunk, minus_words=_BASE_MINUS_WORDS[:5])
        )
    return groups


def _group_name(members: list[Keyword]) -> str:
    """Use the highest-frequency keyword as group label."""
    top = max(members, key=lambda k: k.frequency)
    return top.text.capitalize()


def _suggest_minus_words(members: list[Keyword]) -> list[str]:
    """Return context-relevant minus-words for the group."""
    all_words = " ".join(kw.text for kw in members).lower()
    tokens = re.split(r"\s+", all_words)
    common = [w for w, _ in Counter(tokens).most_common(5) if len(w) > 3]
    return list(
        set(_BASE_MINUS_WORDS[:6] + [w for w in common if w not in _BASE_MINUS_WORDS])
    )
