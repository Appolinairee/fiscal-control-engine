import type {
  AgentConversationMessage,
  AgentRunEvent,
} from "@/api/agent/types";
import {
  ChevronRightIcon,
  ClockIcon,
  TickCircleIcon,
} from "@/public/assets/icons/AgentInputIcons";
import AgentFileCard from "./AgentFileCard";

export default function AgentConversation({
  messages,
}: {
  messages: AgentConversationMessage[];
}) {
  if (messages.length === 0) return null;

  return (
    <div className="space-y-5 pt-3">
      {messages.map((message) =>
        message.role === "user" ? (
          <UserMessage key={message.id} message={message} />
        ) : (
          <AssistantMessage key={message.id} message={message} />
        )
      )}
    </div>
  );
}

function UserMessage({
  message,
}: {
  message: Extract<AgentConversationMessage, { role: "user" }>;
}) {
  return (
    <div className="flex flex-col items-end gap-2">
      {message.attachedFile && <AgentFileCard attachedFile={message.attachedFile} />}
      <div className="max-w-[86%] rounded-2xl bg-[#edf4f7] px-4 py-3 text-[14px] font-medium leading-6 text-[#102734]">
        {message.content}
      </div>
    </div>
  );
}

function AssistantMessage({
  message,
}: {
  message: Extract<AgentConversationMessage, { role: "assistant" }>;
}) {
  const isLoading = message.status === "loading";

  return (
    <div className="space-y-3 px-1 text-[15px] leading-7 text-[#203743]">
      {isLoading && (
        <AgentExecutionThinking
          events={message.executionEvents}
          hasFile={message.hasFileContext}
        />
      )}

      {!isLoading && message.executionEvents.length > 0 && (
        <AgentExecutionSummary events={message.executionEvents} />
      )}

      {message.content && (
        <div className="group/answer">
          <AgentMarkdownAnswer
            content={message.content}
            isError={message.status === "error"}
          />
          {!isLoading && message.providerName && message.modelName && (
            <AgentModelMeta
              providerName={message.providerName}
              modelName={message.modelName}
            />
          )}
        </div>
      )}
    </div>
  );
}

