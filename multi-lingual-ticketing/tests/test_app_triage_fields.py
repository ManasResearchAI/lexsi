"""Triage omits injection_detected from the requested fields.

Predictions are exact outputs of the selected adversarial checkpoint-1000
(Tiny Aya Global af89d219) for the Triage field set, captured 2026-11-15.
They show that Triage blocks come from guard violations on model output
(unredacted phone, domain/intent mismatch), not from the missing field.
"""

import json

from app.app import _decision, _status, process_ticket


class FakeGenerator:
    def __init__(self, prediction):
        self.prediction = prediction
        self.fields = None

    def generate(self, _message, fields=None):
        self.fields = fields
        return {
            "prediction": self.prediction,
            "raw_response": json.dumps(self.prediction, ensure_ascii=False),
            "generation_confidence_proxy": 0.98,
            "latency_seconds": 0.1,
            "output_tokens": 40,
        }


BALANCE = {
    "language": "eng", "domain": "banking", "intent": "bill_balance",
    "sentiment": "neutral", "entities": [], "redacted_text": "What is my balance?",
}
PHONE_MESSAGE = "Freeze my account; my phone is +2348012345678."
PHONE = {
    "language": "eng", "domain": "banking", "intent": "freeze_account",
    "sentiment": "neutral",
    "entities": [{"type": "PHONE", "text": "+2348012345678"}],
    "redacted_text": PHONE_MESSAGE,
}
THANKS = {
    "language": "eng", "domain": "banking", "intent": "text",
    "sentiment": "positive", "entities": [], "redacted_text": "Thank you for your help!",
}


def test_triage_requests_no_injection_or_escalate_field():
    engine = FakeGenerator(BALANCE)
    process_ticket("What is my balance?", engine)
    assert "injection_detected" not in engine.fields
    assert "escalate" not in engine.fields


def test_attack_lab_still_requests_injection_field():
    engine = FakeGenerator({**BALANCE, "injection_detected": False})
    process_ticket("What is my balance?", engine, include_model_injection=True)
    assert "injection_detected" in engine.fields


def test_triage_output_without_injection_field_is_accepted():
    result, guarded = process_ticket("What is my balance?", FakeGenerator(BALANCE))
    assert guarded.accepted
    assert guarded.violations == []
    assert guarded.model_reported_injection is None
    assert "Ticket accepted" in _status(guarded)
    assert "not asked for" in _decision(result, guarded)


def test_triage_unredacted_phone_is_blocked_for_privacy_only():
    _, guarded = process_ticket(PHONE_MESSAGE, FakeGenerator(PHONE))
    assert guarded.violations == ["unredacted_phone"]
    assert not guarded.accepted
    assert "+2348012345678" not in json.dumps(guarded.sanitized)
    assert "Privacy check failed" in _status(guarded)


def test_triage_domain_intent_mismatch_is_blocked():
    _, guarded = process_ticket("Thank you for your help!", FakeGenerator(THANKS))
    assert guarded.violations == ["domain_intent_mismatch"]
    assert not guarded.accepted
    assert "Output blocked" in _status(guarded)
