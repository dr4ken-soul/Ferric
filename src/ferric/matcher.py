"""Build stable request fingerprints and resolve exact cassette matches."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ferric.schema import Cassette
from ferric.store import CassetteStore

_VOLATILE_KEYS = frozenset(
    {"created", "created_at", "id", "request_id", "timestamp", "trace_id"}
)


class UnmatchedRequestError(LookupError):
    """Report an exact replay miss and its nearest diagnostic neighbour."""


def normalise_request_value(value: Any) -> Any:
    """Remove volatile keys and return stable JSON-compatible request data."""

    if isinstance(value, dict):
        return {
            str(key): normalise_request_value(child)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key).casefold() not in _VOLATILE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [normalise_request_value(child) for child in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "model_dump"):
        return normalise_request_value(value.model_dump(mode="json"))
    return str(value)


def request_fingerprint(
    model: str,
    messages: Any,
    tools: Any = None,
) -> str:
    """Hash the model, normalised messages and tools in scope."""

    canonical = json.dumps(
        {
            "messages": normalise_request_value(messages),
            "model": model,
            "tools": normalise_request_value(tools or []),
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def fingerprint_distance(left: str, right: str) -> int:
    """Return the bitwise Hamming distance between two SHA-256 fingerprints."""

    if len(left) != len(right):
        raise ValueError("fingerprints must have equal length")
    try:
        return (int(left, 16) ^ int(right, 16)).bit_count()
    except ValueError as error:
        raise ValueError("fingerprints must be hexadecimal") from error


def match_cassette(store: CassetteStore, fingerprint: str) -> Cassette:
    """Return an exact match or raise with the nearest cassette diagnostic."""

    cassettes = store.list()
    for cassette in cassettes:
        if cassette.fingerprint == fingerprint:
            return cassette
    if not cassettes:
        nearest = "none, the cassette store is empty"
    else:
        candidate = min(
            cassettes,
            key=lambda item: fingerprint_distance(fingerprint, item.fingerprint),
        )
        distance = fingerprint_distance(fingerprint, candidate.fingerprint)
        nearest = f"{candidate.id} at fingerprint distance {distance}"
    raise UnmatchedRequestError(
        f"unmatched replay request fingerprint {fingerprint}; nearest cassette: {nearest}"
    )
