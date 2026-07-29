import { postData } from "@/api/core/api";

import type { AgentRunRequest, AgentRunResponse } from "./types";

export const runAgentPreAnalysis = (
  sessionId: string,
  fileId: string,
  sheetName: string
): Promise<AgentRunResponse> =>
  postData<AgentRunResponse>("agent/runs", {
    message: "Analyse la structure de ce Grand Livre avec l'outil analyze_ledger.",
    session_id: sessionId,
    file_id: fileId,
    allowed_tools: ["analyze_ledger"],
    requested_tool: "analyze_ledger",
    sheet_name: sheetName,
  });

export const runAgentChat = ({
  message,
  sessionId,
  fileId,
  sheetName,
}: AgentRunRequest): Promise<AgentRunResponse> =>
  postData<AgentRunResponse>("agent/runs", {
    message,
    session_id: sessionId,
    file_id: fileId,
    allowed_tools: ["list_sheets", "get_columns", "profile_sheet", "analyze_ledger"],
    sheet_name: sheetName,
  });
