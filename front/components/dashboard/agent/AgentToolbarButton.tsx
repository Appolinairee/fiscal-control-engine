import type { ReactNode } from "react";

type AgentToolbarButtonProps = {
  label: string;
  children: ReactNode;
};

export default function AgentToolbarButton({
  label,
  children,
}: AgentToolbarButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className="flex size-8 cursor-pointer items-center justify-center rounded-full text-black/54 transition hover:bg-black/[0.04] hover:text-black"
    >
      {children}
    </button>
  );
}
