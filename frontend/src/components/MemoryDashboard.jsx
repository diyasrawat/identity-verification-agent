import { useState, useEffect } from "react";

const CATEGORIES = ["name_test", "dob_test", "gender_test", "pan_test", "judge_demo", "manual"];

function StatCard({ label, value, sub, color = "indigo" }) {
  const colors = {
    indigo: "text-indigo-600",
    green: "text-green-600",
    yellow: "text-yellow-600",
    red: "text-red-600",
  };
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
      <p className={`text-2xl font-bold ${colors[color]}`}>{value}</p>
      <p className="text-xs font-semibold text-gray-700 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function Section({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 text-sm font-semibold text-gray-700 hover:bg-gray-100 transition-colors"
      >
        {title}
        <span>{open ? "▲" : "▼"}</span>
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
}

export default function MemoryDashboard() {
  const [stats, setStats] = useState(null);
  const [verifications, setVerifications] = useState([]);
  const [testSessions, setTestSessions] = useState([]);
  const [patterns, setPatterns] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(null);

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
    await fetch("/api/memory/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key }),
    });
    setResetting(null);
    load();
  }

  const VERDICT_COLOR = {
    "CLEAN": "bg-green-100 text-green-800",
    "SOFT ISSUES — HUMAN REVIEW": "bg-yellow-100 text-yellow-800",
    "HARD BLOCK": "bg-red-100 text-red-800",
  };

  const sessionsByCategory = CATEGORIES.reduce((acc, cat) => {
    acc[cat] = testSessions.filter((s) => s.test_category === cat);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="text-sm text-indigo-500 font-medium animate-pulse py-8 text-center">
        Loading memory data…
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-gray-800">💾 Memory & History</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Persistent JSON + SQLite storage — survives server restarts
        </p>
      </div>

      {/* ── Section 1: Summary stats ── */}
      <Section title="📊 Storage Summary" defaultOpen={true}>
        {stats && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard label="Total Verifications" value={stats.summary?.total_verifications ?? 0} color="indigo" />
              <StatCard label="Test Sessions" value={stats.summary?.total_test_sessions ?? 0} color="green" />
              <StatCard label="Healing Events" value={stats.summary?.total_healing_events ?? 0} color="yellow" />
              <StatCard label="Proposals" value={stats.summary?.total_proposals ?? 0} color="indigo" />
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

      {/* ── Section 2: Verification history ── */}
      <Section title="🔍 Recent Verifications (Last 20)">
        {verifications.length === 0 ? (
          <p className="text-sm text-gray-400">No verifications stored yet. Run an orchestration to see history.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-xs text-left">
              <thead className="bg-gray-50 text-gray-600 uppercase tracking-wide">
                <tr>
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Applicant</th>
                  <th className="px-3 py-2">Verdict</th>
                  <th className="px-3 py-2">Confidence</th>
                  <th className="px-3 py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {verifications.map((v) => (
                  <tr key={v.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-400">#{v.id}</td>
                    <td className="px-3 py-2 font-medium text-gray-800">{v.applicant_id}</td>
                    <td className="px-3 py-2">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${VERDICT_COLOR[v.verdict] ?? "bg-gray-100 text-gray-700"}`}>
                        {v.verdict}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={`font-bold ${v.confidence_score >= 85 ? "text-green-600" : v.confidence_score >= 55 ? "text-yellow-600" : "text-red-600"}`}>
                        {v.confidence_score}%
                      </span>
                      <span className="text-gray-400 ml-1">{v.confidence_label}</span>
                    </td>
                    <td className="px-3 py-2 text-gray-400">{v.timestamp?.slice(0, 19).replace("T", " ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* ── Section 3: Test sessions by category ── */}
      <Section title="🧪 Test Sessions by Category">
        {testSessions.length === 0 ? (
          <p className="text-sm text-gray-400">No test sessions yet. Use Live Tester with a test case name to log sessions.</p>
        ) : (
          <div className="space-y-4">
            {CATEGORIES.map((cat) => {
              const sessions = sessionsByCategory[cat];
              if (sessions.length === 0) return null;
              const passCount = sessions.filter((s) => s.verdict === "CLEAN").length;
              return (
                <div key={cat}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold uppercase text-gray-600">{cat}</span>
                    <span className="text-xs text-gray-400">{sessions.length} sessions · {passCount} passed</span>
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-gray-100">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-gray-50 text-gray-500">
                        <tr>
                          <th className="px-3 py-1.5">Test Case</th>
                          <th className="px-3 py-1.5">Verdict</th>
                          <th className="px-3 py-1.5">Score</th>
                          <th className="px-3 py-1.5">Thresholds</th>
                          <th className="px-3 py-1.5">Time</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {sessions.map((s) => (
                          <tr key={s.id}>
                            <td className="px-3 py-1.5 font-medium text-gray-800">{s.test_case_name || "—"}</td>
                            <td className="px-3 py-1.5">
                              <span className={`rounded-full px-2 py-0.5 font-semibold ${VERDICT_COLOR[s.verdict] ?? "bg-gray-100 text-gray-700"}`}>
                                {s.verdict}
                              </span>
                            </td>
                            <td className="px-3 py-1.5 font-bold text-indigo-600">{s.confidence_score}%</td>
                            <td className="px-3 py-1.5 text-gray-400">P:{s.pass_threshold} S:{s.soft_threshold} L:{s.initial_leniency ? "on" : "off"}</td>
                            <td className="px-3 py-1.5 text-gray-400">{s.timestamp?.slice(11, 19)}</td>
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

      {/* ── Section 4: Pattern memory ── */}
      <Section title="🧠 Pattern Memory">
        {patterns ? (
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-xs font-bold text-gray-600 mb-2">Date Formats Seen</p>
              {Object.entries(patterns.date_formats ?? {}).length === 0 ? (
                <p className="text-xs text-gray-400">None yet</p>
              ) : (
                Object.entries(patterns.date_formats)
                  .sort(([, a], [, b]) => b - a)
                  .map(([fmt, count]) => (
                    <div key={fmt} className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs text-gray-700 w-40 truncate">{fmt}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-indigo-400 h-2 rounded-full"
                          style={{ width: `${Math.min(100, count * 20)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{count}×</span>
                    </div>
                  ))
              )}
            </div>
            <div>
              <p className="text-xs font-bold text-gray-600 mb-2">Name Patterns Seen</p>
              {Object.entries(patterns.name_patterns ?? {}).length === 0 ? (
                <p className="text-xs text-gray-400">None yet</p>
              ) : (
                Object.entries(patterns.name_patterns)
                  .sort(([, a], [, b]) => b - a)
                  .map(([pat, count]) => (
                    <div key={pat} className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs text-gray-700 w-40 truncate">{pat}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-teal-400 h-2 rounded-full"
                          style={{ width: `${Math.min(100, count * 20)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{count}×</span>
                    </div>
                  ))
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400">No pattern data yet.</p>
        )}
      </Section>

      {/* ── Section 5: File details ── */}
      <Section title="📁 Persistent File Details">
        {stats && (
          <div className="space-y-2">
            {Object.entries(stats.json_files ?? {}).map(([key, info]) => (
              <div key={key} className="flex items-center justify-between text-xs border border-gray-100 rounded-lg px-3 py-2">
                <div>
                  <span className="font-medium text-gray-800">{key}.json</span>
                  <span className="text-gray-400 ml-3">
                    {info.exists
                      ? `${info.size_bytes} bytes · last modified ${info.last_modified}`
                      : "not created yet"}
                  </span>
                </div>
                {info.exists && (
                  <button
                    onClick={() => handleReset(key)}
                    disabled={resetting === key}
                    className="text-red-500 hover:text-red-700 text-xs underline disabled:opacity-50"
                  >
                    {resetting === key ? "Resetting…" : "Reset"}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* ── Section 6: Refresh ── */}
      <div className="flex justify-end">
        <button
          onClick={load}
          className="text-xs font-medium text-indigo-600 hover:text-indigo-800 underline"
        >
          Refresh All Data
        </button>
      </div>
    </div>
  );
}
