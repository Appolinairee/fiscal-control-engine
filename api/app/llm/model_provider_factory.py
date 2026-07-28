from app.llm.domain import ModelProvider
from app.llm.fallback_model import FallbackModelProvider
from app.llm.internal_provider import InternalControlledModelProvider
from app.llm.model_registry import ModelRegistry, ModelSpec
from app.llm.resilient_model import ResilientModelProvider

INTERNAL_PROVIDER = "internal"
CONTROLLED_RESPONSE_MODEL = "controlled-response"


def create_model_provider(provider_chain: str) -> ModelProvider:
    registry = ModelRegistry.from_chain(provider_chain)
    providers = tuple(
        ResilientModelProvider(provider=_create_single_provider(spec))
        for spec in (registry.primary, *registry.fallbacks)
    )
    if len(providers) == 1:
        return providers[0]
    return FallbackModelProvider(providers)


def _create_single_provider(spec: ModelSpec) -> ModelProvider:
    if (
        spec.provider_name == INTERNAL_PROVIDER
        and spec.model_name == CONTROLLED_RESPONSE_MODEL
    ):
        return InternalControlledModelProvider()
    raise ValueError(
        f"unsupported model provider until adapter exists: "
        f"{spec.provider_name}:{spec.model_name}",
    )
