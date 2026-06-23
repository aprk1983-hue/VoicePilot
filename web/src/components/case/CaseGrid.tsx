import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { CaseData } from "../../api/types";
import { Badge } from "../ui/Badge";

type SortKey = keyof Pick<
  CaseData,
  "case_id" | "playbook_id" | "state" | "finding_count" | "hypothesis_count"
>;

interface CaseGridProps {
  cases: CaseData[];
  onDelete?: (caseId: string) => void;
}

export function CaseGrid({ cases, onDelete }: CaseGridProps) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("case_id");
  const [sortAsc, setSortAsc] = useState(true);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    let rows = cases;
    if (normalized) {
      rows = rows.filter(
        (item) =>
          item.case_id.toLowerCase().includes(normalized) ||
          item.playbook_id.toLowerCase().includes(normalized) ||
          item.state.toLowerCase().includes(normalized),
      );
    }
    return [...rows].sort((a, b) => {
      const left = a[sortKey];
      const right = b[sortKey];
      if (typeof left === "number" && typeof right === "number") {
        return sortAsc ? left - right : right - left;
      }
      return sortAsc
        ? String(left).localeCompare(String(right))
        : String(right).localeCompare(String(left));
    });
  }, [cases, query, sortKey, sortAsc]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((value) => !value);
      return;
    }
    setSortKey(key);
    setSortAsc(true);
  }

  return (
    <div>
      <div className="data-grid-toolbar">
        <input
          className="form-input data-grid-search"
          placeholder="Search cases…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="Search cases"
        />
        <span className="metric-hint">{filtered.length} case(s)</span>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">No cases match your search.</div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => toggleSort("case_id")}>Case ID</th>
                <th onClick={() => toggleSort("playbook_id")}>Playbook</th>
                <th onClick={() => toggleSort("state")}>State</th>
                <th onClick={() => toggleSort("finding_count")}>Findings</th>
                <th onClick={() => toggleSort("hypothesis_count")}>Hypotheses</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.case_id}>
                  <td>
                    <Link to={`/cases/${item.case_id}`}>{item.case_id}</Link>
                  </td>
                  <td>{item.playbook_id}</td>
                  <td>
                    <Badge variant="accent">{item.state}</Badge>
                  </td>
                  <td>{item.finding_count}</td>
                  <td>{item.hypothesis_count}</td>
                  <td>
                    <div className="actions" style={{ marginTop: 0 }}>
                      <Link className="btn btn-secondary btn-sm" to={`/cases/${item.case_id}`}>
                        Open
                      </Link>
                      {onDelete && (
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => onDelete(item.case_id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
