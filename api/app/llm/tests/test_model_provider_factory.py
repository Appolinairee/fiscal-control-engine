import pytest

from app.llm.audited_model import ModelAuditEvent
from app.llm.domain import ModelMessage, ModelRequest
from app.llm.fallback_model import FallbackModelProvider
from app.llm.model_provider_factory import create_model_provider


def test_factory_creates_internal_controlled_provider() -> None:
    audit_events: list[ModelAuditEvent] = []
    provider = create_model_provider(
        "internal:controlled-response",
        audit_sink=audit_events.append,
    )

    response = provider.generate(_request())

    assert response.provider_name == "internal"
    assert response.model_name == "controlled-response"
    assert "controles deterministes" in response.text
    assert audit_events[0].provider_name == "internal"
    assert audit_events[0].model_name == "controlled-response"
    assert audit_events[0].status == "success"


def test_factory_creates_fallback_chain() -> None:
    provider = create_model_provider(
        "internal:controlled-response,internal:controlled-response",
    )

    assert isinstance(provider, FallbackModelProvider)


def test_factory_rejects_unknown_external_provider_until_adapter_exists() -> None:
    with pytest.raises(ValueError, match="unsupported model provider"):
        create_model_provider("openai:gpt-4.1-mini")


def _request() -> ModelRequest:
    return ModelRequest(
        messages=(ModelMessage(role="user", content="Analyse"),),
        allowed_tools=("profile_sheet",),
        temperature=0.0,
        max_output_tokens=300,
        timeout_seconds=10.0,
    )
