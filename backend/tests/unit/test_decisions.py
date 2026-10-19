import pytest
from pydantic import ValidationError

from app.decisions import DecisionInput


def test_decisions_accept_only_human_choice_and_bounded_rejection_reason():
    assert DecisionInput(decision="approve").reason is None
    assert DecisionInput(decision="reject", reason="  Synthetic scope unclear  ").reason == "Synthetic scope unclear"
    assert len(DecisionInput(decision="reject", reason="x" * 1000).reason) == 1000


@pytest.mark.parametrize("payload", [{}, {"decision": "approved"}, {"decision": "reject"},
    {"decision": "reject", "reason": " "}, {"decision": "reject", "reason": "x" * 1001},
    {"decision": "reject", "reason": 123}, {"decision": "approve", "reason": "unrequested"},
    {"decision": "approve", "tasks": []}, {"decision": "approve", "decided_by": "forged"}])
def test_invalid_or_forged_decision_is_rejected(payload):
    with pytest.raises(ValidationError):
        DecisionInput.model_validate(payload)
