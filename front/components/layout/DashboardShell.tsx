import type { ReactNode } from "react";

import Topbar from "@/components/layout/topbar/Topbar";

export default function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-white text-gray-950">
      <Topbar />
      <section className="min-h-[calc(100vh-130px)] bg-white">{children}</section>
    </main>
  );
}
