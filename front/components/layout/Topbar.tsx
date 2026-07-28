import { SearchZoomIcon, PlusIcon } from "@/public/assets/icons/icons";
import { MenuIcon } from "@/public/assets/icons/SideBarIcons";

const iconButtonClass =
  "flex size-10 shrink-0 items-center justify-center rounded-full bg-white text-gray-950 shadow-[0_10px_22px_rgba(15,23,42,0.05)] ring-1 ring-gray-100 transition hover:bg-gray-50";

export default function Topbar() {
  return (
    <header className="w-full rounded-t-[28px] bg-[#fbfbfb] px-6 py-6 shadow-[0_1px_0_rgba(15,23,42,0.03)] sm:px-9">
      <div className="flex h-12 items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-4">
          <button type="button" className={iconButtonClass} aria-label="Ouvrir le menu">
            <MenuIcon className="size-[18px]" />
          </button>

          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-black text-[17px] font-bold text-white">
              Nº
            </div>
            <div className="min-w-0 leading-none">
              <p className="truncate text-[14px] font-bold leading-4 text-gray-950">
                Financial
              </p>
              <p className="truncate text-[14px] leading-4 text-gray-400">
                Dashboard
              </p>
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-4">
          <button type="button" className={iconButtonClass} aria-label="Ajouter">
            <PlusIcon className="size-[17px]" />
          </button>

          <div className="hidden items-center gap-3 sm:flex">
            <div className="size-10 rounded-full bg-[radial-gradient(circle_at_52%_26%,#f8ddd2_0_17%,transparent_18%),radial-gradient(circle_at_50%_43%,#b86a56_0_24%,transparent_25%),linear-gradient(135deg,#f6d3c7,#9e2f2e_54%,#702827)] ring-2 ring-white" />
            <div className="w-[128px] leading-none">
              <p className="truncate text-[13px] font-bold leading-4 text-gray-950">
                Dwayne Tatum
              </p>
              <p className="truncate text-[11px] font-semibold leading-4 text-gray-700">
                CEO Assistant
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-4 md:flex">
            <button type="button" className={iconButtonClass} aria-label="Rechercher">
              <SearchZoomIcon className="size-[18px]" />
            </button>
            <div className="w-[170px] text-[12px] text-gray-300">
              Start searching here ...
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
