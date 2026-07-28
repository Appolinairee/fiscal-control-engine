"use client";

import { useState } from "react";

import { PlusIcon } from "@/public/assets/icons/icons";
import {
  ArrowUpIcon,
  GlobalIcon,
  ScannerIcon,
  SlidersIcon,
} from "@/public/assets/icons/AgentInputIcons";

import AgentToolbarButton from "./AgentToolbarButton";

type AgentWorkState = "idle" | "searching";

const placeholder =
  "Demandez a l'agent d'analyser un compte, une ecriture ou une retenue a la source...";

export default function AgentPromptCard() {
  const [state, setState] = useState<AgentWorkState>("idle");
  const isSearching = state === "searching";

  return (
    <div className="w-full max-w-[640px]">
      <AgentPromptShell>
        <AgentPromptInput onSubmit={() => setState("searching")} />
        <AgentPromptStatusBar
          state={state}
          onStop={() => setState("idle")}
        />
      </AgentPromptShell>
    </div>
  );
}

function AgentPromptShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-[40px] border-[6px] border-[#deebf1] bg-[#deebf1] shadow-[0_24px_54px_rgba(86,105,118,0.12)]">
      {children}
    </div>
  );
}

function AgentPromptInput({ onSubmit }: { onSubmit: () => void }) {
  return (
    <div className="rounded-b-[18px] rounded-t-[25px] bg-white px-5 pb-4 pt-5">
      <label className="block">
        <span className="sr-only">Prompt Fiscal Agent</span>
        <textarea
          rows={2}
          placeholder={placeholder}
          className="block min-h-[60px] w-full resize-none bg-transparent text-[16px] leading-6 text-black outline-none placeholder:text-black/45"
        />
      </label>

      <div className="mt-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <AgentToolbarButton label="Ajouter" variant="primary">
            <PlusIcon className="size-[17px]" />
          </AgentToolbarButton>
          <AgentToolbarButton label="Connecteurs">
            <GlobalIcon className="size-[18px]" />
          </AgentToolbarButton>
          <AgentToolbarButton label="Selectionner un contexte">
            <ScannerIcon className="size-[18px]" />
          </AgentToolbarButton>
          <AgentToolbarButton label="Reglages">
            <SlidersIcon className="size-[18px]" />
          </AgentToolbarButton>
        </div>

        <button
          type="button"
          aria-label="Envoyer"
          onClick={onSubmit}
          className="flex size-[46px] shrink-0 cursor-pointer items-center justify-center rounded-full bg-[#40515c] text-white shadow-[0_14px_28px_rgba(64,81,92,0.20)] transition hover:bg-[#34434c]"
        >
          <ArrowUpIcon className="size-[20px]" />
        </button>
      </div>
    </div>
  );
}

function AgentPromptStatusBar({
  state,
  onStop,
}: {
  state: AgentWorkState;
  onStop: () => void;
}) {
  const isSearching = state === "searching";

  return (
    <div className="flex min-h-[56px] items-center justify-between gap-4 bg-[#c0d4dd] px-4 py-3 rounded-t-[18px] rounded-b-[30px] mt-2">
      <div className="flex items-center gap-2">
        <span className="rounded-full bg-[#dce5ea] px-3 py-2 text-[12px] font-semibold text-[#25313a] shadow-[inset_0_1px_0_rgba(255,255,255,0.55)]">
          Fiscal Agent
        </span>
        <span className="rounded-full bg-white/72 px-3 py-2 text-[12px] font-semibold text-[#50606b] shadow-[inset_0_1px_0_rgba(255,255,255,0.75)]">
          {isSearching ? "Analyse en cours" : "Pret a analyser"}
        </span>
      </div>

      <div className="flex min-w-0 items-center gap-3">
        <p className="hidden truncate text-[12px] font-medium text-[#6d7b86] sm:block">
          {isSearching
            ? "Recherche dans les donnees connectees..."
            : "En attente d'une question fiscale..."}
        </p>
        <button
          type="button"
          disabled={!isSearching}
          onClick={onStop}
          className="cursor-pointer rounded-full bg-[#d4dee4] px-4 py-2 text-[12px] font-semibold text-[#53616b] transition hover:bg-[#c7d3da] disabled:cursor-default disabled:opacity-55"
        >
          Stop
        </button>
      </div>
    </div>
  );
}
