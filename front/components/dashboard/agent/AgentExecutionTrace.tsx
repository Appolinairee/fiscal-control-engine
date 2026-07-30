import type { AgentRunEvent } from "@/api/agent/types";
import {
  ChevronRightIcon,
  ClockIcon,
  TickCircleIcon,
} from "@/public/assets/icons/AgentInputIcons";

type AgentExecutionTraceProps = {
  events: AgentRunEvent[];
  hasFile: boolean;
  isLoading: boolean;
};

export default function AgentExecutionTrace({
  events,
  hasFile,
  isLoading,
}: AgentExecutionTraceProps) {
  const visibleEvents =
    events.length > 0 ? events : getFallbackThinkingEvents(hasFile);

  if (isLoading) {
    return <AgentExecutionEventList events={visibleEvents} isLoading />;
  }

  return (
    <details className="group w-fit text-[12px] font-medium leading-6 text-[#667781]">
      <summary className="flex cursor-pointer list-none items-center gap-2">
        <span>{getSummaryLabel(visibleEvents)}</span>
        <ChevronRightIcon className="size-3 text-[#9aa8b0] transition group-open:rotate-90" />
      </summary>
      <div className="mt-2">
        <AgentExecutionEventList events={visibleEvents} />
      </div>
    </details>
  );
}

function AgentExecutionEventList({
  events,
  isLoading = false,
}: {
  events: AgentRunEvent[];
  isLoading?: boolean;
}) {
  const currentEvent = getCurrentEvent(events);

  return (
    <ol className="relative ml-2 space-y-1.5 pl-7 before:absolute before:left-0 before:top-1 before:h-[calc(100%-8px)] before:w-px before:bg-[#d9e5eb]">
      {events.map((event, index) => {
        const isCurrent = isLoading && event === currentEvent;

        return (
          <li
            key={`${event.event_type}-${index}`}
            className="relative"
            title={event.message}
          >
            <span
              className={`absolute -left-[35px] top-1.5 flex size-4 items-center justify-center rounded-full bg-white ${getEventIconClassName(
                event.status,
                isCurrent,
                isLoading
              )}`}
            >
              <EventStatusIcon
                status={event.status}
                isCurrent={isCurrent}
                isLoading={isLoading}
              />
            </span>
            <span
              className={`block ${
                isCurrent ? "agent-thinking-light text-[#40515c]" : "text-[#8a98a2]"
              }`}
            >
              {event.message}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function EventStatusIcon({
  status,
  isCurrent,
  isLoading,
}: {
  status: string;
  isCurrent: boolean;
  isLoading: boolean;
}) {
  if (status === "error") {
    return <span className="text-[11px] leading-none">!</span>;
  }
  if (isLoading && isCurrent) {
    return <ClockIcon className="size-4" />;
  }
  return <TickCircleIcon className="size-4" />;
}

function getFallbackThinkingEvents(hasFile: boolean): AgentRunEvent[] {
  const messages = hasFile
    ? [
        "Demande prise en compte.",
        "Fichier prêt pour l'analyse.",
        "Préparation de la réponse.",
      ]
    : ["Demande prise en compte.", "Préparation de la réponse."];

  return messages.map((message, index) => ({
    event_type: `fallback_${index}`,
    title: message,
    message,
    status: index === messages.length - 1 ? "running" : "completed",
    tool_name: null,
    provider_name: null,
    model_name: null,
  }));
}

function getCurrentEvent(events: AgentRunEvent[]) {
  return events[events.length - 1];
}

function getSummaryLabel(events: AgentRunEvent[]) {
  const hasError = events.some((event) => event.status === "error");
  if (hasError) return "Analyse arrêtée.";
  return "Réponse prête.";
}

function getEventIconClassName(
  status: string,
  isCurrent: boolean,
  isLoading: boolean
) {
  if (status === "error") return "text-red-500";
  if (isLoading && isCurrent) return "text-[#40515c]";
  return "text-[#6f7f88]";
}
