import AgentPromptCard from "@/components/dashboard/agent/AgentPromptCard";

export default function AgentColumn() {
  return (
    <section className="min-h-[560px] overflow-y-auto bg-white px-6 py-8 lg:min-h-0">
      <div className="flex min-h-full items-center justify-center">
        <AgentPromptCard />
      </div>
    </section>
  );
}
