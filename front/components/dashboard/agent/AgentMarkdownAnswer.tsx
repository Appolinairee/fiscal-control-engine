type AgentMarkdownAnswerProps = {
  content: string;
  isError: boolean;
};

type MarkdownBlock =
  | {
      type: "heading" | "paragraph";
      content: string;
    }
  | {
      type: "list";
      items: string[];
    };

export default function AgentMarkdownAnswer({
  content,
  isError,
}: AgentMarkdownAnswerProps) {
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
