import { MenuIcon } from "@/public/assets/icons/SideBarIcons";

import TopbarIconButton from "./TopbarIconButton";

export default function TopbarBrand() {
  return (
    <div className="flex min-w-0 items-center gap-5">
      <TopbarIconButton label="Ouvrir le menu">
        <MenuIcon className="size-[20px]" />
      </TopbarIconButton>

      <div className="flex min-w-0 items-center gap-4">
        <div className="flex size-[58px] shrink-0 items-center justify-center rounded-full bg-black text-[24px] font-bold leading-none text-white">
          Nº
        </div>

        <div className="min-w-0">
          <p className="truncate text-[21px] font-bold leading-[1.05] text-black">
            Financial
          </p>
          <p className="truncate text-[20px] leading-[1.05] text-[#8f8f8f]">
            Dashboard
          </p>
        </div>
      </div>
    </div>
  );
}
