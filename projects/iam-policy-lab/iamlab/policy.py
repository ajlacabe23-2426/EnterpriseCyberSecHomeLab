"""Explainable, fail-closed toy IAM decisions. Never modifies an identity system."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping

# These deliberately narrow permissions are a teaching fixture, not a real IAM policy.
PERMISSIONS: dict[str, frozenset[tuple[str, str]]] = {
    "helpdesk": frozenset({("user_profile", "read"), ("password_reset", "request")}),
    "security_analyst": frozenset({("security_event", "read"), ("user_profile", "read")}),
    "auditor": frozenset({("audit_log", "read"), ("user_profile", "read")}),
    "identity_admin": frozenset({("role_assignment", "change"), ("user_profile", "read")}),
}

PRIVILEGED = frozenset({("password_reset", "request"), ("role_assignment", "change")})


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        result = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
        return result if result.tzinfo is not None else None
    except ValueError:
        return None


def evaluate(request: Mapping[str, Any], *, now: datetime) -> dict[str, str]:
    """Return a decision and ordered reason without trusting unspecified attributes.

    For a real system, role, MFA and approval assertions must come from separately
    authenticated/authorized sources. This fixture accepts them ONLY for simulation.
    """
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("now must be a timezone-aware UTC datetime")

    def deny(reason: str) -> dict[str, str]:
        return {"decision": "DENY", "reason": reason}

    if not isinstance(request, Mapping):
        return deny("MALFORMED_REQUEST")
    role, resource, action = (request.get(field) for field in ("role", "resource", "action"))
    if any(not isinstance(v, str) or not v for v in (role, resource, action)):
        return deny("MALFORMED_REQUEST")
    if role not in PERMISSIONS:
        return deny("UNKNOWN_ROLE")
    requested = (resource, action)
    if requested not in PERMISSIONS[role]:
        return deny("LEAST_PRIVILEGE_BLOCK")
    if requested in PRIVILEGED:
        if request.get("self_target") is True:
            return deny("SELF_APPROVAL_PROHIBITED")
        if request.get("mfa_verified") is not True:
            return deny("MFA_REQUIRED")
        if request.get("approval_confirmed") is not True:
            return deny("HUMAN_APPROVAL_REQUIRED")
        expires_at = _utc(request.get("expires_at"))
        if expires_at is None:
            return deny("INVALID_EXPIRY")
        if expires_at <= now:
            return deny("ACCESS_EXPIRED")
        if expires_at - now > timedelta(hours=4):
            return deny("ELEVATION_TOO_LONG")
    return {"decision": "ALLOW", "reason": "POLICY_REQUIREMENTS_MET"}
