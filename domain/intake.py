from domain_types import EmailContext, Tone


def create_email_context(
    original_email: str,
    tone: Tone,
    instruction: str | None,
) -> EmailContext:
    normalized_email = original_email.strip()
    if not normalized_email:
        raise ValueError(
            "Email intake failed: expected a non-empty original email, received only whitespace."
        )

    normalized_instruction = instruction.strip() if instruction else None
    return EmailContext(
        original_email=normalized_email,
        tone=tone,
        instruction=normalized_instruction or None,
    )