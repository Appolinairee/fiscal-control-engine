import type { ReactNode } from "react";

import Topbar from "@/components/layout/Topbar";

export default function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-[#dedede] p-2 text-gray-950">
      <div className="mx-auto min-h-[calc(100vh-16px)] max-w-[1440px] overflow-hidden rounded-t-[30px] bg-[#f3f3f3]">
        <Topbar />
        <section className="min-h-[calc(100vh-112px)]">{children}</section>
      </div>
    </main>
  );
}
