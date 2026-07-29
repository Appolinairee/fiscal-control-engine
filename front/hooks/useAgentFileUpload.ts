import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { uploadAgentFile } from "@/api/agent/uploadAgentFile";
import { runAgentChat, runAgentPreAnalysis } from "@/api/agent/runAgentAnalysis";
import type {
  AgentAttachedFile,
  AgentChatExchange,
  AgentErrorResponse,
  AgentRunResponse,
  LedgerPreAnalysis,
} from "@/api/agent/types";
import { ApiError } from "@/utils/api/errors";
import useAlertStore, { AlertTypeStatus } from "@/store/alertStore";

export const AGENT_UPLOAD_ACCEPTED_EXTENSIONS = [".xlsx", ".xlsm"];

const hasAcceptedExtension = (filename: string): boolean => {
  const lowerCaseFilename = filename.toLowerCase();
  return AGENT_UPLOAD_ACCEPTED_EXTENSIONS.some((extension) =>
    lowerCaseFilename.endsWith(extension)
  );
};

export const useAgentFileUpload = () => {
  const [attachedFile, setAttachedFile] = useState<AgentAttachedFile | null>(null);
  const [pendingFile, setPendingFile] = useState<{ filename: string; sizeBytes: number } | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [preAnalysis, setPreAnalysis] = useState<LedgerPreAnalysis | null>(null);
  const [preAnalysisError, setPreAnalysisError] = useState<string | null>(null);
  const [chatExchange, setChatExchange] = useState<AgentChatExchange | null>(null);
  const { setAlert } = useAlertStore();

  const preAnalysisMutation = useMutation({
    mutationFn: ({
      sessionId,
      fileId,
      sheetName,
    }: {
      sessionId: string;
      fileId: string;
      sheetName: string;
    }) => runAgentPreAnalysis(sessionId, fileId, sheetName),
    onSuccess: (response) => {
      setPreAnalysisError(null);
      setPreAnalysis(extractLedgerPreAnalysis(response));
    },
    onError: () => {
      setPreAnalysis(null);
      setPreAnalysisError("La pre-analyse deterministe a echoue.");
    },
  });

  const chatMutation = useMutation({
    mutationFn: ({
      message,
      sessionId,
      fileId,
      sheetName,
    }: {
      message: string;
      sessionId?: string;
      fileId?: string;
      sheetName?: string;
    }) => runAgentChat({ message, sessionId, fileId, sheetName }),
    onSuccess: (response) => {
      setChatExchange((currentExchange) =>
        currentExchange
          ? {
              ...currentExchange,
              answer: response.answer,
            }
          : null
      );
    },
    onError: () => {
      setChatExchange((currentExchange) =>
        currentExchange
          ? {
              ...currentExchange,
              answer: "La reponse agent a echoue. Vous pouvez reformuler ou relancer.",
            }
          : null
      );
    },
  });

  const uploadMutation = useMutation({
    mutationFn: uploadAgentFile,
    onSuccess: (response, file) => {
      const selectedSheetName = response.sheet_names[0] || "";
      setUploadError(null);
      setPendingFile(null);
      setPreAnalysis(null);
      setPreAnalysisError(null);
      setChatExchange(null);
      setAttachedFile({
        sessionId: response.session_id,
        fileId: response.file_id,
        filename: response.original_filename,
        sizeBytes: file.size,
        expiresAt: response.expires_at,
        sheetNames: response.sheet_names,
        selectedSheetName,
      });
      preAnalysisMutation.mutate({
        sessionId: response.session_id,
        fileId: response.file_id,
        sheetName: selectedSheetName,
      });
    },
    onError: (error: unknown) => {
      setPendingFile(null);
      const message =
        error instanceof ApiError
          ? (error.data as AgentErrorResponse | undefined)?.error?.message
          : undefined;
      const errorMessage = message || "L'envoi du fichier a echoue.";

      setAlert({
        content: errorMessage,
        type: AlertTypeStatus.ERROR,
      });
      setUploadError(errorMessage);
    },
  });

  const addFile = (file: File) => {
    setUploadError(null);
    setPreAnalysis(null);
    setPreAnalysisError(null);
    setChatExchange(null);
    if (!hasAcceptedExtension(file.name)) {
      const message =
        "Seuls les fichiers Excel (.xlsx, .xlsm) sont acceptes pour le moment.";
      setAlert({
        content: message,
        type: AlertTypeStatus.ERROR,
      });
      setUploadError(message);
      return;
    }

    setPendingFile({ filename: file.name, sizeBytes: file.size });
    uploadMutation.mutate(file);
  };

  const removeFile = () => {
    setAttachedFile(null);
    setPendingFile(null);
    setUploadError(null);
    setPreAnalysis(null);
    setPreAnalysisError(null);
    setChatExchange(null);
    preAnalysisMutation.reset();
    chatMutation.reset();
    uploadMutation.reset();
  };

  const submitPrompt = (message: string) => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage) return;

    if (!attachedFile) {
      const errorMessage = "Ajoutez d'abord un fichier Excel.";
      setUploadError(errorMessage);
      setAlert({
        content: errorMessage,
        type: AlertTypeStatus.ERROR,
      });
      return;
    }

    setChatExchange({
      question: trimmedMessage,
      attachedFile,
      preAnalysis,
      answer: null,
    });
    chatMutation.mutate({
      message: trimmedMessage,
      sessionId: attachedFile.sessionId,
      fileId: attachedFile.fileId,
      sheetName: attachedFile.selectedSheetName,
    });
  };

  return {
    attachedFile,
    pendingFile,
    isUploading: uploadMutation.isPending,
    isPreAnalyzing: preAnalysisMutation.isPending,
    isResponding: chatMutation.isPending,
    uploadError,
    preAnalysis,
    preAnalysisError,
    chatExchange,
    addFile,
    removeFile,
    submitPrompt,
  };
};

const extractLedgerPreAnalysis = (response: AgentRunResponse): LedgerPreAnalysis | null => {
  const result = response.tool_results.find(
    (toolResult) => toolResult.tool_name === "analyze_ledger" && toolResult.ok
  );
  const output = result?.output;
  if (!isLedgerAnalysisOutput(output)) return null;

  return {
    sheetName: output.sheet_name,
    rowCount: output.row_count,
    columnCount: output.column_count,
    schema: output.schema,
    columns: output.columns,
  };
};

const isLedgerAnalysisOutput = (
  output: Record<string, unknown> | undefined
): output is {
  sheet_name: string;
  row_count: number;
  column_count: number;
  schema: LedgerPreAnalysis["schema"];
  columns: LedgerPreAnalysis["columns"];
} => {
  if (!output) return false;
  return (
    typeof output.sheet_name === "string" &&
    typeof output.row_count === "number" &&
    typeof output.column_count === "number" &&
    isLedgerSchema(output.schema) &&
    Array.isArray(output.columns)
  );
};

const isLedgerSchema = (schema: unknown): schema is LedgerPreAnalysis["schema"] => {
  if (!schema || typeof schema !== "object") return false;
  const candidate = schema as Partial<LedgerPreAnalysis["schema"]>;
  return (
    typeof candidate.is_valid === "boolean" &&
    Array.isArray(candidate.present_columns) &&
    Array.isArray(candidate.missing_required_columns) &&
    Array.isArray(candidate.optional_columns)
  );
};
