import { MenuIcon } from "@/public/assets/icons/SideBarIcons";

import TopbarIconButton from "./TopbarIconButton";

export default function TopbarBrand() {
  return (
    <div className="flex min-w-0 items-center gap-4">
      <TopbarIconButton label="Ouvrir le menu">
        <MenuIcon className="size-[19px]" />
      </TopbarIconButton>

      <div className="flex min-w-0 items-center gap-5">
        <div className="flex size-[64px] shrink-0 items-center justify-center rounded-full bg-black text-[27px] font-bold leading-none text-white">
          <span className="-translate-y-[1px]">N°</span>
        </div>

        <div className="flex h-[64px] min-w-0 flex-col justify-center">
          <p className="truncate text-[28px] font-bold leading-[1.02] text-black">
            Fiscal
          </p>
          <p className="truncate text-[27px] leading-[1.02] text-[#8f8f8f]">
            Dashboard
          </p>
        </div>
      </div>
    </div>
  );
}