function AgentExecutionThinking({
  events,
  hasFile,
}: {
  events: AgentRunEvent[];
  hasFile: boolean;
}) {
  const visibleEvents =
    events.length > 0 ? events : getFallbackThinkingEvents(hasFile);
  const currentEvent = getCurrentThinkingEvent(visibleEvents);

  return (
    <div className="space-y-2 text-[13px] font-medium leading-6 text-[#7f8d96]">
      <div className="inline-flex items-center gap-2 text-[#8a98a2]">
        <span className="size-3 rotate-45 rounded-[3px] border border-[#9fb3be] bg-[#f7fbfd] shadow-[0_0_18px_rgba(160,186,198,0.45)]" />
        <span className="agent-thinking-light">{currentEvent.message}</span>
      </div>
      <ol className="relative ml-2 space-y-2 pl-7 before:absolute before:left-0 before:top-1 before:h-[calc(100%-8px)] before:w-px before:bg-[#d9e5eb]">
        {visibleEvents.map((event, index) => {
          const isCurrent = event === currentEvent;

          return (
            <li
              key={`${event.event_type}-${index}`}
              className="relative"
              title={event.message}
            >
              <span
                className={`absolute -left-[35px] top-1.5 flex size-4 items-center justify-center rounded-full bg-white ${getEventIconClassName(
                  event.status,
                  isCurrent
                )}`}
              >
                <EventStatusIcon status={event.status} />
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
    </div>
  );
}

function AgentExecutionSummary({ events }: { events: AgentRunEvent[] }) {
  const lastMeaningfulEvent =
    [...events].reverse().find((event) => event.status !== "error") || events[0];

  return (
    <details className="group w-fit text-[12px] font-medium leading-6 text-[#667781]">
      <summary className="flex cursor-pointer list-none items-center gap-2">
        <span>{lastMeaningfulEvent?.message || "Analyse terminee"}</span>
        <ChevronRightIcon className="size-3 text-[#9aa8b0] transition group-open:rotate-90" />
      </summary>
      <ol className="relative ml-2 mt-2 space-y-2 pl-7 before:absolute before:left-0 before:top-1 before:h-[calc(100%-8px)] before:w-px before:bg-[#d9e5eb]">
        {events.map((event, index) => (
          <li key={`${event.event_type}-${index}`} className="relative">
            <span
              className={`absolute -left-[35px] top-1.5 flex size-4 items-center justify-center rounded-full bg-white ${getEventIconClassName(
                event.status,
                false
              )}`}
            >
              <EventStatusIcon status={event.status} />
            </span>
            <span
              className={event.status === "error" ? "text-red-700" : ""}
            >
              {event.message}
            </span>
          </li>
        ))}
      </ol>
    </details>
  );
}

function EventStatusIcon({ status }: { status: string }) {
  if (status === "completed") {
    return <TickCircleIcon className="size-4" />;
  }
  if (status === "error") {
    return <span className="text-[11px] leading-none">!</span>;
  }
  return <ClockIcon className="size-4" />;
}

function AgentModelMeta({
  providerName,
  modelName,
}: {
  providerName: string;
  modelName: string;
}) {
  return (
    <p className="pt-1 text-right text-[11px] font-medium text-[#9aa8b0] opacity-0 transition group-hover/answer:opacity-100">
      {providerName} · {modelName}
    </p>
  );
}

function AgentMarkdownAnswer({
  content,
  isError,
}: {
  content: string;
  isError: boolean;
}) {
  return (
    <div
      className={`space-y-3 ${
        isError ? "font-medium text-red-700" : "text-[#203743]"
      }`}
    >
      {parseMarkdownBlocks(content).map((block, index) => {
        if (block.type === "heading") {
          return <p key={`${block.type}-${index}`}>{block.content}</p>;
        }

        if (block.type === "list") {
          return (
            <ul
              key={`${block.type}-${index}`}
              className="list-disc space-y-1 pl-5"
            >
              {block.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          );
        }

        return <p key={`${block.type}-${index}`}>{block.content}</p>;
      })}
    </div>
  );
}

type MarkdownBlock =
  | {
      type: "heading" | "paragraph";
      content: string;
    }
  | {
      type: "list";
      items: string[];
    };

function parseMarkdownBlocks(content: string): MarkdownBlock[] {
  const blocks: MarkdownBlock[] = [];
  let paragraphLines: string[] = [];
  let listItems: string[] = [];
  const normalizedContent = normalizeInlineMarkdownLists(content);

  const flushParagraph = () => {
    if (paragraphLines.length === 0) return;
    blocks.push({
      type: "paragraph",
      content: paragraphLines.join(" "),
    });
    paragraphLines = [];
  };

  const flushList = () => {
    if (listItems.length === 0) return;
    blocks.push({
      type: "list",
      items: listItems,
    });
    listItems = [];
  };

  normalizedContent.split("\n").forEach((line) => {
    const trimmedLine = line.trim();
    if (!trimmedLine) {
      flushParagraph();
      flushList();
      return;
    }

    const headingMatch = trimmedLine.match(/^#{1,3}\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      flushList();
      if (isBoilerplateHeading(headingMatch[1])) {
        return;
      }
      blocks.push({
        type: "heading",
        content: cleanMarkdownText(headingMatch[1]),
      });
      return;
    }

    const listMatch = trimmedLine.match(/^[-*]\s+(.+)$/);
    if (listMatch) {
      flushParagraph();
      listItems.push(cleanMarkdownText(listMatch[1]));
      return;
    }

    flushList();
    paragraphLines.push(cleanMarkdownText(trimmedLine));
  });

  flushParagraph();
  flushList();

  return blocks;
}

function normalizeInlineMarkdownLists(content: string) {
  return content
    .trim()
    .replace(/\s+:\s+-\s+/g, ":\n- ")
    .replace(/\s+-\s+(?=[A-ZÀ-Ý0-9])/g, "\n- ");
}

function cleanMarkdownText(content: string) {
  return content.replace(/\*\*(.*?)\*\*/g, "$1").trim();
}

function isBoilerplateHeading(content: string) {
  return ["introduction"].includes(content.trim().toLowerCase());
}

function getFallbackThinkingEvents(hasFile: boolean): AgentRunEvent[] {
  const messages = hasFile
    ? [
        "Lecture du fichier transmis.",
        "Evaluation du contexte deterministe.",
        "Preparation de la reponse.",
      ]
    : ["Evaluation de la demande.", "Preparation de la reponse."];

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

function getCurrentThinkingEvent(events: AgentRunEvent[]) {
  return (
    [...events].reverse().find((event) => event.status === "running") ||
    events[events.length - 1]
  );
}

function getEventIconClassName(status: string, isCurrent: boolean) {
  if (status === "error") return "text-red-500";
  if (status === "completed") return "text-[#6f7f88]";
  if (isCurrent) return "text-[#40515c]";
  return "text-[#9aa8b0]";
}
