interface MarkdownViewerProps {
  content: string;
}

export function MarkdownViewer({ content }: MarkdownViewerProps) {
  return <pre className="markdown-viewer">{content}</pre>;
}
