import AgentPromptCard from "@/components/dashboard/agent/AgentPromptCard";

export default function AgentColumn() {
  return (
    <section className="custom-scrollbar min-h-[560px] overflow-y-auto bg-white px-6 py-6 lg:min-h-0">
      <div className="mx-auto flex min-h-full w-full justify-center">
        <AgentPromptCard />
      </div>
    </section>
  );
}
