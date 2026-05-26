import { useState, useEffect } from "react";

const VERDICT_COLORS = {
  PROCEED: "bg-green-900 text-green-400",
  REVIEW:  "bg-yellow-900 text-yellow-400",
  REJECT:  "bg-red-900 text-red-400",
};

export default function AuditTrail() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAudit = async () => {
    try {
      const res = await fetch("/api/audit");
      const data = await res.json();
      setEntries((data.entries || []).slice().reverse());
    } catch {}
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchAudit();
    const id = setInterval(fetchAudit, 5000);
    return () => clearInterval(id);
  }, []);

  if (loading) return <div className="text-center py-12 text-gray-500 text-sm">Loading audit log...</div>;
  if (!entries.length) return <div className="text-center py-12 text-gray-500 text-sm">No audit entries yet. Run a verification to start logging.</div>;

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-500">
        {entries.length} verification{entries.length !== 1 ? "s" : ""} logged &nbsp;·&nbsp; auto-refreshes every 5s
      </p>
      {entries.map((entry) => (
        <div key={entry.audit_id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-gray-400">{entry.audit_id}</span>
                <span className="text-xs text-gray-600">{new Date(entry.timestamp).toLocaleString()}</span>
              </div>
              <p className="text-sm font-semibold text-gray-100 mt-1">Applicant: {entry.applicant_id}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${VERDICT_COLORS[entry.final_verdict] || "bg-gray-800 text-gray-400"}`}>
              {entry.final_verdict || "N/A"}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-gray-800">
            <Stat label="Fraud Score" value={entry.fraud_score != null ? `${entry.fraud_score}/100` : "—"} />
            <Stat label="Confidence"  value={entry.confidence_score != null ? `${entry.confidence_score}%` : "—"} />
            <Stat label="Hard Fails"  value={entry.hard_fails ?? "—"} />
            <Stat label="Soft Fails"  value={entry.soft_fails ?? "—"} />
          </div>

          <div className="mt-2 flex flex-wrap gap-1">
            {(entry.agents_run || []).map((agent) => (
              <span key={agent} className="text-xs bg-gray-800 text-gray-400 border border-gray-700 px-2 py-0.5 rounded-full capitalize">
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
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-semibold text-gray-200">{value}</p>
    </div>
  );
}
