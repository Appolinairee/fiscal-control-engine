"use client";

import { CloseIcon, SearchZoomIcon } from "@/public/assets/icons/icons";

import AISidebarFileItem from "./AISidebarFileItem";
import type { SidebarConversation, SidebarFile } from "./aiSidebarData";

export type AISidebarModalMode = "search" | "files";

export default function AISidebarModal({
  mode,
  conversations,
  files,
  onClose,
}: {
  mode: AISidebarModalMode;
  conversations: SidebarConversation[];
  files: SidebarFile[];
  onClose: () => void;
}) {
  const isSearchMode = mode === "search";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/15 p-4 backdrop-blur-[2px]">
      <section className="custom-scrollbar max-h-[calc(100dvh-56px)] w-full max-w-[720px] overflow-y-auto rounded-[22px] bg-white p-4 shadow-[0_28px_90px_rgba(16,39,52,0.18)] ring-1 ring-[#dfeaf0]">
        <div className="flex items-center gap-3 border-b border-black/[0.06] pb-3">
          {isSearchMode ? (
            <>
              <SearchZoomIcon className="size-5 shrink-0 text-[#7c8c96]" />
              <input
                autoFocus
                type="search"
                placeholder="Rechercher..."
                className="min-w-0 flex-1 bg-transparent text-[15px] font-medium text-[#102734] outline-none placeholder:text-[#9aa8b0]"
              />
            </>
          ) : (
            <div className="min-w-0 flex-1">
              <h2 className="text-[15px] font-semibold text-[#102734]">
                Fichiers
              </h2>
              <p className="text-[12px] font-medium text-[#8a98a2]">
                Documents disponibles dans l&apos;espace d&apos;analyse
              </p>
            </div>
          )}
          <button
            type="button"
            aria-label="Fermer"
            onClick={onClose}
            className="flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-full text-[#40515c] transition hover:bg-[#edf4f7]"
          >
            <CloseIcon className="size-5" />
          </button>
        </div>

        <div className="space-y-5 pt-4">
          {isSearchMode && (
            <div>
              <p className="px-2 text-[12px] font-medium text-[#7c8c96]">
                Discussions récentes
              </p>
              <div className="mt-2 space-y-1">
                {conversations.map((conversation) => (
                  <button
                    key={conversation.id}
                    type="button"
                    className="flex w-full cursor-pointer items-center justify-between gap-4 rounded-[14px] px-3 py-2.5 text-left text-[14px] font-medium text-[#203743] transition hover:bg-[#f5f8fa]"
                  >
                    <span className="min-w-0 truncate">{conversation.title}</span>
                    <span className="shrink-0 text-[12px] text-[#9aa8b0]">
                      {conversation.updatedAt}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="px-2 text-[12px] font-medium text-[#7c8c96]">
              {isSearchMode ? "Fichiers" : "Fichiers récents"}
            </p>
            <div className="mt-2 space-y-1">
              {files.map((file) => (
                <AISidebarFileItem key={file.id} file={file} />
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
