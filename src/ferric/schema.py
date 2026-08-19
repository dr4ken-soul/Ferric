"""Validated provider-neutral models used by Ferric."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class EventRole(StrEnum):
    """Identify the behavioural role of one normalised event."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"


class MessagePayload(BaseModel):
    """Store provider-neutral message content."""

    model_config = ConfigDict(extra="forbid")

    content: JsonValue
    name: str | None = None
    source_role: str | None = None
    refusal: bool = False


class ToolCallPayload(BaseModel):
    """Store a normalised tool request."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    arguments: dict[str, JsonValue] = Field(default_factory=dict)
    call_id: str | None = None


class ToolResultPayload(BaseModel):
    """Store the result returned by a tool."""

    model_config = ConfigDict(extra="forbid")

    content: JsonValue
    name: str | None = None
    call_id: str | None = None
    is_error: bool = False


class ErrorPayload(BaseModel):
    """Store a safe provider failure description."""

    model_config = ConfigDict(extra="forbid")

    error_type: str = Field(min_length=1)
    message: str


class UserMessage(BaseModel):
    """Represent an outbound user or system message."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    role: Literal[EventRole.USER] = EventRole.USER
    payload: MessagePayload


class AssistantMessage(BaseModel):
    """Represent assistant content returned by a provider."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    role: Literal[EventRole.ASSISTANT] = EventRole.ASSISTANT
    payload: MessagePayload


class ToolCall(BaseModel):
    """Represent one provider-selected tool invocation."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    role: Literal[EventRole.TOOL_CALL] = EventRole.TOOL_CALL
    payload: ToolCallPayload


class ToolResult(BaseModel):
    """Represent one tool result supplied to an agent."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    role: Literal[EventRole.TOOL_RESULT] = EventRole.TOOL_RESULT
    payload: ToolResultPayload


class ErrorEvent(BaseModel):
    """Represent a provider error captured during recording."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    role: Literal[EventRole.ERROR] = EventRole.ERROR
    payload: ErrorPayload


Event = Annotated[
    UserMessage | AssistantMessage | ToolCall | ToolResult | ErrorEvent,
    Field(discriminator="role"),
]


