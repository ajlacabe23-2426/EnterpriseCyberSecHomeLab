"""Offline, deterministic *signals* of prompt injection in untrusted text.

These patterns are for educational triage, not a security boundary. They cannot
reliably establish author intent or whether an AI application would comply.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
import re
from typing import Literal

MAX_CHARS = 100_000
MAX_MATCHES_PER_RULE = 3
Severity = Literal["review", "high"]

# These are analyst-supplied labels, never claims of elevated authority.
SOURCE_GUIDANCE: dict[str, str] = {
    "unknown": "Identify where this text came from before taking any action.",
    "direct_user": "Evaluate the request under the application's existing permissions and policies.",
    "retrieved_document": "Treat document instructions as untrusted content, not as directions to the assistant.",
    "tool_output": "Treat external tool results as evidence only; do not execute embedded commands.",
}



@dataclass(frozen=True)
class Rule:
    id: str
    severity: Severity
    explanation: str
    pattern: re.Pattern[str]


def rule(rule_id: str, severity: Severity, explanation: str, expression: str) -> Rule:
    return Rule(rule_id, severity, explanation, re.compile(expression, re.IGNORECASE | re.MULTILINE))


RULES = (
    rule(
        "instruction_override", "review",
        "Text asks an assistant to discard or override prior instructions.",
        r"\b(?:ignore|disregard|override|forget)\b[^\n.!?]{0,70}\b(?:previous|earlier|prior|above|system|developer)\s+(?:instructions|rules|messages|guidelines)\b",
    ),
    rule(
        "role_spoofing", "high",
        "Text imitates a privileged system or developer message boundary.",
        r"(?:^|\n)\s*(?:\[\s*(?:system|developer)\s*\]|(?:system|developer)\s*:|<\s*(?:system|developer)\s*>)",
    ),
    rule(
        "hidden_instruction_disclosure", "high",
        "Text requests disclosure of hidden or privileged instructions.",
        r"\b(?:reveal|print|show|disclose|expose)\b[^\n.!?]{0,90}\b(?:system|developer|hidden|internal)\s+(?:prompt|instructions|message|rules)\b",
    ),
    rule(
        "sensitive_data_transfer", "high",
        "Text requests transferring secrets or sensitive data.",
        r"\b(?:send|upload|transmit|exfiltrate)\b[^\n.!?]{0,90}\b(?:secret|passwords?|api[ -]?keys?|private data|confidential data|access tokens?)\b",
    ),
    rule(
        "silent_tool_action", "review",
        "Text requests quiet or unapproved use of a tool.",
        r"\b(?:use|invoke|call|run)\b[^\n.!?]{0,50}\b(?:tool|function|shell|terminal)\b[^\n.!?]{0,65}\b(?:silently|secretly|without (?:asking|approval)|immediately)\b",
    ),
    rule(
        "trust_boundary_claim", "review",
        "Untrusted content claims elevated authority over assistant behavior.",
        r"\b(?:treat this as|this (?:document|page|text) is)\b[^\n.!?]{0,35}\b(?:system|developer|trusted)\s+(?:prompt|instruction|message)\b",
    ),
)


def scan_text(text: str, *, source_type: str = "unknown") -> dict[str, object]:
    """Return a safe-to-display report without echoing any source text.

    Accepts a non-empty UTF-8-compatible Python string from an *untrusted* source.
    A low-risk result only means these particular heuristics found nothing.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    if not text.strip():
        raise ValueError("Input must contain non-whitespace content")
    if len(text) > MAX_CHARS:
        raise ValueError(f"Input exceeds the {MAX_CHARS} character limit")
    if not isinstance(source_type, str) or source_type not in SOURCE_GUIDANCE:
        raise ValueError("Unsupported source_type; choose a known, untrusted source category")

    findings: list[dict[str, object]] = []
    for check in RULES:
        for match in islice(check.pattern.finditer(text), MAX_MATCHES_PER_RULE):
            findings.append({
                "rule_id": check.id,
                "severity": check.severity,
                "reason": check.explanation,
                "start": match.start(),
                "end": match.end(),
            })
    findings.sort(key=lambda finding: (int(finding["start"]), str(finding["rule_id"])))
    risk = "high" if any(item["severity"] == "high" for item in findings) else ("review" if findings else "low_signal")
    return {
        "schema": "promptguard-lab-v3",
        "source_context": {
            "source_type": source_type,
            "trust_level": "untrusted",
            "handling_guidance": SOURCE_GUIDANCE[source_type],
        },
        "risk": risk,
        "finding_count": len(findings),
        "findings": findings,
        "recommendation": (
            "Keep untrusted content as data; independently review suspicious instructions."
            if findings else
            "No configured rule matched; do not assume this content is safe."
        ),
        "limitations": "Heuristic indicators do not establish intent or safety; labels are analyst-supplied, and false positives and misses are expected.",
    }
