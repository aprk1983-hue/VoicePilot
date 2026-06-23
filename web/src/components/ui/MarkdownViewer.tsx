export function MarkdownViewer({ content }: { content: string }) {
  return <pre className="markdown-viewer">{content}</pre>;
}
