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
    <div className="space-y-3 pt-3">
      <div className="rounded-2xl bg-[#edf4f7] px-4 py-3 text-[13px] font-medium text-[#31424c]">
        <div className="flex flex-wrap items-center gap-2">
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
        <div className="mt-2 rounded-xl bg-white/75 px-3 py-2 text-[13px] text-[#40515c]">
          {chatExchange.question}
        </div>
      </div>

      <div className="rounded-2xl bg-[#f4f8fa] px-4 py-3 text-[14px] leading-6 text-[#31424c]">
        {chatExchange.preAnalysis && (
          <div className="mb-3 grid grid-cols-3 gap-2">
            <Metric label="Lignes" value={chatExchange.preAnalysis.rowCount.toLocaleString("fr-FR")} />
            <Metric label="Colonnes" value={String(chatExchange.preAnalysis.columnCount)} />
            <Metric
              label="Manquantes"
              value={String(chatExchange.preAnalysis.schema.missing_required_columns.length)}
            />
          </div>
        )}
        {isResponding || !chatExchange.answer ? (
          <span className="flex items-center gap-2 font-medium">
            <span className="size-3 animate-spin rounded-full border-2 border-[#31424c]/25 border-t-[#31424c]" />
            Reponse agent en cours...
          </span>
        ) : (
          chatExchange.answer
        )}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white px-3 py-2">
      <div className="text-[11px] font-medium text-[#7a8992]">{label}</div>
      <div className="mt-0.5 text-[15px] font-semibold text-[#102734]">{value}</div>
    </div>
  );
}
