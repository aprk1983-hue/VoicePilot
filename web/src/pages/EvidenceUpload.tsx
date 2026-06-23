import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { CaseSummaryCard } from "../components/CaseSummaryCard";
import { ErrorBanner } from "../components/ErrorBanner";

export function EvidenceUploadPage() {
  const { caseId = "" } = useParams();
  const [command, setCommand] = useState("show sip-ua status");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const result = await api.uploadEvidence(caseId, command, content);
      setSuccess(`Evidence ${result.evidence_id} accepted for command ${result.command}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Evidence Upload</h1>
      <ErrorBanner message={error} />
      {success && <div className="card badge-success">{success}</div>}
      <CaseSummaryCard caseId={caseId} />

      <form className="card" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="command">Command</label>
          <input
            id="command"
            value={command}
            onChange={(event) => setCommand(event.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="content">Evidence content</label>
          <textarea
            id="content"
            value={content}
            onChange={(event) => setContent(event.target.value)}
            placeholder="Paste CLI or export output here…"
            required
          />
        </div>
        <div className="actions">
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Uploading…" : "Upload Evidence"}
          </button>
          <Link className="btn btn-secondary" to={`/cases/${caseId}`}>
            Back to Case
          </Link>
        </div>
      </form>
    </div>
  );
}
