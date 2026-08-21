import re
from typing import Protocol

from domain_types import EmailContext, GroundingDecision, Warning, WarningCategory


class GroundingChecker(Protocol):
    def check_grounding(
        self,
        candidate_sentence: str,
        email_context: EmailContext,
    ) -> GroundingDecision:
        ...


COMMITMENT_SENTENCE_PATTERN = re.compile(
    r"(?P<sentence>[^.!?\n]*(?:I'll|I will|I've|I have|I agree to|I can|"
    r"I am going to|works for me|that works for me)[^.!?\n]*[.!?]?)",
    re.IGNORECASE,
)
REQUEST_ACTION_PATTERN = re.compile(
    r"\b(?:please|can you|could you|would you)\b[^.!?\n]*\b"
    r"(?:send|share|provide|prepare|finish|complete|deliver|confirm)\b",
    re.IGNORECASE,
)
PROMISE_PATTERN = re.compile(
    r"\b(?:i'll|i will|i can|i am going to|i agree to)\b[^.!?\n]*"
    r"\b(?:send|share|provide|prepare|finish|complete|deliver|confirm|schedule)\b",
    re.IGNORECASE,
)
COMPLETION_PATTERN = re.compile(
    r"\b(?:i've|i have|i)\s+(?:completed|finished|sent|prepared|delivered)\b",
    re.IGNORECASE,
)
EXPLICIT_AGREEMENT_PATTERN = re.compile(
    r"\b(?:i can|i will|i'll|i agree to|yes,? i can|confirmed)\b",
    re.IGNORECASE,
)
MAX_PROVIDER_GROUNDING_CHECKS = 3


def detect_unsupported_commitments(
    draft_text: str,
    email_context: EmailContext,
    grounding_checker: GroundingChecker | None = None,
) -> list[Warning]:
    warnings: list[Warning] = []
    for index, candidate_sentence in enumerate(_find_commitment_phrases(draft_text)):
        checker = grounding_checker if index < MAX_PROVIDER_GROUNDING_CHECKS else None
        decision = _evaluate_grounding(candidate_sentence, email_context, checker)
        if decision.is_grounded:
            continue
        warnings.append(
            Warning(
                category=WarningCategory.UNSUPPORTED_COMMITMENT,
                triggering_phrase=candidate_sentence,
                explanation=decision.reason,
            )
        )
    return warnings


def _find_commitment_phrases(draft_text: str) -> list[str]:
    candidates: list[str] = []
    for match in COMMITMENT_SENTENCE_PATTERN.finditer(draft_text):
        sentence = _clean_sentence(match.group("sentence"))
        if sentence and sentence.lower() not in {item.lower() for item in candidates}:
            candidates.append(sentence)
    return candidates


def _evaluate_grounding(
    candidate_sentence: str,
    email_context: EmailContext,
    grounding_checker: GroundingChecker | None,
) -> GroundingDecision:
    source_text = f"{email_context.original_email} {email_context.instruction or ''}"
    lowered_candidate = candidate_sentence.lower()
    lowered_source = source_text.lower()

    if PROMISE_PATTERN.search(candidate_sentence) and REQUEST_ACTION_PATTERN.search(
        email_context.original_email
    ):
        if not _instruction_explicitly_confirms(email_context.instruction):
            return GroundingDecision(
                is_grounded=False,
                reason=(
                    "The draft turns a request into a promise, but the original email "
                    "did not establish that you agreed to complete it."
                ),
            )

    if COMPLETION_PATTERN.search(candidate_sentence) and not _source_states_completion(
        lowered_source
    ):
        return GroundingDecision(
            is_grounded=False,
            reason=(
                "The draft states that an action is completed, but the source and "
                "instruction do not confirm that completion."
            ),
        )

    if "works for me" in lowered_candidate or "that works for me" in lowered_candidate:
        if not _contains_source_detail(candidate_sentence, source_text):
            return GroundingDecision(
                is_grounded=False,
                reason=(
                    "The draft confirms a specific arrangement that is not present "
                    "in the original email or instruction."
                ),
            )

    if _contains_source_detail(candidate_sentence, source_text):
        return GroundingDecision(
            is_grounded=True,
            reason="The specific commitment detail appears in the source.",
        )
    if grounding_checker is not None:
        return grounding_checker.check_grounding(candidate_sentence, email_context)
    return GroundingDecision(
        is_grounded=_contains_source_detail(candidate_sentence, source_text),
        reason=(
            "The draft includes a commitment whose specific detail is not present "
            "in the original email or instruction."
        ),
    )


def _instruction_explicitly_confirms(instruction: str | None) -> bool:
    if instruction is None:
        return False
    return bool(
        re.search(r"\b(?:agree|yes|will|send|share|provide|complete)\b", instruction, re.I)
    )


def _source_states_completion(source_text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:i have|i've|i already)\s+"
            r"(?:completed|finished|sent|prepared|delivered)\b",
            source_text,
            re.IGNORECASE,
        )
    )


def _contains_source_detail(candidate_sentence: str, source_text: str) -> bool:
    candidate_terms = {
        term.lower()
        for term in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", candidate_sentence)
        if term.lower()
        not in {
            "will", "works", "for", "with", "that", "have", "the", "and",
            "this", "your", "you", "from", "into", "after", "before",
            "please", "can", "could", "would", "i", "am", "to",
            "ll", "i'll", "i've",
            "send", "share", "provide", "prepare", "finish", "complete",
            "deliver", "confirm", "schedule", "review", "follow", "up",
        }
    }
    source_terms = {
        term.lower()
        for term in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", source_text)
    }
    return bool(candidate_terms) and candidate_terms <= source_terms


def _clean_sentence(sentence: str) -> str:
    return re.sub(r"\s+", " ", sentence).strip()