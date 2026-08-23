import pytest

from aureus.domain import IntentState
from aureus.intents import ComputeIntent


def test_unknown_requires_reconciliation() -> None:
    intent = ComputeIntent("1", "idem", "vast", "gpu")
    intent = intent.transition(IntentState.POLICY_CHECK).transition(IntentState.ECONOMICS_CHECK)
    intent = intent.transition(IntentState.READY).transition(IntentState.DISPATCHING).transition(IntentState.UNKNOWN)
    with pytest.raises(ValueError):
        intent.transition(IntentState.READY)
    assert intent.transition(IntentState.RECONCILING).state is IntentState.RECONCILING
