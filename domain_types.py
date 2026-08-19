from dataclasses import dataclass
from enum import Enum
from typing import Literal


class Tone(str, Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    CONCISE = "concise"
    APOLOGETIC = "apologetic"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WarningCategory(str, Enum):
    SENSITIVE_INFO = "sensitive_info"
    UNSUPPORTED_COMMITMENT = "unsupported_commitment"
    UNVERIFIABLE_CLAIM = "unverifiable_claim"
    INVENTED_DETAIL = "invented_detail"


@dataclass(frozen=True)
class EmailContext:
    original_email: str
    tone: Tone
    instruction: str | None


@dataclass(frozen=True)
class ContextAnalysis:
    intent: str
    key_entities: tuple[str, ...]
    detected_requests: tuple[str, ...]


@dataclass(frozen=True)
class Warning:
    category: WarningCategory
    triggering_phrase: str
    explanation: str


@dataclass(frozen=True)
class GroundingDecision:
    is_grounded: bool
    reason: str


@dataclass(frozen=True)
class DraftResult:
    draft_text: str
    analysis: ContextAnalysis
    warnings: tuple[Warning, ...]
    risk_level: RiskLevel
    ai_disclosed: Literal[True] = True