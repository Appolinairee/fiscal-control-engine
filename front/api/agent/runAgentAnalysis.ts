import { postData } from "@/api/core/api";

import type { AgentRunResponse } from "./types";

export const runAgentAnalysis = (
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
