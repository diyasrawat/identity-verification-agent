import { useState, useEffect } from "react";

const VERDICT_COLORS = {
  PROCEED: "bg-green-100 text-green-700",
  REVIEW: "bg-yellow-100 text-yellow-700",
  REJECT: "bg-red-100 text-red-700",
};

export default function AuditTrail() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAudit = async () => {
    try {
      const res = await fetch("/api/audit");
      const data = await res.json();
      setEntries((data.entries || []).slice().reverse());
    } catch {
      /* swallow network errors */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudit();
    const id = setInterval(fetchAudit, 5000);
    return () => clearInterval(id);
  }, []);

  if (loading) {
    return (
      <div className="text-center py-12 text-gray-400 text-sm">
        Loading audit log…
      </div>
    );
  }

  if (!entries.length) {
    return (
      <div className="text-center py-12 text-gray-400 text-sm">
        No audit entries yet. Run a verification to start logging.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500">
          {entries.length} verification{entries.length !== 1 ? "s" : ""} logged
          &nbsp;·&nbsp; auto-refreshes every 5s
        </p>
      </div>
      {entries.map((entry) => (
        <div
          key={entry.audit_id}
          className="bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-300 transition-colors"
        >
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-gray-700">
                  {entry.audit_id}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(entry.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="text-sm font-semibold text-gray-800 mt-1">
                Applicant: {entry.applicant_id}
              </p>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold ${
                VERDICT_COLORS[entry.final_verdict] || "bg-gray-100 text-gray-600"
              }`}
            >
              {entry.final_verdict || "N/A"}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-gray-100">
            <Stat label="Fraud Score" value={entry.fraud_score != null ? `${entry.fraud_score}/100` : "—"} />
            <Stat label="Confidence" value={entry.confidence_score != null ? `${entry.confidence_score}%` : "—"} />
            <Stat label="Hard Fails" value={entry.hard_fails ?? "—"} />
            <Stat label="Soft Fails" value={entry.soft_fails ?? "—"} />
          </div>

          <div className="mt-2 flex flex-wrap gap-1">
            {(entry.agents_run || []).map((agent) => (
              <span
                key={agent}
                className="text-xs bg-blue-50 text-blue-600 border border-blue-100 px-2 py-0.5 rounded-full capitalize"
              >
                {agent}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-sm font-semibold text-gray-700">{value}</p>
    </div>
  );
}
