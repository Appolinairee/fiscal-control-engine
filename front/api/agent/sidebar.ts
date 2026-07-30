import { getData } from "@/api/core/api";

import type {
  AgentSessionContextResponse,
  AgentSidebarConversationListResponse,
  AgentSidebarFileListResponse,
} from "./types";

export const agentSidebarQueryKeys = {
  conversations: ["agent", "conversations"] as const,
  files: ["agent", "files"] as const,
  sessionContext: (sessionId: string) => ["agent", "sessions", sessionId, "context"],
};

export const listAgentConversations = (
  limit = 20
): Promise<AgentSidebarConversationListResponse> =>
  getData<AgentSidebarConversationListResponse>("agent/conversations", {
    limit: String(limit),
  });

export const listAgentFiles = (
  limit = 20
): Promise<AgentSidebarFileListResponse> =>
  getData<AgentSidebarFileListResponse>("agent/files", {
    limit: String(limit),
  });

export const getAgentSessionContext = (
  sessionId: string
): Promise<AgentSessionContextResponse> =>
  getData<AgentSessionContextResponse>(`agent/sessions/${sessionId}/context`);
