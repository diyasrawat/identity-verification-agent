import { useState, useEffect } from "react";
import VerdictBanner from "./components/VerdictBanner";
import LedgerTable from "./components/LedgerTable";
import AskAIDrawer from "./components/AskAIDrawer";
import LiveTestPanel from "./components/LiveTestPanel";
import RuleEngine from "./components/RuleEngine";
import OrchestrationPanel from "./components/OrchestrationPanel";
import AddressPanel from "./components/AddressPanel";
import FraudPanel from "./components/FraudPanel";
import AuditTrail from "./components/AuditTrail";
import UnderwriterNotes from "./components/UnderwriterNotes";
import SelfImprovingAgent from "./components/SelfImprovingAgent";
import HealingPanel from "./components/HealingPanel";
import MemoryDashboard from "./components/MemoryDashboard";

const FILES = [
  { id: "FL-001", label: "FL-001 — Clean",         file: "/mock_files/file1_clean.json" },
  { id: "FL-002", label: "FL-002 — Soft Mismatch",  file: "/mock_files/file2_soft.json"  },
  { id: "FL-003", label: "FL-003 — Hard Mismatch",  file: "/mock_files/file3_hard.json"  },
];

const TABS = [
  { id: "verification", label: "Verification"      },
  { id: "address",      label: "Address"            },
  { id: "fraud",        label: "Fraud"              },
  { id: "underwriter",  label: "Underwriter"        },
  { id: "rules",        label: "Rules"              },
  { id: "live",         label: "Live Tester"        },
  { id: "audit",        label: "Audit Trail"        },
  { id: "self-improve", label: "Self-Improving"     },
  { id: "healing",      label: "Self-Healing"       },
  { id: "memory",       label: "Memory & History"   },
];

