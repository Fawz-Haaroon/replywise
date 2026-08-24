from responsible_ai.risk_score import calculate_prototype_risk_level
from domain_types import RiskLevel, Warning, WarningCategory


def warning(category: WarningCategory) -> Warning:
    return Warning(category, "trigger", "reason")


def test_no_warnings_are_low_risk():
    assert calculate_prototype_risk_level([]) == RiskLevel.LOW


def test_invented_detail_is_medium_risk():
    assert calculate_prototype_risk_level([warning(WarningCategory.INVENTED_DETAIL)]) == RiskLevel.MEDIUM


def test_sensitive_information_is_high_risk():
    assert calculate_prototype_risk_level([warning(WarningCategory.SENSITIVE_INFO)]) == RiskLevel.HIGH


def test_two_warnings_are_high_risk():
    warnings = [
        warning(WarningCategory.INVENTED_DETAIL),
        warning(WarningCategory.UNSUPPORTED_COMMITMENT),
    ]
    assert calculate_prototype_risk_level(warnings) == RiskLevel.HIGH