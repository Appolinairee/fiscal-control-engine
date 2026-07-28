from app.config import get_settings
from app.llm.model_provider_factory import create_model_provider
from app.llm.smoke_check import LLMProviderSmokeCheck


def main() -> int:
    settings = get_settings()
    api_key = (
        settings.llm_openai_compatible_api_key.get_secret_value()
        if settings.llm_openai_compatible_api_key is not None
        else None
    )
    if "openai-compatible:" in settings.llm_provider_chain and not api_key:
        print("LLM smoke check skipped: missing LLM_OPENAI_COMPATIBLE_API_KEY")
        return 2

    provider = create_model_provider(
        provider_chain=settings.llm_provider_chain,
        openai_compatible_api_key=api_key,
        openai_compatible_base_url=settings.llm_openai_compatible_base_url,
    )
    result = LLMProviderSmokeCheck(provider=provider).run()
    print(
        "LLM smoke check ok: "
        f"provider={result.provider_name} "
        f"model={result.model_name} "
        f"finish_reason={result.finish_reason}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
