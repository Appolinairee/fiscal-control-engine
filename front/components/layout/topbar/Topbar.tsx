import { PlusIcon } from "@/public/assets/icons/icons";

import TopbarBrand from "./TopbarBrand";
import TopbarIconButton from "./TopbarIconButton";
import TopbarProfile from "./TopbarProfile";
import TopbarSearch from "./TopbarSearch";

export default function Topbar() {
  return (
    <header className="w-full bg-white px-8 py-9 sm:px-12 lg:px-[72px]">
      <div className="flex h-[58px] items-center justify-between gap-8">
        <TopbarBrand />

        <div className="flex shrink-0 items-center gap-8">
          <TopbarIconButton label="Ajouter">
            <PlusIcon className="size-[20px]" />
          </TopbarIconButton>
          <TopbarProfile />
          <TopbarSearch />
        </div>
      </div>
    </header>
  );
}
