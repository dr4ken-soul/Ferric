"""Provide transparent passthrough, record and hermetic replay wrappers."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, Literal, cast

from ferric.adapters.anthropic import normalise_anthropic
from ferric.adapters.openai import normalise_openai
from ferric.matcher import match_cassette, request_fingerprint
from ferric.schema import ErrorEvent, Event
from ferric.store import CassetteStore, build_cassette

Provider = Literal["openai", "anthropic"]
Normaliser = Callable[[dict[str, Any], Any | None, BaseException | None], list[Event]]


class ReplayObject(SimpleNamespace):
    """Provide recursive attribute access for a replayed SDK-like response."""

    def model_dump(self, **_: Any) -> dict[str, Any]:
        """Return a plain mapping compatible with common provider SDK models."""

        return {
            key: _to_plain(value)
            for key, value in vars(self).items()
            if not key.startswith("_ferric_")
        }

    def model_dump_json(self, **kwargs: Any) -> str:
        """Return stable JSON for the replayed object."""

        exact = getattr(self, "_ferric_response_json", None)
        if exact is not None and not kwargs:
            return cast(str, exact)
        return json.dumps(self.model_dump(), **kwargs)

    def to_json(self) -> str:
        """Return compact JSON for Anthropic-compatible callers."""

        return json.dumps(self.model_dump(), separators=(",", ":"))


def _to_plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _to_plain(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(child) for child in value]
    if isinstance(value, bytes):
        return value.decode("latin-1")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "__dict__"):
        return {
            key: _to_plain(child)
            for key, child in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


def _to_object(value: Any, exact_json: str | None = None) -> Any:
    if isinstance(value, dict):
        result = ReplayObject(
            **{key: _to_object(child) for key, child in value.items()}
        )
        if exact_json is not None:
            result._ferric_response_json = exact_json
        return result
    if isinstance(value, list):
        return [_to_object(child) for child in value]
    return value


def _serialise_response(response: Any) -> tuple[Any, str, str | None]:
    if isinstance(response, bytes):
        return response.decode("latin-1"), "bytes", None
    if isinstance(response, dict):
        return _to_plain(response), "mapping", None
    if response is None:
        return None, "none", None
    response_json: str | None = None
    if hasattr(response, "model_dump_json"):
        response_json = cast(str, response.model_dump_json())
    elif hasattr(response, "to_json"):
        response_json = cast(str, response.to_json())
    return _to_plain(response), "object", response_json


def _reconstruct_response(
    response: Any,
    kind: str,
    response_json: str | None = None,
) -> Any:
    if kind == "bytes":
        return cast(str, response).encode("latin-1")
    if kind == "mapping":
        return response
    if kind == "none":
        return None
    return _to_object(response, response_json)


class RecordedProviderError(RuntimeError):
    """Represent a provider error served from a recorded cassette."""


def _detect_provider(client: Any) -> Provider:
    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        return "openai"
    if hasattr(client, "messages"):
        return "anthropic"
    raise TypeError("unsupported client shape, expected chat.completions or messages")


class _EndpointProxy:
    def __init__(self, owner: FerricClient, endpoint: Any, provider: Provider) -> None:
        self._owner = owner
        self._endpoint = endpoint
        self._provider = provider

    def create(self, *args: Any, **kwargs: Any) -> Any:
        return self._owner._create(self._endpoint, self._provider, args, kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._endpoint, name)


class _NamespaceProxy:
    def __init__(self, **values: Any) -> None:
        for key, value in values.items():
            setattr(self, key, value)


class FerricClient:
    """Wrap common OpenAI and Anthropic client call shapes."""

    def __init__(
        self,
        client: Any,
        *,
        mode: str,
        store: CassetteStore,
        provider: Provider,
    ) -> None:
        """Initialise the selected execution path around one client."""

        if mode not in {"", "record", "replay"}:
            raise ValueError("FERRIC_MODE must be record, replay, or unset")
        self._client = client
        self._mode = mode
        self._store = store
        self._provider = provider
        if provider == "openai":
            endpoint = client.chat.completions
            self.chat = _NamespaceProxy(
                completions=_EndpointProxy(self, endpoint, provider)
            )
        else:
            self.messages = _EndpointProxy(self, client.messages, provider)

    def __getattr__(self, name: str) -> Any:
        """Delegate all unsupported attributes to the original client."""

        return getattr(self._client, name)

    def _create(
        self,
        endpoint: Any,
        provider: Provider,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        if self._mode == "":
            return endpoint.create(*args, **kwargs)
        request = dict(kwargs)
        if args:
            request["_positional_args"] = list(args)
        model = str(request.get("model", "unknown"))
        fingerprint = request_fingerprint(
            model,
            request.get("messages", []),
            request.get("tools", []),
        )
        if self._mode == "replay":
            cassette = match_cassette(self._store, fingerprint)
            error_events = [
                event for event in cassette.events if isinstance(event, ErrorEvent)
            ]
            if error_events:
                payload = error_events[-1].payload
                raise RecordedProviderError(
                    f"recorded {payload.error_type}: {payload.message}"
                )
            return _reconstruct_response(
                cassette.response,
                cassette.response_kind,
                cassette.response_json,
            )

        normaliser: Normaliser = (
            normalise_openai if provider == "openai" else normalise_anthropic
        )
        started = time.perf_counter()
        try:
            response = endpoint.create(*args, **kwargs)
        except BaseException as error:
            elapsed = int((time.perf_counter() - started) * 1000)
            events = normaliser(request, None, error)
            cassette = build_cassette(
                provider=provider,
                model=model,
                fingerprint=fingerprint,
                latency_ms=elapsed,
                request=_to_plain(request),
                response=None,
                response_kind="none",
                events=events,
            )
            self._store.write(cassette)
            raise
        elapsed = int((time.perf_counter() - started) * 1000)
        response_data, response_kind, response_json = _serialise_response(response)
        events = normaliser(request, response, None)
        cassette = build_cassette(
            provider=provider,
            model=model,
            fingerprint=fingerprint,
            latency_ms=elapsed,
            request=_to_plain(request),
            response=response_data,
            response_kind=response_kind,
            response_json=response_json,
            events=events,
        )
        self._store.write(cassette)
        return response


def wrap(
    client: Any,
    *,
    cassette_dir: str | os.PathLike[str] | None = None,
    provider: Provider | None = None,
    mode: str | None = None,
) -> FerricClient:
    """Wrap an OpenAI or Anthropic client using the selected Ferric mode."""

    selected_mode = os.environ.get("FERRIC_MODE", "") if mode is None else mode
    selected_provider = provider or _detect_provider(client)
    return FerricClient(
        client,
        mode=selected_mode.casefold(),
        store=CassetteStore(
            os.fspath(cassette_dir) if cassette_dir is not None else None
        ),
        provider=selected_provider,
    )