def calculate_content_id(events: list[Event]) -> str:
    """Return the stable SHA-256 identifier for normalised events."""

    payload = [event.model_dump(mode="json") for event in events]
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def calculate_integrity_hash_payload(payload: Mapping[str, Any]) -> str:
    """Hash the cassette fields that must remain tamper-evident."""

    covered = {
        key: payload.get(key)
        for key in (
            "provider",
            "model",
            "fingerprint",
            "request",
            "response",
            "response_kind",
            "response_json",
            "events",
            "redactions",
            "assertions",
            "drift",
            "replay",
        )
    }
    canonical = json.dumps(
        covered,
        default=lambda value: value.model_dump(mode="json"),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class RedactionRecord(BaseModel):
    """Describe one removed value without retaining that value."""

    model_config = ConfigDict(extra="forbid")

    rule_class: str = Field(min_length=1)
    event_index: int = Field(ge=-1)
    field_path: str = Field(min_length=1)


class AssertionFamily(StrEnum):
    """Identify a behavioural assertion evidence family."""

    SEQUENCE = "sequence"
    ARGUMENTS = "arguments"
    SCHEMA = "schema"
    LEAKAGE = "leakage"


class AssertionStatus(StrEnum):
    """Record whether an evidenced assertion passed or failed."""

    PASS = "pass"
    FAIL = "fail"


class AssertionEvidence(BaseModel):
    """Store one deterministic behavioural assertion result."""

    model_config = ConfigDict(extra="forbid")

    family: AssertionFamily
    status: AssertionStatus
    message: str = Field(min_length=1)
    expected: JsonValue | None = None
    observed: JsonValue | None = None
    pattern: str | None = None
    location: str | None = None


class ReplayEvidence(BaseModel):
    """Store measured or deterministic local replay evidence."""

    model_config = ConfigDict(extra="forbid")

    network_calls: int = Field(ge=0)
    tokens: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    provenance: str = Field(min_length=1)


class DriftClassification(StrEnum):
    """Classify model behaviour relative to a recorded baseline."""

    UNCHANGED = "unchanged"
    REWORDED = "reworded"
    DIVERGED = "diverged"


class DriftDimension(StrEnum):
    """Name the behavioural dimension that changed."""

    TOOL_SELECTION = "tool_selection"
    TOOL_ORDER = "tool_order"
    SCHEMA_VALIDITY = "schema_validity"
    REFUSAL = "refusal"


class DriftEvidence(BaseModel):
    """Store deterministic local drift evidence for one cassette."""

    model_config = ConfigDict(extra="forbid")

    classification: DriftClassification
    dimension: DriftDimension | None = None
    baseline_events: list[Event] = Field(min_length=1)
    target_events: list[Event] = Field(min_length=1)
    tokens_spent: int = Field(ge=0)
    provenance: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dimension(self) -> DriftEvidence:
        """Require a dimension only for divergent evidence."""

        if self.classification is DriftClassification.DIVERGED:
            if self.dimension is None:
                raise ValueError("diverged drift evidence requires a dimension")
        elif self.dimension is not None:
            raise ValueError("only diverged drift evidence may have a dimension")
        return self


class Cassette(BaseModel):
    """Store one validated and replayable interaction."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[0-9a-f]{64}$")
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider: Literal["openai", "anthropic", "mcp"]
    model: str = Field(min_length=1)
    recorded_at: datetime
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    latency_ms: int = Field(ge=0)
    request: dict[str, JsonValue]
    response: JsonValue | None = None
    response_kind: Literal["mapping", "object", "bytes", "none"] = "object"
    response_json: str | None = None
    events: list[Event] = Field(min_length=1)
    redactions: list[RedactionRecord] = Field(default_factory=list)
    provenance: str | None = None
    assertions: list[AssertionEvidence] = Field(default_factory=list)
    drift: DriftEvidence | None = None
    replay: ReplayEvidence | None = None

    @model_validator(mode="after")
    def validate_order_and_identifier(self) -> Cassette:
        """Reject non-monotonic events and inconsistent identifiers."""

        indexes = [event.index for event in self.events]
        if any(
            current <= previous
            for previous, current in zip(indexes, indexes[1:], strict=False)
        ):
            raise ValueError("event indexes must be strictly monotonic")
        expected = calculate_content_id(self.events)
        if self.id != expected:
            raise ValueError("cassette identifier does not match its events")
        expected_integrity = calculate_integrity_hash_payload(
            self.model_dump(mode="json", exclude={"integrity_hash"})
        )
        if self.integrity_hash != expected_integrity:
            raise ValueError("cassette integrity hash does not match its contents")
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must include a timezone")
        return self


class ManifestEntry(BaseModel):
    """Store list metadata for one cassette."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[0-9a-f]{64}$")
    provider: Literal["openai", "anthropic", "mcp"]
    model: str
    recorded_at: datetime
    event_count: int = Field(ge=1)


class Manifest(BaseModel):
    """Index all cassettes in one store."""

    model_config = ConfigDict(extra="forbid")

    entries: list[ManifestEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_entries(self) -> Manifest:
        """Reject duplicate cassette identifiers."""

        identifiers = [entry.id for entry in self.entries]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("manifest contains duplicate cassette identifiers")
        return self


class DriftResult(BaseModel):
    """Store one model drift comparison."""

    model_config = ConfigDict(extra="forbid")

    cassette_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    classification: DriftClassification
    dimension: DriftDimension | None = None
    baseline_events: list[Event]
    target_events: list[Event]
    tokens_spent: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_dimension(self) -> DriftResult:
        """Require a dimension only for divergent results."""

        if self.classification is DriftClassification.DIVERGED:
            if self.dimension is None:
                raise ValueError("diverged results require a dimension")
        elif self.dimension is not None:
            raise ValueError("only diverged results may have a dimension")
        return self


class DriftSkipped(BaseModel):
    """Describe a cassette excluded from a live drift classification."""

    model_config = ConfigDict(extra="forbid")

    cassette_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason: str = Field(min_length=1)


class DriftRun(BaseModel):
    """Store classified and explicitly skipped drift inputs."""

    model_config = ConfigDict(extra="forbid")

    target_provider: Literal["openai", "anthropic", "groq"]
    target_model: str = Field(min_length=1)
    results: list[DriftResult] = Field(default_factory=list)
    skipped: list[DriftSkipped] = Field(default_factory=list)

    @property
    def tokens_spent(self) -> int:
        """Return tokens spent by classified provider calls only."""

        return sum(result.tokens_spent for result in self.results)
