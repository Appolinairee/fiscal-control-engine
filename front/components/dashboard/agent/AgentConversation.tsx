import type { AgentChatExchange } from "@/api/agent/types";
import { formatFileSize } from "@/utils/ui/files";

export default function AgentConversation({
  chatExchange,
  isResponding,
}: {
  chatExchange: AgentChatExchange | null;
  isResponding: boolean;
}) {
  if (!chatExchange) return null;

  return (
    <div className="space-y-4 pt-3">
      <div className="flex flex-col items-end gap-2">
        {chatExchange.attachedFile && (
          <div className="flex max-w-[86%] flex-wrap items-center gap-2 rounded-2xl bg-[#edf4f7] px-3 py-2 text-[13px] font-medium text-[#31424c]">
            <span className="text-emerald-600">✓</span>
            <span className="max-w-[260px] truncate text-[#102734]">
              {chatExchange.attachedFile.filename}
            </span>
            <span className="text-[#667781]">
              {formatFileSize(chatExchange.attachedFile.sizeBytes)}
            </span>
            <span className="text-[#667781]">
              {chatExchange.attachedFile.sheetNames.length} feuille(s)
            </span>
          </div>
        )}
        <div className="max-w-[86%] rounded-2xl bg-[#edf4f7] px-4 py-3 text-[14px] font-medium leading-6 text-[#102734]">
          {chatExchange.question}
        </div>
      </div>

      <div className="px-1 text-[15px] leading-7 text-[#203743]">
        {isResponding || !chatExchange.answer ? (
          <AgentExecutionLoading hasFile={Boolean(chatExchange.attachedFile)} />
        ) : (
          chatExchange.answer
        )}
      </div>
    </div>
  );
}

function AgentExecutionLoading({ hasFile }: { hasFile: boolean }) {
  const steps = hasFile
    ? [
        "Fichier Excel attache",
        "Contexte deterministe pret",
        "Appel du modele",
        "Redaction de la reponse",
      ]
    : ["Question recue", "Appel du modele", "Redaction de la reponse"];

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 font-semibold text-[#203743]">
        <span className="size-3 animate-spin rounded-full border-2 border-[#31424c]/25 border-t-[#31424c]" />
        L'agent prepare sa reponse
      </div>
      <div className="flex flex-wrap gap-2 text-[12px] font-medium text-[#667781]">
        {steps.map((step) => (
          <span key={step} className="rounded-full bg-[#f4f8fa] px-3 py-1.5">
            {step}
          </span>
        ))}
      </div>
    </div>
  );
}
