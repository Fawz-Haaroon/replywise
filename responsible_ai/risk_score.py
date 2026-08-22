from domain_types import RiskLevel, Warning, WarningCategory


def calculate_prototype_risk_level(warnings: list[Warning]) -> RiskLevel:
    if not warnings:
        return RiskLevel.LOW
    if any(warning.category == WarningCategory.SENSITIVE_INFO for warning in warnings):
        return RiskLevel.HIGH
    if len(warnings) >= 2:
        return RiskLevel.HIGH
    if any(
        warning.category
        in {WarningCategory.UNVERIFIABLE_CLAIM, WarningCategory.INVENTED_DETAIL}
        for warning in warnings
    ):
        return RiskLevel.MEDIUM
    return RiskLevel.MEDIUM