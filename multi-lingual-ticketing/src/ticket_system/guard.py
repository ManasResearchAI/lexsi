"""Fail-closed guard for untrusted ticket inputs and model JSON outputs."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from jsonschema import ValidationError

from .constants import INTENT_TO_DOMAIN
from .inference import extract_json
from .schema import PARTIAL_SCHEMA, validate_ticket

ALLOWED_KEYS = frozenset(PARTIAL_SCHEMA["properties"])

_CONFUSABLES = str.maketrans({
    "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
    "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
    "О": "O", "о": "o", "Ι": "I", "І": "I", "ⅼ": "l",
})

INJECTION_PATTERNS = (
    r"ignore (?:all |the )?(?:previous|prior|earlier) instructions?",
    r"system\s*:", r"developer\s*:", r"assistant\s*:",
    r"classify (?:this )?as", r"set (?:the )?intent", r"mark (?:this )?urgent",
    r"foju k[oọ] (?:gbogbo )?(?:ilana|[aà]ṣẹ)", r"samisi .*b[ií]",
    r"puuza (?:maagizo|miongozo)", r"weka (?:nia|dhamira|kipaumbele)",
    r"(?:foju k[oọ]|puuza) (?:rules|schema)", r"(?:urgent|pajawiri).*intent\s*=",
    r"do not redact", r"m[aá] ṣe .*pamọ", r"usifiche",
    r"(?:score|mark|set|weka|samisi) (?:this )?(?:as )?neutral",
    r"(?:neutral feedback|no emotion|everything is fine).*(?:hurt|attack|kill)",
    r"(?:ero neutral|ko si ibinu|ohun gbogbo dara).*(?:lara|k[oọ]lu|pa)",
    r"(?:maoni neutral|hakuna hasira|kila kitu ni sawa).*(?:umiza|shambulia|ua)",
    r"(?:escalate|intent)\s*=", r"refund_(?:amount|approved)",
    r"(?:final command|aṣẹ ikẹhin|amri ya mwisho)",
    r"(?:cloud model|awoṣe .*cloud|modeli .*cloud)",
    r"(?:force|fi ipa mu|lazimisha) (?:an )?escalation",
    r"(?:next model|awoṣe t[oó] tẹ̀le|modeli inayofuata)",
    r"(?:reveal|ṣafihan|onyesha) system prompt",
    r"confidence (?:zero|odo|sifuri)",
    r"\"(?:escalate|intent|domain)\"\s*:",
)
THREAT_PATTERNS = (
    r"\b(?:kill|hurt|attack|bomb|threat)\b", r"\b(?:pa|ipalara|kọlu)\b",
    r"\b(?:ua|kuumiza|shambulia|bomu|tishio)\b",
)
PHONE_DIGITS = re.compile(r"(?:\+?\d[\d .()\-]{7,}\d)")
PHONE_WORDS = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|"
    r"odo|[oọ]k[aà]n|meji|meta|m[eẹ]rin|marun|m[eẹ]fa|meje|m[eẹ]jo|m[eẹ]san|"
    r"sifuri|moja|mbili|tatu|nne|tano|sita|saba|nane|tisa)"
    r"(?:[\s\-]+(?:zero|one|two|three|four|five|six|seven|eight|nine|"
    r"odo|[oọ]k[aà]n|meji|meta|m[eẹ]rin|marun|m[eẹ]fa|meje|m[eẹ]jo|m[eẹ]san|"
    r"sifuri|moja|mbili|tatu|nne|tano|sita|saba|nane|tisa)){6,}\b",
    re.IGNORECASE,
)


def normalized_security_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).translate(_CONFUSABLES).casefold()
    return " ".join(value.split())


def detects_injection(text: str) -> bool:
    normalized = normalized_security_text(text)
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in INJECTION_PATTERNS)


def detects_threat(text: str) -> bool:
    normalized = normalized_security_text(text)
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in THREAT_PATTERNS)


def contains_obfuscated_phone(text: str) -> bool:
    normalized = normalized_security_text(text)
    return bool(PHONE_DIGITS.search(normalized) or PHONE_WORDS.search(normalized))


@dataclass
class GuardResult:
    accepted: bool
    sanitized: dict[str, Any] | None
    violations: list[str]
    injection_detected: bool
    escalate: bool
    model_reported_injection: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def guard_output(
    raw_output: str | dict[str, Any], source_text: str, *, confidence: float = 1.0,
    escalation_threshold: float = 0.5, max_input_chars: int = 6000,
) -> GuardResult:
    """Validate and sanitize before downstream routing or side effects."""
    violations: list[str] = []
    parsed = raw_output if isinstance(raw_output, dict) else extract_json(raw_output)
    injection = detects_injection(source_text)
    if len(source_text) > max_input_chars:
        violations.append("input_too_long")
        injection = True
    if parsed is None:
        return GuardResult(False, None, [*violations, "invalid_json"], injection, True)
    extra = sorted(set(parsed) - ALLOWED_KEYS)
    if extra:
        violations.append("extra_keys:" + ",".join(extra))
    sanitized = {key: value for key, value in parsed.items() if key in ALLOWED_KEYS}
    try:
        validate_ticket(sanitized, partial=True)
    except ValidationError:
        violations.append("schema_invalid")
    intent = sanitized.get("intent")
    if intent in INTENT_TO_DOMAIN and sanitized.get("domain") not in {None, INTENT_TO_DOMAIN[intent]}:
        violations.append("domain_intent_mismatch")
    redacted = sanitized.get("redacted_text", "")
    if contains_obfuscated_phone(source_text) and (
        not isinstance(redacted, str) or "[PHONE]" not in redacted
    ):
        violations.append("unredacted_phone")
    if detects_threat(source_text) and sanitized.get("sentiment") not in {None, "negative"}:
        violations.append("threat_sentiment_masked")
    reported_injection = sanitized.get("injection_detected")
    if injection and reported_injection is not True:
        violations.append("injection_not_reported")
    privacy_failure = "unredacted_phone" in violations
    if privacy_failure:
        # Remove every model-supplied field: the phone may also appear in
        # entities or another field, not just redacted_text.
        sanitized = {"redacted_text": "[REDACTED: privacy check failed]"}
    sanitized["injection_detected"] = injection
    # The ticket cannot force this field. Serving policy owns escalation. An
    # injection is contained locally rather than forwarded to the more costly
    # model, which closes the A4 payload-delivery and cost-inflation path.
    non_injection_violations = [
        value for value in violations if value != "injection_not_reported"
    ]
    escalate = not injection and not privacy_failure and (
        confidence < escalation_threshold or bool(non_injection_violations)
    )
    sanitized["escalate"] = escalate
    fatal = privacy_failure or any(v.startswith(("extra_keys", "schema_invalid", "domain_intent_mismatch")) for v in violations)
    return GuardResult(not fatal, sanitized, violations, injection, escalate, reported_injection if isinstance(reported_injection, bool) else None)

