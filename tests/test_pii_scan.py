from responsible_ai.pii_scan import scan_for_sensitive_information
from domain_types import WarningCategory


def test_detects_indian_phone_number_with_country_code():
    warnings = scan_for_sensitive_information("Reach me at +91 98765 43210 anytime.")
    assert any(warning.category == WarningCategory.SENSITIVE_INFO for warning in warnings)


def test_detects_email_address():
    warnings = scan_for_sensitive_information("Contact rahul.k@example.com if needed.")
    assert any("rahul.k@example.com" in warning.triggering_phrase for warning in warnings)


def test_detects_social_security_number():
    warnings = scan_for_sensitive_information("The SSN is 123-45-6789.")
    assert any("Social Security number" in warning.explanation for warning in warnings)


def test_detects_account_number_near_financial_label():
    warnings = scan_for_sensitive_information("My account number is 123456789012.")
    assert any("Financial identifier" in warning.explanation for warning in warnings)


def test_detects_pan_identifier():
    warnings = scan_for_sensitive_information("The PAN is ABCDE1234F.")
    assert any(warning.triggering_phrase == "ABCDE1234F" for warning in warnings)


def test_detects_otp():
    warnings = scan_for_sensitive_information("The OTP is 482913.")
    assert any("one-time code" in warning.explanation for warning in warnings)


def test_does_not_flag_a_plain_date_as_phone_number():
    warnings = scan_for_sensitive_information("Let's confirm for 21 08 2026.")
    assert not any("Phone number" in warning.explanation for warning in warnings)