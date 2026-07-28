export type AgentFileUploadResponse = {
  session_id: string;
  file_id: string;
  original_filename: string;
  expires_at: string;
  validated_for_agent: boolean;
  rag_indexable: boolean;
  sheet_names: string[];
};

export type AgentAttachedFile = {
  sessionId: string;
  fileId: string;
  filename: string;
  sheetNames: string[];
};

export type AgentErrorResponse = {
  error: {
    code: string;
    message: string;
  };
};

export type AgentRunResponse = {
  answer: string;
  tool_results: Array<{
    tool_name: string;
    ok: boolean;
    output: Record<string, unknown>;
    error_code: string | null;
    error_message: string | null;
  }>;
};
