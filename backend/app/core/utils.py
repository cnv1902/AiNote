"""
Các hàm tiện ích cho ứng dụng.
"""
import hashlib


def hash_text_sha256(value: str) -> str:
    """Băm văn bản bằng SHA256."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
