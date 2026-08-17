from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ferric.matcher import UnmatchedRequestError
from ferric.redact import RedactionRule
from ferric.store import CassetteStore, CassetteStoreError
from ferric.wrapper import RecordedProviderError, replay_client, wrap


class FakeResponse:
    def __init__(self, payload: dict[str, Any], exact_json: str | None = None) -> None:
        self.payload = payload
        self.exact_json = exact_json or json.dumps(payload, separators=(",", ":"))

    def model_dump(self, **_: Any) -> dict[str, Any]:
        return self.payload

    def model_dump_json(self) -> str:
        return self.exact_json


class Endpoint:
    def __init__(
        self, response: Any = None, error: BaseException | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def create(self, *args: Any, **kwargs: Any) -> Any:
        self.calls.append((args, kwargs))
        if self.error is not None:
            raise self.error
        return self.response


class OpenAIClient:
    def __init__(self, endpoint: Endpoint) -> None:
        self.chat = SimpleNamespace(completions=endpoint)


class AnthropicClient:
    def __init__(self, endpoint: Endpoint) -> None:
        self.messages = endpoint


class NestedProviderSpy:
    @property
    def with_raw_response(self) -> Any:
        raise AssertionError("nested provider endpoint was accessed")


OPENAI_REQUEST = {
    "model": "local-openai",
    "messages": [{"role": "user", "content": "local request"}],
    "tools": [],
}
OPENAI_RESPONSE = {
    "id": "local-response",
    "choices": [
        {"message": {"role": "assistant", "content": "local reply", "refusal": None}}
    ],
    "usage": {"total_tokens": 7},
}


def test_passthrough_forwards_arguments_and_returns_identity(tmp_path: Path) -> None:
    response = FakeResponse(OPENAI_RESPONSE)
    endpoint = Endpoint(response)
    wrapped = wrap(OpenAIClient(endpoint), cassette_dir=tmp_path, mode="")
    observed = wrapped.chat.completions.create(**OPENAI_REQUEST)
    assert observed is response
    assert endpoint.calls == [((), OPENAI_REQUEST)]
    assert list(tmp_path.iterdir()) == []


def test_record_forwards_unchanged_and_returns_identity(tmp_path: Path) -> None:
    response = FakeResponse(OPENAI_RESPONSE)
    endpoint = Endpoint(response)
    wrapped = wrap(OpenAIClient(endpoint), cassette_dir=tmp_path, mode="record")
    observed = wrapped.chat.completions.create(**OPENAI_REQUEST)
    assert observed is response
    assert endpoint.calls == [((), OPENAI_REQUEST)]
    cassettes = CassetteStore(tmp_path).verify()
    assert len(cassettes) == 1
    assert cassettes[0].provider == "openai"


def test_replay_never_calls_provider_or_socket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeResponse(OPENAI_RESPONSE)
    recorder = wrap(
        OpenAIClient(Endpoint(response)), cassette_dir=tmp_path, mode="record"
    )
    recorder.chat.completions.create(**OPENAI_REQUEST)
    endpoint = Endpoint(error=AssertionError("provider was called"))

    def fail_socket(*_: Any, **__: Any) -> None:
        raise AssertionError("a socket was opened")

    monkeypatch.setattr("socket.socket", fail_socket)
    replay = wrap(OpenAIClient(endpoint), cassette_dir=tmp_path, mode="replay")
    observed = replay.chat.completions.create(**OPENAI_REQUEST)
    assert observed.choices[0].message.content.encode("utf-8") == b"local reply"
    assert endpoint.calls == []


def test_nested_openai_raw_response_replay_never_touches_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeResponse(OPENAI_RESPONSE)
    recorder = wrap(
        OpenAIClient(Endpoint(response)), cassette_dir=tmp_path, mode="record"
    )
    recorder.chat.completions.create(**OPENAI_REQUEST)

    def fail_socket(*_: Any, **__: Any) -> None:
        raise AssertionError("a socket was opened")

    monkeypatch.setattr("socket.socket", fail_socket)
    client = OpenAIClient(NestedProviderSpy())
    replay = wrap(client, cassette_dir=tmp_path, mode="replay")
    observed = replay.chat.completions.with_raw_response.create(**OPENAI_REQUEST)
    assert observed.choices[0].message.content == "local reply"


def test_nested_anthropic_raw_response_replay_never_touches_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = {
        "model": "local-anthropic",
        "max_tokens": 32,
        "messages": [{"role": "user", "content": "local request"}],
    }
    payload = {
        "id": "local-message",
        "content": [{"type": "text", "text": "local Anthropic reply"}],
    }
    wrap(
        AnthropicClient(Endpoint(FakeResponse(payload))),
        cassette_dir=tmp_path,
        mode="record",
    ).messages.create(**request)

    def fail_socket(*_: Any, **__: Any) -> None:
        raise AssertionError("a socket was opened")

    monkeypatch.setattr("socket.socket", fail_socket)
    replay = wrap(
        AnthropicClient(NestedProviderSpy()), cassette_dir=tmp_path, mode="replay"
    )
    observed = replay.messages.with_raw_response.create(**request)
    assert observed.content[0].text == "local Anthropic reply"


def test_keyless_replay_client_needs_no_sdk_key_or_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = FakeResponse(OPENAI_RESPONSE)
    wrap(
        OpenAIClient(Endpoint(response)), cassette_dir=tmp_path, mode="record"
    ).chat.completions.create(**OPENAI_REQUEST)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fail_socket(*_: Any, **__: Any) -> None:
        raise AssertionError("a socket was opened")

    monkeypatch.setattr("socket.socket", fail_socket)
    replay = replay_client("openai", cassette_dir=tmp_path)
    observed = replay.chat.completions.with_streaming_response.create(**OPENAI_REQUEST)
    assert observed.choices[0].message.content == "local reply"


def test_keyless_anthropic_replay_client_needs_no_transport(tmp_path: Path) -> None:
    request = {
        "model": "local-anthropic",
        "max_tokens": 32,
        "messages": [{"role": "user", "content": "local request"}],
    }
    payload = {"content": [{"type": "text", "text": "local reply"}]}
    wrap(
        AnthropicClient(Endpoint(FakeResponse(payload))),
        cassette_dir=tmp_path,
        mode="record",
    ).messages.create(**request)
    observed = replay_client("anthropic", cassette_dir=tmp_path).messages.create(
        **request
    )
    assert observed.content[0].text == "local reply"


def test_wrap_exposes_custom_redaction_rules(tmp_path: Path) -> None:
    request = {
        **OPENAI_REQUEST,
        "messages": [{"role": "user", "content": "tenant-private-42"}],
    }
    rule = RedactionRule.from_pattern("tenant", r"tenant-private-\d+")
    wrap(
        OpenAIClient(Endpoint(FakeResponse(OPENAI_RESPONSE))),
        cassette_dir=tmp_path,
        mode="record",
        custom_rules=(rule,),
    ).chat.completions.create(**request)
    raw = next(
        path for path in tmp_path.glob("*.json") if path.name != "manifest.json"
    ).read_text(encoding="utf-8")
    assert "tenant-private-42" not in raw
    assert "[REDACTED:tenant]" in raw


def test_keyless_replay_applies_custom_verification_rules(tmp_path: Path) -> None:
    request = {
        **OPENAI_REQUEST,
        "messages": [{"role": "user", "content": "tenant-private-42"}],
    }
    wrap(
        OpenAIClient(Endpoint(FakeResponse(OPENAI_RESPONSE))),
        cassette_dir=tmp_path,
        mode="record",
    ).chat.completions.create(**request)
    rule = RedactionRule.from_pattern("tenant", r"tenant-private-\d+")
    replay = replay_client("openai", cassette_dir=tmp_path, custom_rules=(rule,))
    with pytest.raises(CassetteStoreError, match="unredacted tenant"):
        replay.chat.completions.create(**request)


def test_replay_reconstructs_exact_response_json(tmp_path: Path) -> None:
    exact = '{"id":"local-response", "choices":[{"message":{"role":"assistant","content":"local reply","refusal":null}}], "usage":{"total_tokens":7}}'
    response = FakeResponse(OPENAI_RESPONSE, exact)
    wrap(
        OpenAIClient(Endpoint(response)), cassette_dir=tmp_path, mode="record"
    ).chat.completions.create(**OPENAI_REQUEST)
    replayed = wrap(
        OpenAIClient(Endpoint(error=AssertionError("provider called"))),
        cassette_dir=tmp_path,
        mode="replay",
    ).chat.completions.create(**OPENAI_REQUEST)
    assert replayed.model_dump_json().encode("utf-8") == exact.encode("utf-8")


def test_repeated_replay_is_byte_equivalent(tmp_path: Path) -> None:
    response = FakeResponse(OPENAI_RESPONSE)
    wrap(
        OpenAIClient(Endpoint(response)), cassette_dir=tmp_path, mode="record"
    ).chat.completions.create(**OPENAI_REQUEST)
    replay = wrap(OpenAIClient(Endpoint()), cassette_dir=tmp_path, mode="replay")
    first = replay.chat.completions.create(**OPENAI_REQUEST)
    second = replay.chat.completions.create(**OPENAI_REQUEST)
    assert first.model_dump_json().encode() == second.model_dump_json().encode()


def test_unmatched_replay_never_falls_through(tmp_path: Path) -> None:
    wrap(
        OpenAIClient(Endpoint(FakeResponse(OPENAI_RESPONSE))),
        cassette_dir=tmp_path,
        mode="record",
    ).chat.completions.create(**OPENAI_REQUEST)
    endpoint = Endpoint(error=AssertionError("provider called"))
    replay = wrap(OpenAIClient(endpoint), cassette_dir=tmp_path, mode="replay")
    with pytest.raises(UnmatchedRequestError, match="nearest cassette"):
        replay.chat.completions.create(**{**OPENAI_REQUEST, "model": "changed-model"})
    assert endpoint.calls == []


def test_anthropic_messages_shape_records_and_replays(tmp_path: Path) -> None:
    request = {
        "model": "local-anthropic",
        "max_tokens": 32,
        "messages": [{"role": "user", "content": "local request"}],
    }
    payload = {
        "id": "local-message",
        "content": [{"type": "text", "text": "local Anthropic reply"}],
        "usage": {"input_tokens": 4, "output_tokens": 3},
    }
    recorder = wrap(
        AnthropicClient(Endpoint(FakeResponse(payload))),
        cassette_dir=tmp_path,
        mode="record",
    )
    recorder.messages.create(**request)
    endpoint = Endpoint(error=AssertionError("provider called"))
    replay = wrap(AnthropicClient(endpoint), cassette_dir=tmp_path, mode="replay")
    observed = replay.messages.create(**request)
    assert observed.content[0].text == "local Anthropic reply"
    assert endpoint.calls == []


def test_provider_error_is_recorded_and_original_is_reraised(tmp_path: Path) -> None:
    error = RuntimeError("deterministic provider failure")
    wrapped = wrap(
        OpenAIClient(Endpoint(error=error)), cassette_dir=tmp_path, mode="record"
    )
    with pytest.raises(RuntimeError) as failure:
        wrapped.chat.completions.create(**OPENAI_REQUEST)
    assert failure.value is error
    cassette = CassetteStore(tmp_path).verify()[0]
    assert cassette.events[-1].role.value == "error"


def test_recorded_provider_error_replays_without_call(tmp_path: Path) -> None:
    wrapped = wrap(
        OpenAIClient(Endpoint(error=RuntimeError("recorded local failure"))),
        cassette_dir=tmp_path,
        mode="record",
    )
    with pytest.raises(RuntimeError):
        wrapped.chat.completions.create(**OPENAI_REQUEST)
    endpoint = Endpoint(error=AssertionError("provider called"))
    replay = wrap(OpenAIClient(endpoint), cassette_dir=tmp_path, mode="replay")
    with pytest.raises(RecordedProviderError, match="recorded RuntimeError"):
        replay.chat.completions.create(**OPENAI_REQUEST)
    assert endpoint.calls == []


def test_invalid_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="FERRIC_MODE"):
        wrap(OpenAIClient(Endpoint()), mode="live")


def test_unsupported_client_shape_is_rejected() -> None:
    with pytest.raises(TypeError, match="unsupported client shape"):
        wrap(object())
