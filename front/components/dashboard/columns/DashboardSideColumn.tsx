type DashboardSideColumnProps = {
  title: string;
  side: "left" | "right";
};

export default function DashboardSideColumn({
  title,
  side,
}: DashboardSideColumnProps) {
  return (
    <aside
      className={[
        "min-h-0 overflow-y-auto bg-white px-6 py-6",
        side === "left"
          ? "border-b border-black/[0.06] lg:border-b-0 lg:border-r"
          : "border-t border-black/[0.06] lg:border-l lg:border-t-0",
      ].join(" ")}
    >
      <div className="h-full rounded-[8px] border border-dashed border-black/[0.08] bg-[#fbfbfb] px-4 py-4">
        <p className="text-[13px] font-semibold uppercase tracking-[0.12em] text-black/35">
          {title}
        </p>
      </div>
    </aside>
  );
}
