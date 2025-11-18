"""
Utility functions for the application.
"""
import hashlib


def hash_text_sha256(value: str) -> str:
    """Hash text using SHA256."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
