import { PlusIcon } from "@/public/assets/icons/icons";
import {
  ArrowUpIcon,
  GlobalIcon,
  ScannerIcon,
  SlidersIcon,
} from "@/public/assets/icons/AgentInputIcons";

import AgentToolbarButton from "./AgentToolbarButton";

const placeholder =
  "Demandez a l'agent d'analyser un compte, une ecriture ou une retenue a la source...";

export default function AgentPromptCard() {
  return (
    <div className="w-full max-w-[640px]">
      <div className="overflow-hidden rounded-[26px] border-[3px] border-[#1f252b] bg-white shadow-[0_22px_50px_rgba(15,23,42,0.10)]">
        <div className="min-h-[190px] px-5 pb-4 pt-5">
          <label className="block">
            <span className="sr-only">Prompt Harmonizer Agent</span>
            <textarea
              rows={4}
              placeholder={placeholder}
              className="block min-h-[96px] w-full resize-none bg-transparent text-[16px] leading-6 text-black outline-none placeholder:text-black/45"
            />
          </label>

          <div className="mt-3 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AgentToolbarButton label="Ajouter">
                <PlusIcon className="size-[18px]" />
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
              className="flex size-[46px] shrink-0 cursor-pointer items-center justify-center rounded-full bg-[#24272b] text-white shadow-[0_14px_28px_rgba(15,23,42,0.18)] transition hover:bg-black"
            >
              <ArrowUpIcon className="size-[20px]" />
            </button>
          </div>
        </div>

        <div className="flex min-h-[54px] items-center justify-between gap-4 bg-[#edf1f3] px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-[#dfe6ea] px-3 py-2 text-[12px] font-semibold text-[#28323a]">
              Harmonizer Agent
            </span>
            <span className="rounded-full bg-white/70 px-3 py-2 text-[12px] font-semibold text-[#50606b]">
              Analyse locale
            </span>
          </div>

          <div className="flex min-w-0 items-center gap-3">
            <p className="hidden truncate text-[12px] font-medium text-[#72808a] sm:block">
              Recherche dans les donnees connectees...
            </p>
            <button
              type="button"
              className="cursor-pointer rounded-full bg-[#d8e0e5] px-4 py-2 text-[12px] font-semibold text-[#53616b] transition hover:bg-[#cbd6dc]"
            >
              Stop
            </button>
          </div>
        </div>
      </div>

      <p className="mx-auto mt-4 max-w-[520px] text-center text-[13px] leading-5 text-black/42">
        Les reponses restent explicatives: les regles deterministes et la validation
        humaine gardent la decision fiscale.
      </p>
    </div>
  );
}
