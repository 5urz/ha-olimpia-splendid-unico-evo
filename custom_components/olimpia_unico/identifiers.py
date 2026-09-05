"""Privacy-preserving identifiers for Olimpia Splendid UNICO."""

from __future__ import annotations

from hashlib import sha256

_FINGERPRINT_PREFIX = "unico-"
_FINGERPRINT_HEX_LENGTH = 20


def device_fingerprint(device_id: str) -> str:
    """Return a stable non-secret fingerprint for a Tuya Device ID.

    The raw Device ID is still stored in the config entry because TinyTuya needs
    it for local communication, but it should not be exposed through Home
    Assistant registry identifiers or entity unique IDs.
    """
    normalized = device_id.strip()
    digest = sha256(normalized.encode("utf-8")).hexdigest()
    return f"{_FINGERPRINT_PREFIX}{digest[:_FINGERPRINT_HEX_LENGTH]}"
