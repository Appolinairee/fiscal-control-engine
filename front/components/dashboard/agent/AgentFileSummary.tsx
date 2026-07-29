import type { AgentAttachedFile } from "@/api/agent/types";
import { CloseIcon } from "@/public/assets/icons/icons";
import { formatFileSize } from "@/utils/ui/files";

export default function AgentFileSummary({
  attachedFile,
  onRemoveFile,
}: {
  attachedFile: AgentAttachedFile;
  onRemoveFile: () => void;
}) {
  return (
    <div className="mb-3 rounded-2xl bg-[#edf4f7] px-3 py-2 text-[13px] font-medium text-[#31424c]">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-emerald-600">✓</span>
            <span className="max-w-[240px] truncate text-[#102734]">
              {attachedFile.filename}
            </span>
            <span className="text-[#667781]">
              {formatFileSize(attachedFile.sizeBytes)}
            </span>
          </div>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-[#667781]">
            <span>{attachedFile.sheetNames.length} feuille(s)</span>
            <span>Feuille active: {attachedFile.selectedSheetName || "-"}</span>
          </div>
        </div>
        <button
          type="button"
          aria-label="Retirer le fichier"
          onClick={onRemoveFile}
          className="flex size-7 shrink-0 cursor-pointer items-center justify-center rounded-full text-[#31424c]/60 transition hover:bg-black/[0.06] hover:text-[#31424c]"
        >
          <CloseIcon className="size-3" />
        </button>
      </div>
    </div>
  );
}
