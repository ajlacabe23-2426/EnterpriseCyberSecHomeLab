"""Offline illustration of a policy boundary independent of prompt screening.

This module ONLY computes an explainable simulated verdict. It never dispatches
tools, reads external files, calls models, verifies identities, or issues tokens.
A real service must construct ApprovedScope and request_origin from authenticated
server-side controls, never from a prompt, document, model output, or user flag.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import FrozenSet

from .detector import scan_text


@dataclass(frozen=True)
class ApprovedScope:
    """Fictional approval supplied by a trusted test harness, NOT a credential."""
    subject: str
    grants: FrozenSet[tuple[str, str]]
    expires_at: datetime


def _valid_scope(scope: object) -> bool:
    if not isinstance(scope, ApprovedScope):
        return False
    if not isinstance(scope.subject, str) or not scope.subject.strip():
        return False
    if not isinstance(scope.grants, frozenset):
        return False
    if not all(isinstance(pair, tuple) and len(pair) == 2
               and all(isinstance(value, str) and value.strip() for value in pair)
               for pair in scope.grants):
        return False
    return (isinstance(scope.expires_at, datetime)
            and scope.expires_at.tzinfo is not None
            and scope.expires_at.utcoffset() == timedelta(0))


def assess_action(
    untrusted_text: str,
    *,
    source_type: str,
    request_origin: str,
    resource: str,
    action: str,
    scope: ApprovedScope | None,
    now: datetime,
) -> dict[str, object]:
    """Simulate an independent authorization decision with safe diagnostic metadata.

    The source text is always data. The scan may suggest review, but matching a
    pattern never authorizes an action; neither does a low-signal scan result.
    request_origin is a toy *assertion*, not cryptographic authentication.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("now must be a timezone-aware UTC datetime")
    report = scan_text(untrusted_text, source_type=source_type)
    reason = "POLICY_SCOPE_APPROVED"
    decision = "ALLOW"
    if request_origin != "trusted_workflow":
        reason, decision = "UNTRUSTED_REQUEST_ORIGIN", "DENY"
    elif not _valid_scope(scope):
        reason, decision = "MISSING_OR_INVALID_APPROVAL", "DENY"
    elif scope.expires_at <= now:
        reason, decision = "APPROVAL_EXPIRED", "DENY"
    elif (not isinstance(resource, str) or not resource.strip()
          or not isinstance(action, str) or not action.strip()):
        reason, decision = "INVALID_ACTION", "DENY"
    elif (resource, action) not in scope.grants:
        reason, decision = "LEAST_PRIVILEGE_DENY", "DENY"
    return {
        "schema": "promptguard-action-boundary-v1",
        "decision": decision,
        "reason": reason,
        "tool_executed": False,
        "scan_risk": report["risk"],
        "rule_ids": sorted({finding["rule_id"] for finding in report["findings"]}),
        "analyst_review_recommended": report["risk"] != "low_signal",
        "limitations": "Synthetic verdict only; approval and origin are test fixtures, not authenticated evidence.",
    }
