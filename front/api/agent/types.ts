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
  sizeBytes: number;
  previewUrl: string | null;
  expiresAt: string;
  sheetNames: string[];
  selectedSheetName: string;
};

export type AgentErrorResponse = {
  error: {
    code: string;
    message: string;
  };
};

export type AgentRunEvent = {
  event_type: string;
  title: string;
  message: string;
  status: "completed" | "running" | "streaming" | "error" | string;
  tool_name: string | null;
  provider_name: string | null;
  model_name: string | null;
};

export type AgentRunResponse = {
  answer: string;
  provider_name: string;
  model_name: string;
  execution_events: AgentRunEvent[];
  tool_results: Array<{
    tool_name: string;
    ok: boolean;
    output: Record<string, unknown>;
    error_code: string | null;
    error_message: string | null;
  }>;
};

export type AgentRunRequest = {
  message: string;
  sessionId?: string;
  fileId?: string;
  sheetName?: string;
};

export type AgentRunStreamMessage =
  | {
      type: "event";
      data: AgentRunEvent;
    }
  | {
      type: "result";
      data: AgentRunResponse;
    };

export type LedgerAnalysisSchema = {
  is_valid: boolean;
  present_columns: string[];
  missing_required_columns: string[];
  optional_columns: string[];
};

export type LedgerAnalysisColumn = {
  name: string;
  position: number;
  detected_type: string;
  non_empty_count: number;
  missing_count: number;
  missing_ratio: number;
};

export type LedgerPreAnalysis = {
  sheetName: string;
  rowCount: number;
  columnCount: number;
  schema: LedgerAnalysisSchema;
  columns: LedgerAnalysisColumn[];
};

export type AgentConversationMessage =
  | {
      id: string;
      role: "user";
      content: string;
      attachedFile: AgentAttachedFile | null;
    }
  | {
      id: string;
      role: "assistant";
      content: string | null;
      status: "loading" | "done" | "error";
      hasFileContext: boolean;
      preAnalysis: LedgerPreAnalysis | null;
      executionEvents: AgentRunEvent[];
      providerName: string | null;
      modelName: string | null;
    };
