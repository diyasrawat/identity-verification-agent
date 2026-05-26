import { useState, useEffect, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "";

const TYPE_STYLES = {
  DATE_FORMAT_HANDLER:      "bg-blue-900 text-blue-300",
  NAME_THRESHOLD_ADJUSTMENT:"bg-violet-900 text-violet-300",
  TYPO_CORRECTION_RULE:     "bg-orange-900 text-orange-300",
  SYSTEMATIC_HARD_FAIL:     "bg-red-900 text-red-300",
};

const PRIORITY_STYLES = {
  HIGH:   "bg-red-900 text-red-300",
  MEDIUM: "bg-yellow-900 text-yellow-300",
};

const TRAINING_CARDS = [
  {
    id: 1, title: "Date Typo Test", desc: "Tests typo detection in month names",
    payload: { applicant_id: "TRAIN-001", pan: { number: "ABCDE1234F", name: "Test User", dob: "2004 arpil 6th", gender: "M", father_name: "Father Name" }, aadhaar: { last4: "1234", name: "Test User", dob: "2004-04-06", gender: "M", father_name: "Father Name" }, bureau: { name: "Test User", dob: "2004-04-06", pan_linked: "ABCDE1234F", aadhaar_last4: "1234" } },
  },
  {
    id: 2, title: "Initial Name Test", desc: "Tests initial vs full name pattern",
    payload: { applicant_id: "TRAIN-002", pan: { number: "ABCDE1234F", name: "P. Kumar", dob: "1990-04-12", gender: "M", father_name: "Ram Kumar" }, aadhaar: { last4: "5678", name: "Prashant Kumar", dob: "1990-04-12", gender: "M", father_name: "Ram Kumar" }, bureau: { name: "Prashant Kumar", dob: "1990-04-12", pan_linked: "ABCDE1234F", aadhaar_last4: "5678" } },
  },
  {
    id: 3, title: "Multi-Format DOB Test", desc: "Tests multiple date format normalization",
    payload: { applicant_id: "TRAIN-003", pan: { number: "PQRST5678G", name: "Anita Sharma", dob: "12/04/1990", gender: "F", father_name: "Suresh Sharma" }, aadhaar: { last4: "9012", name: "Anita Sharma", dob: "April 12, 1990", gender: "F", father_name: "Suresh Sharma" }, bureau: { name: "Anita Sharma", dob: "1990-04-12", pan_linked: "PQRST5678G", aadhaar_last4: "9012" } },
  },
  {
    id: 4, title: "Ordinal Suffix Test", desc: "Tests ordinal suffix handling",
    payload: { applicant_id: "TRAIN-004", pan: { number: "LMNOP9012H", name: "Raj Patel", dob: "6th April 2004", gender: "M", father_name: "Kiran Patel" }, aadhaar: { last4: "3456", name: "Raj Patel", dob: "2004-04-06", gender: "M", father_name: "Kiran Patel" }, bureau: { name: "Raj Patel", dob: "2004-04-06", pan_linked: "LMNOP9012H", aadhaar_last4: "3456" } },
  },
  {
    id: 5, title: "Short Year Test", desc: "Tests 2-digit year expansion",
    payload: { applicant_id: "TRAIN-005", pan: { number: "UVWXY3456I", name: "Meena Joshi", dob: "12-04-90", gender: "F", father_name: "Ramesh Joshi" }, aadhaar: { last4: "7890", name: "Meena Joshi", dob: "1990-04-12", gender: "F", father_name: "Ramesh Joshi" }, bureau: { name: "Meena Joshi", dob: "1990-04-12", pan_linked: "UVWXY3456I", aadhaar_last4: "7890" } },
  },
  {
    id: 6, title: "Multiple Initials Test", desc: "Tests multiple initial detection",
    payload: { applicant_id: "TRAIN-006", pan: { number: "FGHIJ7890J", name: "P. K. Sharma", dob: "1985-07-20", gender: "M", father_name: "K. Sharma" }, aadhaar: { last4: "2345", name: "Prashant Kumar Sharma", dob: "1985-07-20", gender: "M", father_name: "Kamal Sharma" }, bureau: { name: "Prashant Kumar Sharma", dob: "1985-07-20", pan_linked: "FGHIJ7890J", aadhaar_last4: "2345" } },
  },
];

function MiniBar({ label, value, max }) {
  const pct = max > 0 ? Math.max(4, Math.round((value / max) * 100)) : 4;
  return (
    <div className="flex items-center gap-3 py-1">
      <span className="text-xs text-gray-400 w-44 font-mono truncate" title={label}>{label}</span>
      <div className="flex-1 bg-gray-800 rounded h-2.5">
        <div className="bg-indigo-500 h-2.5 rounded" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-gray-300 w-6 text-right">{value}</span>
    </div>
  );
}

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
      <p className="text-2xl font-bold text-indigo-400">{value}</p>
      <p className="text-xs font-semibold text-gray-300 mt-1">{label}</p>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function SelfImprovingAgent() {
  const [stats,        setStats]        = useState(null);
  const [proposals,    setProposals]    = useState({ pending: [], approved: [], rejected: [] });
  const [historyTab,   setHistoryTab]   = useState("approved");
  const [trainResults, setTrainResults] = useState({});
  const [trainLoading, setTrainLoading] = useState({});
  const [approving,    setApproving]    = useState({});

  const fetchStats     = useCallback(async () => { try { const r = await fetch(`${API_BASE}/api/self-improve/stats`);     setStats(await r.json());    } catch {} }, []);
  const fetchProposals = useCallback(async () => { try { const r = await fetch(`${API_BASE}/api/self-improve/proposals`); setProposals(await r.json()); } catch {} }, []);

  useEffect(() => {
    fetchStats(); fetchProposals();
    const i1 = setInterval(fetchStats, 5000);
    const i2 = setInterval(fetchProposals, 5000);
    return () => { clearInterval(i1); clearInterval(i2); };
  }, [fetchStats, fetchProposals]);

  async function runTrainingCard(card) {
    setTrainLoading((p) => ({ ...p, [card.id]: true }));
    try {
      const res = await fetch(`${API_BASE}/api/orchestrate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(card.payload) });
      const data = await res.json();
      const checks = data.checks || [];
      const hf = checks.filter((c) => c.result === "hard_fail").length;
      const sf = checks.filter((c) => c.result === "soft_fail").length;
      const verdict = hf > 0 ? "HARD FAIL" : sf > 0 ? "SOFT FAIL" : "PASS";
      setTrainResults((p) => ({ ...p, [card.id]: { verdict, proposals: data.new_proposals_generated || 0 } }));
      await fetchStats(); await fetchProposals();
    } catch {
      setTrainResults((p) => ({ ...p, [card.id]: { verdict: "ERROR" } }));
    } finally {
      setTrainLoading((p) => ({ ...p, [card.id]: false }));
    }
  }

  async function handleApprove(proposalId) {
    setApproving((p) => ({ ...p, [proposalId]: true }));
    try {
      const res = await fetch(`${API_BASE}/api/self-improve/proposals/${proposalId}/approve`, { method: "POST" });
      const updated = await res.json();
      await fetchProposals();
      if (updated.generated_code) {
        setProposals((prev) => ({ ...prev, approved: prev.approved.map((p) => p.id === proposalId ? { ...p, generated_code: updated.generated_code } : p) }));
      }
    } finally {
      setApproving((p) => ({ ...p, [proposalId]: false }));
    }
  }

  async function handleReject(proposalId) {
    await fetch(`${API_BASE}/api/self-improve/proposals/${proposalId}/reject`, { method: "POST" });
    await fetchProposals();
  }

  const topDateFormats = stats?.top_date_formats || [];
  const topNamePatterns = stats?.top_name_patterns || [];
  const maxDateCount = topDateFormats.reduce((m, [, v]) => Math.max(m, v), 1);
  const maxNameCount = topNamePatterns.reduce((m, [, v]) => Math.max(m, v), 1);

  return (
    <div className="space-y-8">
      {/* Pattern Memory */}
      <div>
        <div className="mb-4">
          <h2 className="text-base font-bold text-gray-100">Pattern Memory</h2>
          <p className="text-xs text-gray-500 mt-0.5">What the agent has learned from every verification run</p>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          <StatCard label="Total Runs Observed" value={stats?.total_runs ?? 0} />
          <StatCard label="Patterns Discovered"  value={stats?.patterns_discovered ?? 0} />
          <StatCard label="Typos Caught"          value={stats?.typos_caught ?? 0} />
          <StatCard label="Proposals Generated"   value={(proposals.pending?.length || 0) + (proposals.approved?.length || 0) + (proposals.rejected?.length || 0)} sub={`${proposals.pending?.length || 0} pending`} />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Top Date Formats Seen</p>
            {topDateFormats.length === 0 ? <p className="text-xs text-gray-500 italic">No data yet</p> : topDateFormats.map(([fmt, cnt]) => <MiniBar key={fmt} label={fmt} value={cnt} max={maxDateCount} />)}
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Top Name Patterns Seen</p>
            {topNamePatterns.length === 0 ? <p className="text-xs text-gray-500 italic">No data yet</p> : topNamePatterns.map(([pat, cnt]) => <MiniBar key={pat} label={pat} value={cnt} max={maxNameCount} />)}
          </div>
        </div>
      </div>

      {/* Proposed Rule Updates */}
      <div>
        <div className="mb-4">
          <h2 className="text-base font-bold text-gray-100">
            Proposed Rule Updates
            <span className="ml-2 text-sm font-normal text-gray-500">({proposals.pending?.length || 0} pending)</span>
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">The agent identified these patterns and proposes updating its own rules.</p>
        </div>
        {(!proposals.pending || proposals.pending.length === 0) ? (
          <div className="rounded-xl border-2 border-dashed border-gray-800 py-10 text-center text-gray-500 text-sm">
            No proposals yet. Run verifications to train the agent.
          </div>
        ) : (
          <div className="space-y-3">
            {proposals.pending.map((p) => (
              <ProposalCard key={p.id} proposal={p} onApprove={() => handleApprove(p.id)} onReject={() => handleReject(p.id)} approving={approving[p.id]} />
            ))}
          </div>
        )}
      </div>

      {/* Learning History */}
      <div>
        <h2 className="text-base font-bold text-gray-100 mb-3">Learning History</h2>
        <div className="flex gap-0 border-b border-gray-800 mb-4">
          {["approved", "rejected"].map((t) => (
            <button key={t} onClick={() => setHistoryTab(t)} className={`px-4 py-2 text-sm font-medium border-b-2 capitalize transition-colors ${historyTab === t ? "border-indigo-400 text-indigo-400" : "border-transparent text-gray-500 hover:text-gray-300"}`}>
              {t} ({proposals[t]?.length || 0})
            </button>
          ))}
        </div>
        {(proposals[historyTab] || []).length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">No {historyTab} proposals yet.</p>
        ) : (
          <div className="space-y-3">
            {[...(proposals[historyTab] || [])].reverse().map((p) => <HistoryCard key={p.id} proposal={p} type={historyTab} />)}
          </div>
        )}
      </div>

      {/* Train the Agent */}
      <div>
        <div className="mb-4">
          <h2 className="text-base font-bold text-gray-100">Train the Agent</h2>
          <p className="text-xs text-gray-500 mt-0.5">Run these test inputs to trigger pattern detection</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {TRAINING_CARDS.map((card) => {
            const res     = trainResults[card.id];
            const loading = trainLoading[card.id];
            return (
              <div key={card.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-3">
                <div>
                  <p className="text-sm font-semibold text-gray-100">{card.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{card.desc}</p>
                </div>
                <div className="flex items-center justify-between mt-auto">
                  <button onClick={() => runTrainingCard(card)} disabled={loading} className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-700 text-white hover:bg-indigo-600 disabled:opacity-50 transition-colors">
                    {loading ? "Running..." : "Run Test"}
                  </button>
                  {res && (
                    <span className={`text-xs font-bold px-2 py-1 rounded-full ${res.verdict === "PASS" ? "bg-green-900 text-green-400" : res.verdict === "SOFT FAIL" ? "bg-yellow-900 text-yellow-400" : res.verdict === "HARD FAIL" ? "bg-red-900 text-red-400" : "bg-gray-800 text-gray-400"}`}>
                      {res.verdict}
                      {res.proposals > 0 && <span className="ml-1 text-indigo-400">+{res.proposals}</span>}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ProposalCard({ proposal, onApprove, onReject, approving }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="text-xs font-mono font-bold text-gray-400 bg-gray-800 px-2 py-0.5 rounded">{proposal.id}</span>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${TYPE_STYLES[proposal.type] || "bg-gray-800 text-gray-400"}`}>{proposal.type}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${PRIORITY_STYLES[proposal.priority] || "bg-gray-800 text-gray-400"}`}>{proposal.priority}</span>
        <span className="ml-auto text-xs text-gray-500">{new Date(proposal.created_at).toLocaleTimeString()}</span>
      </div>
      <div className="space-y-2 mb-4">
        <div className="bg-gray-800 rounded-lg px-3 py-2">
          <p className="text-xs font-semibold text-gray-500 mb-1">Observation</p>
          <p className="text-sm text-gray-300">{proposal.observation}</p>
        </div>
        <div className="bg-blue-950 rounded-lg px-3 py-2">
          <p className="text-xs font-semibold text-blue-400 mb-1">Proposed Action</p>
          <p className="text-sm text-gray-300">{proposal.proposed_action}</p>
        </div>
      </div>
      <div className="flex gap-2">
        <button onClick={onApprove} disabled={approving} className="flex-1 text-xs font-semibold py-2 rounded-lg bg-green-700 text-white hover:bg-green-600 disabled:opacity-50 transition-colors">
          {approving ? "Generating..." : "Approve + Generate Code"}
        </button>
        <button onClick={onReject} className="flex-1 text-xs font-semibold py-2 rounded-lg border border-red-900 text-red-400 hover:bg-red-950 transition-colors">
          Reject
        </button>
      </div>
    </div>
  );
}

function HistoryCard({ proposal, type }) {
  return (
    <div className={`border rounded-xl p-4 ${type === "approved" ? "bg-green-950 border-green-900" : "bg-gray-900 border-gray-800"}`}>
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className="text-xs font-mono font-bold text-gray-400">{proposal.id}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${TYPE_STYLES[proposal.type] || "bg-gray-800 text-gray-400"}`}>{proposal.type}</span>
        <span className="ml-auto text-xs text-gray-500">
          {type === "approved"
            ? `Approved ${new Date(proposal.approved_at).toLocaleTimeString()}`
            : `Rejected ${new Date(proposal.rejected_at || proposal.created_at).toLocaleTimeString()}`}
        </span>
      </div>
      <p className="text-sm text-gray-300 mb-2">{proposal.observation}</p>
      {type === "approved" && proposal.generated_code && (
        <div>
          <p className="text-xs font-semibold text-green-400 mb-1">Generated improvement code:</p>
          <pre className="bg-gray-950 text-green-400 rounded-lg px-4 py-3 text-xs overflow-x-auto whitespace-pre-wrap border border-gray-800">
            {proposal.generated_code}
          </pre>
        </div>
      )}
    </div>
  );
}
