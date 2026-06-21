"""Risk assessment for engineering change packages."""

from __future__ import annotations

from enum import Enum

from shared.constants import DEFAULT_CONFIDENCE_THRESHOLD


class ChangeRiskLevel(str, Enum):
    """Advisory risk level for proposed configuration changes."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def assess_change_risk(
    confidence: float,
    *,
    has_likely_root_cause: bool = True,
    requires_engineer_approval: bool = False,
    template_risk: ChangeRiskLevel | None = None,
) -> ChangeRiskLevel:
    """Assign advisory risk from investigation confidence and change characteristics."""
    if template_risk is not None:
        return template_risk

    if not has_likely_root_cause or confidence < 40:
        return ChangeRiskLevel.LOW

    if requires_engineer_approval and confidence >= DEFAULT_CONFIDENCE_THRESHOLD:
        return ChangeRiskLevel.HIGH

    if confidence >= 90:
        return ChangeRiskLevel.MEDIUM

    if confidence >= DEFAULT_CONFIDENCE_THRESHOLD:
        return ChangeRiskLevel.MEDIUM

    return ChangeRiskLevel.LOW


def format_risk_summary(risk_level: ChangeRiskLevel, *, has_likely_root_cause: bool) -> str:
    """Return a short advisory risk narrative."""
    if not has_likely_root_cause:
        return (
            "Insufficient investigation confidence to propose configuration changes. "
            "Collect additional evidence before CAB review."
        )

    narratives = {
        ChangeRiskLevel.LOW: (
            "Low advisory risk. Changes are informational or require further validation "
            "before implementation."
        ),
        ChangeRiskLevel.MEDIUM: (
            "Medium advisory risk. Configuration examples should be reviewed against "
            "the current baseline during a standard change window."
        ),
        ChangeRiskLevel.HIGH: (
            "High advisory risk. Proposed changes affect production voice routing or "
            "signaling and require engineer approval plus rollback planning."
        ),
        ChangeRiskLevel.CRITICAL: (
            "Critical advisory risk. Changes may impact cluster-wide call processing. "
            "Require maintenance window, CAB approval, and tested rollback."
        ),
    }
    return narratives[risk_level]
