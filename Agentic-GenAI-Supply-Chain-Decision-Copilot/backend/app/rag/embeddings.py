import numpy as np
from typing import List

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

_model_instance = None
_use_fallback = False

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    _use_fallback = True

try:
    from sklearn.feature_extraction.text import HashingVectorizer
    _hashing_vectorizer = HashingVectorizer(n_features=EMBEDDING_DIMENSION, norm='l2')
except ImportError:
    _hashing_vectorizer = None


def get_embedding_model():
    global _model_instance, _use_fallback
    if _use_fallback or SentenceTransformer is None:
        return None
    if _model_instance is None:
        try:
            _model_instance = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except Exception:
            _use_fallback = True
            return None
    return _model_instance


def _fallback_embed(text: str) -> List[float]:
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIMENSION
    if _hashing_vectorizer is not None:
        vec = _hashing_vectorizer.transform([text]).toarray()[0]
        return vec.tolist()
    # Simple deterministic hash fallback if sklearn absent
    arr = np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)
    for word in text.lower().split():
        idx = abs(hash(word)) % EMBEDDING_DIMENSION
        arr[idx] += 1.0
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()


def embed_text(text: str) -> List[float]:
    """
    Generates a 384-dimensional dense vector embedding for a single query or text string.
    Uses sentence-transformers (all-MiniLM-L6-v2) with sklearn HashingVectorizer fallback.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIMENSION

    model = get_embedding_model()
    if model is not None:
        try:
            vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return vec.tolist()
        except Exception:
            pass

    return _fallback_embed(text)


def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Generates 384-dimensional dense vector embeddings for a batch of document chunks.
    """
    if not texts:
        return []

    model = get_embedding_model()
    if model is not None:
        try:
            vecs = model.encode(texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True)
            return [v.tolist() for v in vecs]
        except Exception:
            pass

    return [_fallback_embed(t) for t in texts]

