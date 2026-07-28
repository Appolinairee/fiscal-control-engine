import type { ReactNode } from "react";

import { cn } from "@/utils/ui/styles";

type TopbarIconButtonProps = {
  label: string;
  children: ReactNode;
  className?: string;
};

export default function TopbarIconButton({
  label,
  children,
  className,
}: TopbarIconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      className={cn(
        "flex size-[54px] shrink-0 cursor-pointer items-center justify-center rounded-full bg-white text-black shadow-[0_14px_30px_rgba(15,23,42,0.055)] ring-1 ring-black/[0.055] transition hover:bg-gray-50",
        className
      )}
    >
      {children}
    </button>
  );
}
