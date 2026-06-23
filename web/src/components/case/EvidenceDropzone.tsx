import { useCallback, useState } from "react";

interface EvidenceDropzoneProps {
  onFileContent: (filename: string, content: string) => void;
  disabled?: boolean;
}

const ACCEPTED = ".txt,.csv,.json,.yaml,.yml,.log,.md";

export function EvidenceDropzone({ onFileContent, disabled }: EvidenceDropzoneProps) {
  const [dragging, setDragging] = useState(false);
  const [lastFile, setLastFile] = useState<string | null>(null);

  const readFile = useCallback(
    async (file: File) => {
      const content = await file.text();
      setLastFile(file.name);
      onFileContent(file.name, content);
    },
    [onFileContent],
  );

  const onDrop = useCallback(
    async (event: React.DragEvent) => {
      event.preventDefault();
      setDragging(false);
      if (disabled) return;
      const file = event.dataTransfer.files[0];
      if (file) await readFile(file);
    },
    [disabled, readFile],
  );

  return (
    <div
      className={`dropzone${dragging ? " dragging" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <div className="dropzone-title">Drag & drop evidence files</div>
      <div className="dropzone-hint">
        Supports {ACCEPTED.replace(/\./g, "").split(",").join(", ")} — read-only upload to API
      </div>
      <div className="actions" style={{ justifyContent: "center", marginTop: "1rem" }}>
        <label className="btn btn-secondary btn-sm">
          Browse files
          <input
            type="file"
            accept={ACCEPTED}
            hidden
            disabled={disabled}
            onChange={async (event) => {
              const file = event.target.files?.[0];
              if (file) await readFile(file);
            }}
          />
        </label>
      </div>
      {lastFile && <div className="metric-hint" style={{ marginTop: "0.75rem" }}>Loaded: {lastFile}</div>}
    </div>
  );
}
