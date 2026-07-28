from app.llm.domain import ModelRequest, ModelResponse


class InternalControlledModelProvider:
    provider_name = "internal"
    model_name = "controlled-response"

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            text=(
                "Le modele externe n'est pas configure. "
                "Les controles deterministes et les tools internes restent disponibles."
            ),
            provider_name=self.provider_name,
            model_name=self.model_name,
            finish_reason="controlled_response",
            tool_calls=(),
        )
