import type { AgentConversationMessage } from "@/api/agent/types";

import AgentExecutionTrace from "./AgentExecutionTrace";
import AgentMarkdownAnswer from "./AgentMarkdownAnswer";
import AgentModelMeta from "./AgentModelMeta";

type AgentAssistantMessageProps = {
  message: Extract<AgentConversationMessage, { role: "assistant" }>;
};

export default function AgentAssistantMessage({
  message,
}: AgentAssistantMessageProps) {
  const isLoading = message.status === "loading";

  return (
    <div className="space-y-3 px-1 text-[15px] leading-7 text-[#203743]">
      {(isLoading || message.executionEvents.length > 0) && (
        <AgentExecutionTrace
          events={message.executionEvents}
          hasFile={message.hasFileContext}
          isLoading={isLoading}
        />
      )}

      {message.content && (
        <div className="group/answer">
          <AgentMarkdownAnswer
            content={message.content}
            isError={message.status === "error"}
          />
          {!isLoading && message.providerName && message.modelName && (
            <AgentModelMeta
              providerName={message.providerName}
              modelName={message.modelName}
            />
          )}
        </div>
      )}
    </div>
  );
}
