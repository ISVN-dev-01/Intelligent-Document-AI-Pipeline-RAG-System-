"""Embedding interface plus an explicitly non-semantic offline demonstration provider."""
import hashlib
import re
from typing import Protocol

import numpy as np


class EmbeddingService(Protocol):
    fingerprint: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


STOPWORDS = set("a an the is are was were be to of in on for and or what how many who does do can it this that with as per its".split())


def terms(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS}


class HashEmbeddingService:
    """Stable hashed bag of words. Test/demo baseline, NOT a trained language model."""
    fingerprint = "offline-hash-v1:1024"

    def embed_query(self, text):
        vector = np.zeros(1024, dtype=np.float32)
        for word in terms(text):
            digest = hashlib.sha256(word.encode()).digest()
            vector[int.from_bytes(digest[:4], "big") % 1024] += 1
        if not vector.any():
            vector[0] = 1
        return vector.tolist()

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]
