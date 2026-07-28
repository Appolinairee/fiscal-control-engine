from dataclasses import dataclass

from app.agent.constants import (
    BLOCKED_TAX_DECISION_ANSWER,
    FORBIDDEN_TAX_DECISION_MARKERS,
    OVERSIZED_MODEL_ANSWER,
)


@dataclass(frozen=True)
class AnswerPolicyResult:
    answer: str
    blocked: bool


class AgentAnswerPolicy:
    def __init__(self, max_answer_characters: int = 4_000) -> None:
        if max_answer_characters < 1:
            raise ValueError("max_answer_characters must be positive")
        self._max_answer_characters = max_answer_characters

    def apply(self, answer: str) -> AnswerPolicyResult:
        normalized_answer = answer.lower()
        contains_tax_decision = any(
            marker in normalized_answer for marker in FORBIDDEN_TAX_DECISION_MARKERS
        )
        if contains_tax_decision:
            return AnswerPolicyResult(
                answer=BLOCKED_TAX_DECISION_ANSWER,
                blocked=True,
            )
        if len(answer) > self._max_answer_characters:
            return AnswerPolicyResult(answer=OVERSIZED_MODEL_ANSWER, blocked=True)
        return AnswerPolicyResult(answer=answer, blocked=False)
