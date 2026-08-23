from __future__ import annotations

from dataclasses import dataclass

from .domain import IntentState


_ALLOWED: dict[IntentState, frozenset[IntentState]] = {
    IntentState.CREATED: frozenset({IntentState.POLICY_CHECK, IntentState.FAILED_FINAL}),
    IntentState.POLICY_CHECK: frozenset({IntentState.ECONOMICS_CHECK, IntentState.WAITING_APPROVAL, IntentState.FAILED_FINAL}),
    IntentState.ECONOMICS_CHECK: frozenset({IntentState.WAITING_APPROVAL, IntentState.READY, IntentState.FAILED_FINAL}),
    IntentState.WAITING_APPROVAL: frozenset({IntentState.READY, IntentState.FAILED_FINAL}),
    IntentState.READY: frozenset({IntentState.DISPATCHING, IntentState.FAILED_FINAL}),
    IntentState.DISPATCHING: frozenset({IntentState.DISPATCHED, IntentState.UNKNOWN}),
    IntentState.DISPATCHED: frozenset({IntentState.CONFIRMED, IntentState.UNKNOWN}),
    IntentState.UNKNOWN: frozenset({IntentState.RECONCILING}),
    IntentState.RECONCILING: frozenset({IntentState.CONFIRMED, IntentState.FAILED_FINAL}),
    IntentState.CONFIRMED: frozenset(),
    IntentState.FAILED_FINAL: frozenset(),
}


@dataclass(frozen=True)
class ComputeIntent:
    intent_id: str
    idempotency_key: str
    provider: str
    resource_id: str
    state: IntentState = IntentState.CREATED

    def transition(self, target: IntentState) -> "ComputeIntent":
        if target not in _ALLOWED[self.state]:
            raise ValueError(f"invalid transition: {self.state} -> {target}")
        return ComputeIntent(self.intent_id, self.idempotency_key, self.provider, self.resource_id, target)
