import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { uploadAgentFile } from "@/api/agent/uploadAgentFile";
import { runAgentAnalysis } from "@/api/agent/runAgentAnalysis";
import type { AgentAttachedFile, AgentErrorResponse } from "@/api/agent/types";
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
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);
  const { setAlert } = useAlertStore();

  const analysisMutation = useMutation({
    mutationFn: ({
      sessionId,
      fileId,
      sheetName,
    }: {
      sessionId: string;
      fileId: string;
      sheetName: string;
    }) => runAgentAnalysis(sessionId, fileId, sheetName),
    onSuccess: (response) => {
      console.log("[AgentFile] Analyse terminée", response);
      setAnalysisResult(response.answer);
    },
    onError: (error: unknown) => {
      console.error("[AgentFile] Échec de l'analyse", error);
      setUploadError("Le fichier est chargé, mais son analyse a échoué.");
    },
  });

  const mutation = useMutation({
    mutationFn: uploadAgentFile,
    onSuccess: (response) => {
      console.log("[AgentFile] Upload réussi", response);
      setUploadError(null);
      setAttachedFile({
        sessionId: response.session_id,
        fileId: response.file_id,
        filename: response.original_filename,
        sheetNames: response.sheet_names,
      });
      analysisMutation.mutate({
        sessionId: response.session_id,
        fileId: response.file_id,
        sheetName: response.sheet_names[0],
      });
    },
    onError: (error: unknown) => {
      console.error("[AgentFile] Échec de l'upload", error);
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
    setAnalysisResult(null);
    console.log("[AgentFile] Validation du fichier", {
      nom: file.name,
      taille: file.size,
      type: file.type,
    });
    if (!hasAcceptedExtension(file.name)) {
      const message =
        "Seuls les fichiers Excel (.xlsx, .xlsm) sont acceptes pour le moment.";
      console.warn("[AgentFile] Extension refusée", file.name);
      setAlert({
        content: message,
        type: AlertTypeStatus.ERROR,
      });
      setUploadError(message);
      return;
    }

    mutation.mutate(file);
  };

  const removeFile = () => {
    setAttachedFile(null);
    setUploadError(null);
    setAnalysisResult(null);
    analysisMutation.reset();
    mutation.reset();
  };

  return {
    attachedFile,
    isUploading: mutation.isPending,
    isAnalyzing: analysisMutation.isPending,
    uploadError,
    analysisResult,
    addFile,
    removeFile,
  };
};
