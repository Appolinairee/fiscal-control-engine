import { MenuIcon } from "@/public/assets/icons/SideBarIcons";

import TopbarIconButton from "./TopbarIconButton";

export default function TopbarBrand() {
  return (
    <div className="flex min-w-0 items-center gap-5">
      <TopbarIconButton label="Ouvrir le menu">
        <MenuIcon className="size-[19px]" />
      </TopbarIconButton>

      <div className="flex min-w-0 items-center gap-4">
        <div className="flex size-[54px] shrink-0 items-center justify-center rounded-full bg-black text-[22px] font-bold leading-none text-white">
          <span className="-translate-y-px">N°</span>
        </div>

        <div className="flex h-[54px] min-w-0 flex-col justify-center">
          <p className="truncate text-[22px] font-bold leading-[1.02] text-black">
            Fiscal
          </p>
          <p className="truncate text-[21px] leading-[1.02] text-[#8f8f8f]">
            Dashboard
          </p>
        </div>
      </div>
    </div>
  );
}
