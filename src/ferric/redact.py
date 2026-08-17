"""Remove sensitive values before a cassette reaches disk."""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern
from typing import Any, cast

from pydantic import TypeAdapter

from ferric.schema import (
    Cassette,
    Event,
    RedactionRecord,
    calculate_content_id,
)


@dataclass(frozen=True)
class RedactionRule:
    """Define a named regular expression used for safe replacement."""

    rule_class: str
    pattern: Pattern[str]

    @classmethod
    def from_pattern(cls, rule_class: str, pattern: str) -> RedactionRule:
        """Build a custom rule from a regular expression string."""

        if not rule_class:
            raise ValueError("rule_class must not be empty")
        return cls(rule_class, re.compile(pattern))


BUILT_IN_RULES: tuple[RedactionRule, ...] = (
    RedactionRule("api_key", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]+")),
    RedactionRule(
        "bearer_token",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    ),
    RedactionRule(
        "email",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    ),
    RedactionRule("card", re.compile(r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)")),
)

_EVENT_ADAPTER = TypeAdapter(list[Event])


class Redactor:
    """Apply built-in and custom redaction rules to nested data."""

    def __init__(self, custom_rules: tuple[RedactionRule, ...] = ()) -> None:
        """Initialise a redactor with optional user-declared rules."""

        self.rules = BUILT_IN_RULES + custom_rules

    def redact_cassette(self, cassette: Cassette) -> Cassette:
        """Return a redacted cassette with a recalculated content identifier."""

        records = list(cassette.redactions)
        event_payloads: list[dict[str, Any]] = []
        for event in cassette.events:
            payload = event.model_dump(mode="json")
            redacted = self._walk(
                payload,
                event.index,
                "$",
                records,
            )
            event_payloads.append(cast(dict[str, Any], redacted))

        events = _EVENT_ADAPTER.validate_python(event_payloads)
        request = cast(
            dict[str, Any],
            self._walk(cassette.request, -1, "$.request", records),
        )
        response = self._walk(cassette.response, -1, "$.response", records)
        response_json = cast(
            str | None,
            self._walk(cassette.response_json, -1, "$.response_json", records),
        )
        data = cassette.model_dump(mode="json")
        assertions = self._walk(data["assertions"], -1, "$.assertions", records)
        drift = self._walk(data["drift"], -1, "$.drift", records)
        replay = self._walk(data["replay"], -1, "$.replay", records)
        provenance = self._walk(data["provenance"], -1, "$.provenance", records)
        data.update(
            {
                "id": calculate_content_id(events),
                "request": request,
                "response": response,
                "response_json": response_json,
                "events": [event.model_dump(mode="json") for event in events],
                "redactions": [record.model_dump(mode="json") for record in records],
                "assertions": assertions,
                "drift": drift,
                "replay": replay,
                "provenance": provenance,
            }
        )
        return Cassette.model_validate(data)

    def find_sensitive(self, value: Any, path: str = "$") -> list[tuple[str, str]]:
        """Return safe paths and rule classes for unredacted values."""

        findings: list[tuple[str, str]] = []
        self._scan(value, path, findings)
        return findings

    def _replace(
        self,
        value: str,
        event_index: int,
        path: str,
        records: list[RedactionRecord],
    ) -> str:
        result = value
        for rule in self.rules:
            if rule.pattern.search(result):
                records.append(
                    RedactionRecord(
                        rule_class=rule.rule_class,
                        event_index=event_index,
                        field_path=path,
                    )
                )
                result = rule.pattern.sub(f"[REDACTED:{rule.rule_class}]", result)
        return result

    def _walk(
        self,
        value: Any,
        event_index: int,
        path: str,
        records: list[RedactionRecord],
    ) -> Any:
        if isinstance(value, str):
            return self._replace(value, event_index, path, records)
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for key, child in value.items():
                safe_key = self._replace(
                    str(key), event_index, f"{path}.<key>", records
                )
                redacted[safe_key] = self._walk(
                    child,
                    event_index,
                    f"{path}.{safe_key}",
                    records,
                )
            return redacted
        if isinstance(value, list):
            return [
                self._walk(child, event_index, f"{path}[{index}]", records)
                for index, child in enumerate(value)
            ]
        return value

    def _scan(
        self,
        value: Any,
        path: str,
        findings: list[tuple[str, str]],
    ) -> None:
        if isinstance(value, str):
            for rule in self.rules:
                if rule.pattern.search(value):
                    findings.append((path, rule.rule_class))
        elif isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                for rule in self.rules:
                    if rule.pattern.search(key_text):
                        findings.append((f"{path}.<key>", rule.rule_class))
                self._scan(child, f"{path}.{key_text}", findings)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._scan(child, f"{path}[{index}]", findings)


def redact_cassette(
    cassette: Cassette,
    custom_rules: tuple[RedactionRule, ...] = (),
) -> Cassette:
    """Redact one cassette using built-in and optional custom rules."""

    return Redactor(custom_rules).redact_cassette(cassette)
