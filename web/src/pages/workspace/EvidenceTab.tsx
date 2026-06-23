import { FormEvent, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import { EvidenceDropzone } from "../../components/case/EvidenceDropzone";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";

export function EvidenceTab() {
  const { caseId = "" } = useParams();
  const [command, setCommand] = useState("organization-export");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function submit(contentValue: string, commandValue: string) {
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const result = await api.uploadEvidence(caseId, commandValue, contentValue);
      setSuccess(`Evidence ${result.evidence_id} accepted.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    await submit(content, command);
  }

  return (
    <div>
      <ErrorBanner message={error} />
      {success && <div className="card badge-success" style={{ marginBottom: "1rem" }}>{success}</div>}

      <Card title="Drag & Drop Evidence">
        <EvidenceDropzone
          disabled={loading}
          onFileContent={(filename, fileContent) => {
            setContent(fileContent);
            const inferred = filename.replace(/\.[^.]+$/, "").replace(/_/g, "-");
            setCommand(inferred);
          }}
        />
      </Card>

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="command">
            Command
          </label>
          <input
            id="command"
            className="form-input"
            value={command}
            onChange={(event) => setCommand(event.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="content">
            Evidence content
          </label>
          <textarea
            id="content"
            className="form-textarea"
            value={content}
            onChange={(event) => setContent(event.target.value)}
            placeholder="Paste or drop evidence output…"
            required
          />
        </div>
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Uploading…" : "Upload to API"}
        </button>
      </form>
    </div>
  );
}
