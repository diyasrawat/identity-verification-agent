import { useState, useEffect } from "react";

const CATEGORIES = ["name_test", "dob_test", "gender_test", "pan_test", "judge_demo", "manual"];

function StatCard({ label, value, sub, color = "indigo" }) {
  const colors = { indigo: "text-indigo-400", green: "text-green-400", yellow: "text-yellow-400", red: "text-red-400" };
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
      <p className={`text-2xl font-bold ${colors[color]}`}>{value}</p>
      <p className="text-xs font-semibold text-gray-400 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-gray-600 mt-1">{sub}</p>}
    </div>
  );
}

function Section({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800 text-sm font-semibold text-gray-300 hover:bg-gray-750 transition-colors"
      >
        {title}
        <span className="text-gray-500">{open ? "^" : "v"}</span>
      </button>
      {open && <div className="p-4 bg-gray-900">{children}</div>}
    </div>
  );
}

const VERDICT_COLOR = {
  "CLEAN":                      "bg-green-900 text-green-400",
  "SOFT ISSUES — HUMAN REVIEW": "bg-yellow-900 text-yellow-400",
  "HARD BLOCK":                 "bg-red-900 text-red-400",
};

export default function MemoryDashboard() {
  const [stats,         setStats]         = useState(null);
  const [verifications, setVerifications] = useState([]);
  const [testSessions,  setTestSessions]  = useState([]);
  const [patterns,      setPatterns]      = useState(null);
  const [loading,       setLoading]       = useState(true);
  const [resetting,     setResetting]     = useState(null);

  async function load() {
    setLoading(true);
    try {
      const [statsRes, verRes, sesRes, patRes] = await Promise.all([
        fetch("/api/memory/stats").then((r) => r.json()),
        fetch("/api/history/verifications?limit=20").then((r) => r.json()),
        fetch("/api/history/test-sessions?limit=50").then((r) => r.json()),
        fetch("/api/history/patterns").then((r) => r.json()),
      ]);
      setStats(statsRes);
      setVerifications(verRes.verifications ?? []);
      setTestSessions(sesRes.sessions ?? []);
      setPatterns(patRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleReset(key) {
    if (!window.confirm(`Reset "${key}"? This cannot be undone.`)) return;
    setResetting(key);
    await fetch("/api/memory/reset", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key }) });
    setResetting(null);
    load();
  }

  const sessionsByCategory = CATEGORIES.reduce((acc, cat) => {
    acc[cat] = testSessions.filter((s) => s.test_category === cat);
    return acc;
  }, {});

  if (loading) return <div className="text-sm text-indigo-400 font-medium animate-pulse py-8 text-center">Loading memory data...</div>;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-gray-100">Memory &amp; History</h2>
        <p className="text-xs text-gray-500 mt-0.5">Persistent JSON + SQLite — survives server restarts</p>
      </div>

      {/* Storage Summary */}
      <Section title="Storage Summary" defaultOpen={true}>
        {stats && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard label="Total Verifications" value={stats.summary?.total_verifications ?? 0} color="indigo" />
              <StatCard label="Test Sessions"        value={stats.summary?.total_test_sessions ?? 0}   color="green"  />
              <StatCard label="Healing Events"       value={stats.summary?.total_healing_events ?? 0}  color="yellow" />
              <StatCard label="Proposals"            value={stats.summary?.total_proposals ?? 0}       color="indigo" />
            </div>
            <div className="text-xs text-gray-500">
              SQLite DB: {Math.round((stats.sqlite?.db_size_bytes ?? 0) / 1024)} KB
              {Object.entries(stats.json_files ?? {}).map(([key, info]) => (
                <span key={key} className="ml-4">
                  {key}.json: {info.exists ? `${Math.round(info.size_bytes / 1024)} KB` : "not created yet"}
                </span>
              ))}
            </div>
          </div>
        )}
      </Section>

      {/* Verification History */}
      <Section title="Recent Verifications (Last 20)">
        {verifications.length === 0 ? (
          <p className="text-sm text-gray-500">No verifications stored yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-800">
            <table className="w-full text-xs text-left">
              <thead className="bg-gray-800 text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Applicant</th>
                  <th className="px-3 py-2">Verdict</th>
                  <th className="px-3 py-2">Confidence</th>
                  <th className="px-3 py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {verifications.map((v) => (
                  <tr key={v.id} className="bg-gray-900 hover:bg-gray-800">
                    <td className="px-3 py-2 text-gray-500">#{v.id}</td>
                    <td className="px-3 py-2 font-medium text-gray-200">{v.applicant_id}</td>
                    <td className="px-3 py-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${VERDICT_COLOR[v.verdict] ?? "bg-gray-800 text-gray-400"}`}>
                        {v.verdict}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={`font-bold ${v.confidence_score >= 85 ? "text-green-400" : v.confidence_score >= 55 ? "text-yellow-400" : "text-red-400"}`}>
                        {v.confidence_score}%
                      </span>
                      <span className="text-gray-500 ml-1">{v.confidence_label}</span>
                    </td>
                    <td className="px-3 py-2 text-gray-500">{v.timestamp?.slice(0, 19).replace("T", " ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* Test Sessions */}
      <Section title="Test Sessions by Category">
        {testSessions.length === 0 ? (
          <p className="text-sm text-gray-500">No test sessions yet. Use Live Tester with a test case name.</p>
        ) : (
          <div className="space-y-4">
            {CATEGORIES.map((cat) => {
              const sessions = sessionsByCategory[cat];
              if (sessions.length === 0) return null;
              const passCount = sessions.filter((s) => s.verdict === "CLEAN").length;
              return (
                <div key={cat}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold uppercase text-gray-400">{cat}</span>
                    <span className="text-xs text-gray-600">{sessions.length} sessions · {passCount} passed</span>
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-gray-800">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-gray-800 text-gray-500">
                        <tr>
                          <th className="px-3 py-1.5">Test Case</th>
                          <th className="px-3 py-1.5">Verdict</th>
                          <th className="px-3 py-1.5">Score</th>
                          <th className="px-3 py-1.5">Thresholds</th>
                          <th className="px-3 py-1.5">Time</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800">
                        {sessions.map((s) => (
                          <tr key={s.id} className="bg-gray-900">
                            <td className="px-3 py-1.5 font-medium text-gray-200">{s.test_case_name || "—"}</td>
                            <td className="px-3 py-1.5">
                              <span className={`rounded-full px-2 py-0.5 font-semibold ${VERDICT_COLOR[s.verdict] ?? "bg-gray-800 text-gray-400"}`}>
                                {s.verdict}
                              </span>
                            </td>
                            <td className="px-3 py-1.5 font-bold text-indigo-400">{s.confidence_score}%</td>
                            <td className="px-3 py-1.5 text-gray-500">P:{s.pass_threshold} S:{s.soft_threshold} L:{s.initial_leniency ? "on" : "off"}</td>
                            <td className="px-3 py-1.5 text-gray-500">{s.timestamp?.slice(11, 19)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Section>

      {/* Pattern Memory */}
      <Section title="Pattern Memory">
        {patterns ? (
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-xs font-bold text-gray-500 mb-2">Date Formats Seen</p>
              {Object.entries(patterns.date_formats ?? {}).length === 0 ? (
                <p className="text-xs text-gray-600">None yet</p>
              ) : (
                Object.entries(patterns.date_formats).sort(([, a], [, b]) => b - a).map(([fmt, count]) => (
                  <div key={fmt} className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs text-gray-300 w-40 truncate">{fmt}</span>
                    <div className="flex-1 bg-gray-800 rounded-full h-2">
                      <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${Math.min(100, count * 20)}%` }} />
                    </div>
                    <span className="text-xs text-gray-500">{count}x</span>
                  </div>
                ))
              )}
            </div>
            <div>
              <p className="text-xs font-bold text-gray-500 mb-2">Name Patterns Seen</p>
              {Object.entries(patterns.name_patterns ?? {}).length === 0 ? (
                <p className="text-xs text-gray-600">None yet</p>
              ) : (
                Object.entries(patterns.name_patterns).sort(([, a], [, b]) => b - a).map(([pat, count]) => (
                  <div key={pat} className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs text-gray-300 w-40 truncate">{pat}</span>
                    <div className="flex-1 bg-gray-800 rounded-full h-2">
                      <div className="bg-teal-500 h-2 rounded-full" style={{ width: `${Math.min(100, count * 20)}%` }} />
                    </div>
                    <span className="text-xs text-gray-500">{count}x</span>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : <p className="text-sm text-gray-500">No pattern data yet.</p>}
      </Section>

      {/* File Details */}
      <Section title="Persistent File Details">
        {stats && (
          <div className="space-y-2">
            {Object.entries(stats.json_files ?? {}).map(([key, info]) => (
              <div key={key} className="flex items-center justify-between text-xs border border-gray-800 rounded-lg px-3 py-2 bg-gray-900">
                <div>
                  <span className="font-medium text-gray-200">{key}.json</span>
                  <span className="text-gray-500 ml-3">
                    {info.exists ? `${info.size_bytes} bytes · last modified ${info.last_modified}` : "not created yet"}
                  </span>
                </div>
                {info.exists && (
                  <button
                    onClick={() => handleReset(key)}
                    disabled={resetting === key}
                    className="text-red-400 hover:text-red-300 text-xs underline disabled:opacity-50"
                  >
                    {resetting === key ? "Resetting..." : "Reset"}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>

      <div className="flex justify-end">
        <button onClick={load} className="text-xs font-medium text-indigo-400 hover:text-indigo-300 underline">
          Refresh All Data
        </button>
      </div>
    </div>
  );
}
