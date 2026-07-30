import type { AgentConversationMessage } from "@/api/agent/types";

import AgentAssistantMessage from "./AgentAssistantMessage";
import AgentUserMessage from "./AgentUserMessage";

export default function AgentConversation({
  messages,
}: {
  messages: AgentConversationMessage[];
}) {
  if (messages.length === 0) return null;

  return (
    <div className="space-y-5 pt-3">
      {messages.map((message) =>
        message.role === "user" ? (
          <AgentUserMessage key={message.id} message={message} />
        ) : (
          <AgentAssistantMessage key={message.id} message={message} />
        )
      )}
    </div>
  );
}
