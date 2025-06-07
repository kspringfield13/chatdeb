from __future__ import annotations

"""Utility for matching user queries against preloaded analysis questions."""

from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


QUESTIONS_FILE = Path(__file__).parent / "data" / "preloaded" / "analysis_quest.txt"

_vectorizer: TfidfVectorizer | None = None
_embeddings = None
_questions: list[str] = []


def _load():
    global _vectorizer, _embeddings, _questions
    if _vectorizer is not None:
        return
    if not QUESTIONS_FILE.exists():
        _vectorizer = None
        _embeddings = None
        _questions = []
        return

    text = [q.strip() for q in QUESTIONS_FILE.read_text(encoding="utf-8").splitlines() if q.strip()]
    _questions = text
    _vectorizer = TfidfVectorizer().fit(text)
    _embeddings = _vectorizer.transform(text)


def is_similar(question: str, threshold: float = 0.5) -> bool:
    """Return ``True`` if ``question`` is semantically close to the preloaded ones."""
    _load()
    if not _vectorizer or _embeddings is None:
        return False
    vec = _vectorizer.transform([question])
    sims = cosine_similarity(vec, _embeddings)
    score = float(sims.max()) if sims.size else 0.0
    return score >= threshold


__all__ = ["is_similar"]
