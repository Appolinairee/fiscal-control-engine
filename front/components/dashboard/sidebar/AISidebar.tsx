"use client";

import { useState } from "react";

import { ChevronRightIcon } from "@/public/assets/icons/AgentInputIcons";
import { SearchZoomIcon } from "@/public/assets/icons/icons";
import { AddSquareIcon, CategoryIcon } from "@/public/assets/icons/SideBarIcons";

import AISidebarConversationItem from "./AISidebarConversationItem";
import AISidebarModal, { type AISidebarModalMode } from "./AISidebarModal";
import { sidebarConversations, sidebarFiles } from "./aiSidebarData";

export default function AISidebar() {
  const [isRecentExpanded, setIsRecentExpanded] = useState(false);
  const [modalMode, setModalMode] = useState<AISidebarModalMode | null>(null);

  const visibleConversations = isRecentExpanded
    ? sidebarConversations
    : sidebarConversations.slice(0, 3);
  const hiddenCount = sidebarConversations.length - visibleConversations.length;

  return (
    <>
      <div className="flex min-h-full flex-col gap-7 text-[#102734]">
        <div className="space-y-1.5">
          <button
            type="button"
            className="flex h-11 w-full cursor-pointer items-center gap-3 rounded-[17px] bg-[#f5f8fa] px-3.5 text-left text-[14px] font-medium text-[#102734] shadow-[inset_0_1px_0_rgba(255,255,255,0.75)] transition hover:bg-[#edf4f7]"
          >
            <AddSquareIcon className="size-[18px] shrink-0 text-[#40515c]" />
            Nouveau chat
          </button>
          <button
            type="button"
            onClick={() => setModalMode("files")}
            className="flex h-10 w-full cursor-pointer items-center gap-3 rounded-[12px] px-3.5 text-left text-[14px] font-medium text-[#203743] transition hover:bg-[#f7f9fa]"
          >
            <CategoryIcon className="size-[18px] shrink-0 text-[#667781]" />
            Fichiers
          </button>
          <button
            type="button"
            onClick={() => setModalMode("search")}
            className="flex h-10 w-full cursor-pointer items-center gap-3 rounded-[12px] px-3.5 text-left text-[14px] font-medium text-[#203743] transition hover:bg-[#f7f9fa]"
          >
            <SearchZoomIcon className="size-[18px] shrink-0 text-[#667781]" />
            Rechercher
          </button>
        </div>

        <section className="space-y-2">
          <button
            type="button"
            onClick={() => setIsRecentExpanded((current) => !current)}
            className="flex h-8 w-full cursor-pointer items-center justify-between rounded-[10px] px-3 text-left text-[12px] font-semibold text-[#31424c] transition hover:bg-[#f7f9fa]"
          >
            <span>Récents</span>
            <ChevronRightIcon
              className={[
                "size-3.5 text-[#8a98a2] transition-transform",
                isRecentExpanded ? "rotate-90" : "",
              ].join(" ")}
            />
          </button>
          <div className="space-y-1">
            {visibleConversations.map((conversation) => (
              <AISidebarConversationItem
                key={conversation.id}
                conversation={conversation}
              />
            ))}
          </div>
          {!isRecentExpanded && hiddenCount > 0 && (
            <button
              type="button"
              onClick={() => setIsRecentExpanded(true)}
              className="h-8 w-full cursor-pointer rounded-[10px] px-3 text-left text-[12px] font-medium text-[#8a98a2] transition hover:bg-[#f7f9fa]"
            >
              Afficher {hiddenCount} ancien{hiddenCount > 1 ? "s" : ""}
            </button>
          )}
        </section>
      </div>
      {modalMode && (
        <AISidebarModal
          mode={modalMode}
          conversations={sidebarConversations}
          files={sidebarFiles}
          onClose={() => setModalMode(null)}
        />
      )}
    </>
  );
}
