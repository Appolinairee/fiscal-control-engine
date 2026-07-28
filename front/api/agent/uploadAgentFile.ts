import { postData } from "@/api/core/api";

import type { AgentFileUploadResponse } from "./types";

export const uploadAgentFile = (file: File): Promise<AgentFileUploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  console.log("[AgentFile] POST /api/agent/files", {
    nom: file.name,
    taille: file.size,
  });
  return postData<AgentFileUploadResponse>("agent/files", formData);
};