export default function App() {
  const [selectedFile,   setSelectedFile]   = useState(null);
  const [profile,        setProfile]        = useState(null);
  const [result,         setResult]         = useState(null);
  const [askAICheck,     setAskAICheck]     = useState(null);
  const [loading,        setLoading]        = useState(false);
  const [activeTab,      setActiveTab]      = useState("verification");
  const [pendingProposals, setPendingProposals] = useState(0);
  const [healedErrors,   setHealedErrors]   = useState(0);
  const [metrics,        setMetrics]        = useState(null);
  const [metricsOpen,    setMetricsOpen]    = useState(false);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [judgeRunning,   setJudgeRunning]   = useState(false);
  const [judgeToast,     setJudgeToast]     = useState(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const res  = await fetch("/api/self-improve/stats");
        const data = await res.json();
        setPendingProposals(data.pending_proposals ?? 0);
      } catch {}
    };
    poll();
    const id = setInterval(poll, 10000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const pollHealing = async () => {
      try {
        const res  = await fetch("/api/healing/log");
        const data = await res.json();
        setHealedErrors(data.total_healed ?? 0);
      } catch {}
    };
    pollHealing();
    const id = setInterval(pollHealing, 10000);
    return () => clearInterval(id);
  }, []);

  async function handleSelectFile(fileConfig) {
    setSelectedFile(fileConfig.id);
    setResult(null);
    setAskAICheck(null);
    setLoading(true);
    setActiveTab("verification");
    try {
      const fileRes = await fetch(fileConfig.file);
      const data    = await fileRes.json();
      setProfile(data);
      const res        = await fetch("/api/orchestrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      setResult(await res.json());
    } catch (err) {
      console.error("Orchestration failed:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleJudgeDemo() {
    setJudgeRunning(true);
    setJudgeToast(null);
    try {
      const res  = await fetch("/api/test/run-all-judge-cases", { method: "POST" });
      const data = await res.json();
      setJudgeToast({
        type: data.accuracy === 100 ? "success" : "warn",
        msg:  `Judge Demo: ${data.correct}/${data.total} passed (${data.accuracy}% accuracy) — saved to Memory`,
      });
      setActiveTab("memory");
    } catch {
      setJudgeToast({ type: "error", msg: "Judge Demo failed — is the backend running?" });
    } finally {
      setJudgeRunning(false);
      setTimeout(() => setJudgeToast(null), 6000);
    }
  }

  const checks    = result?.checks ?? [];
  const passed    = checks.filter((c) => c.result === "pass").length;
  const hardFails = checks.filter((c) => c.result === "hard_fail").length;
  const softFails = checks.filter((c) => c.result === "soft_fail").length;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Toast */}
      {judgeToast && (
        <div className={`fixed top-4 right-4 z-50 rounded-xl px-5 py-3 text-sm font-medium shadow-xl transition-all ${
          judgeToast.type === "success" ? "bg-green-700 text-white" :
          judgeToast.type === "warn"    ? "bg-amber-600 text-white" : "bg-red-700 text-white"
        }`}>
          {judgeToast.msg}
        </div>
      )}

      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-100">VerifyIQ: Identity Cross-Verification Agent</h1>
          <p className="text-xs text-gray-500 mt-0.5">FlexiLoans · Underwriting Desk</p>
        </div>
        <button
          onClick={handleJudgeDemo}
          disabled={judgeRunning}
          className="rounded-lg bg-violet-700 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-600 disabled:opacity-60 transition-colors"
        >
          {judgeRunning ? "Running 10 Judge Cases..." : "Run Judge Demo"}
        </button>
      </header>

      {/* Tab bar */}
      <div className="bg-gray-900 border-b border-gray-800 px-6">
        <div className="flex gap-0 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? "border-indigo-400 text-indigo-400"
                  : "border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-600"
              }`}
            >
              {tab.label}
              {tab.id === "self-improve" && pendingProposals > 0 && (
                <span className="relative inline-flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                </span>
              )}
              {tab.id === "healing" && healedErrors > 0 && (
                <span className="relative inline-flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* File selector */}
        {["verification", "address", "fraud", "underwriter"].includes(activeTab) && (
          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">Select Applicant File</p>
            <div className="flex gap-3 flex-wrap">
              {FILES.map((f) => (
                <button
                  key={f.id}
                  onClick={() => handleSelectFile(f)}
                  disabled={loading}
                  className={`rounded-lg px-5 py-2.5 text-sm font-semibold border transition-colors disabled:opacity-50 ${
                    selectedFile === f.id
                      ? "bg-indigo-700 text-white border-indigo-600"
                      : "bg-gray-900 text-gray-300 border-gray-700 hover:border-indigo-500 hover:text-indigo-300"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="text-sm text-indigo-400 font-medium animate-pulse mb-6">Running agentic pipeline...</div>
        )}

        {/* Verification tab */}
        {activeTab === "verification" && (
          <div className="space-y-6">
            {!loading && !result && (
              <div className="rounded-xl border-2 border-dashed border-gray-800 py-16 text-center text-gray-600 text-sm">
                Select an applicant file above to begin verification
              </div>
            )}

            {result && !loading && (
              <>
                <OrchestrationPanel steps={result.pipeline_steps} />
                <VerdictBanner verdict={result.identity_verdict} />

                {result.confidence_score && (
                  <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold text-gray-200">Identity Confidence Score</span>
                      <span className={`font-bold text-lg ${
                        result.confidence_score.color === "green"  ? "text-green-400"  :
                        result.confidence_score.color === "yellow" ? "text-yellow-400" : "text-red-400"
                      }`}>
                        {result.confidence_score.score}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-4">
                      <div
                        className={`h-4 rounded-full transition-all duration-700 ${
                          result.confidence_score.color === "green"  ? "bg-green-500"  :
                          result.confidence_score.color === "yellow" ? "bg-yellow-500" : "bg-red-500"
                        }`}
                        style={{ width: `${result.confidence_score.score}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {result.confidence_score.label} · Critical checks (DOB, PAN format, Aadhaar) weighted 2x
                    </p>
                  </div>
                )}

                {result.reasoning_result?.agent_note && (
                  <div className="bg-indigo-950 border border-indigo-900 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="font-bold text-indigo-300 text-sm">Agent Reasoning</span>
                      <span className={`ml-auto px-3 py-1 rounded-full text-xs font-bold ${
                        result.reasoning_result.recommendation === "PROCEED" ? "bg-green-900 text-green-400" :
                        result.reasoning_result.recommendation === "REJECT"  ? "bg-red-900 text-red-400"   :
                        "bg-yellow-900 text-yellow-400"
                      }`}>
                        {result.reasoning_result.recommendation}
                      </span>
                    </div>
                    <p className="text-sm text-indigo-200 mb-2">{result.reasoning_result.agent_note}</p>
                    <p className="text-xs text-indigo-400">
                      Confidence: {result.reasoning_result.confidence} · {result.reasoning_result.reasoning}
                    </p>
                  </div>
                )}

                <LedgerTable checks={result.checks} onAskAI={setAskAICheck} />

                <div className="flex gap-6 text-sm text-gray-500 bg-gray-900 rounded-xl border border-gray-800 px-6 py-3">
                  <span><span className="font-bold text-gray-100">{checks.length}</span> Checks Run</span>
                  <span className="text-gray-700">|</span>
                  <span><span className="font-bold text-green-400">{passed}</span> Passed</span>
                  <span className="text-gray-700">|</span>
                  <span>
                    <span className="font-bold text-red-400">{hardFails + softFails}</span> Failed
                    {(hardFails + softFails) > 0 && (
                      <span className="text-gray-600 ml-1">({hardFails} hard, {softFails} soft)</span>
                    )}
                  </span>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === "address" && (
          <div>
            {!result && !loading && (
              <div className="rounded-xl border-2 border-dashed border-gray-800 py-16 text-center text-gray-600 text-sm">
                Select an applicant file above to run address analysis
              </div>
            )}
            {result && !loading && <AddressPanel addressResult={result.address_result} />}
          </div>
        )}

        {activeTab === "fraud" && (
          <div>
            {!result && !loading && (
              <div className="rounded-xl border-2 border-dashed border-gray-800 py-16 text-center text-gray-600 text-sm">
                Select an applicant file above to run fraud analysis
              </div>
            )}
            {result && !loading && <FraudPanel fraudResult={result.fraud_result} />}
          </div>
        )}

        {activeTab === "underwriter" && (
          <div>
            {!result && !loading && (
              <div className="rounded-xl border-2 border-dashed border-gray-800 py-16 text-center text-gray-600 text-sm">
                Select an applicant file above to generate underwriter notes
              </div>
            )}
            {result && !loading && (
              <UnderwriterNotes verdictResult={result.final_verdict} applicantId={result.applicant_id} />
            )}
          </div>
        )}

        {activeTab === "rules"        && <RuleEngine />}
        {activeTab === "live"         && <LiveTestPanel />}
        {activeTab === "audit"        && <AuditTrail />}
        {activeTab === "self-improve" && <SelfImprovingAgent />}
        {activeTab === "healing"      && <HealingPanel />}
        {activeTab === "memory"       && <MemoryDashboard />}

        {/* System Accuracy Metrics */}
        {activeTab === "verification" && (
          <div className="mt-4">
            <button
              onClick={async () => {
                setMetricsOpen((o) => !o);
                if (!metrics && !metricsLoading) {
                  setMetricsLoading(true);
                  try {
                    const res = await fetch("/api/evaluation/metrics");
                    setMetrics(await res.json());
                  } finally {
                    setMetricsLoading(false);
                  }
                }
              }}
              className="flex items-center gap-2 text-xs font-semibold text-gray-600 hover:text-gray-400 transition-colors"
            >
              <span>{metricsOpen ? "v" : ">"}</span>
              System Accuracy Metrics
            </button>
            {metricsOpen && (
              <div className="mt-3 rounded-xl border border-gray-800 bg-gray-900 p-5">
                {metricsLoading && (
                  <p className="text-xs text-indigo-400 animate-pulse">Running all 3 mock files to compute accuracy...</p>
                )}
                {metrics && !metricsLoading && (
                  <>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                      {[
                        { label: "Precision", value: `${metrics.precision}%`,  sub: metrics.interpretation?.precision },
                        { label: "Recall",    value: `${metrics.recall}%`,     sub: metrics.interpretation?.recall    },
                        { label: "F1 Score",  value: `${metrics.f1_score}%`,   sub: metrics.interpretation?.f1        },
                        { label: "Accuracy",  value: `${metrics.accuracy}%`,   sub: `${metrics.true_positives} TP · ${metrics.true_negatives} TN · ${metrics.false_positives} FP · ${metrics.false_negatives} FN` },
                      ].map((m) => (
                        <div key={m.label} className="bg-gray-800 rounded-lg p-3 text-center border border-gray-700">
                          <p className="text-xl font-bold text-indigo-400">{m.value}</p>
                          <p className="text-xs font-semibold text-gray-300 mt-0.5">{m.label}</p>
                          {m.sub && <p className="text-xs text-gray-500 mt-1">{m.sub}</p>}
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-gray-600">
                      Architecture: Hybrid deterministic + AI · 7 checks run as pure code &lt;100ms ·
                      LLM fires only on soft-fail names · Model: Claude Haiku · Cost/file: ~$0.001
                    </p>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      {askAICheck && (
        <AskAIDrawer check={askAICheck} profile={profile} onClose={() => setAskAICheck(null)} />
      )}
    </div>
  );
}
