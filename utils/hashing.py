import hashlib


def sha256_bytes(data: bytes) -> str:
    """Return a content hash independent of the supplied filename."""
    return hashlib.sha256(data).hexdigest()
