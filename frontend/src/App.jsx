import { useState } from "react";

const ARCH_NOTES = `Architecture: Hybrid deterministic + AI. 7 checks run as pure code — zero LLM cost, <100ms. AI fires only on soft-fail name checks and Ask AI clicks. Model: Claude Haiku. Cost per file: <$0.001 (max 3 LLM calls × ~150 tokens). At 50,000 files/day: ~$50/day.`;
import VerdictBanner from "./components/VerdictBanner";
import LedgerTable from "./components/LedgerTable";
import AskAIDrawer from "./components/AskAIDrawer";
import LiveTestPanel from "./components/LiveTestPanel";
import RuleEngine from "./components/RuleEngine";

const FILES = [
  { id: "FL-001", label: "FL-001 — Clean", file: "/mock_files/file1_clean.json" },
  { id: "FL-002", label: "FL-002 — Soft Mismatch", file: "/mock_files/file2_soft.json" },
  { id: "FL-003", label: "FL-003 — Hard Mismatch", file: "/mock_files/file3_hard.json" },
];

export default function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [archOpen, setArchOpen] = useState(false);
  const [profile, setProfile] = useState(null);
  const [result, setResult] = useState(null);
  const [askAICheck, setAskAICheck] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSelectFile(fileConfig) {
    setSelectedFile(fileConfig.id);
    setResult(null);
    setAskAICheck(null);
    setLoading(true);

    try {
      const fileRes = await fetch(fileConfig.file);
      const data = await fileRes.json();
      setProfile(data);

      const verifyRes = await fetch("/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const verifyData = await verifyRes.json();
      setResult(verifyData);
    } catch (err) {
      console.error("Verification failed:", err);
    } finally {
      setLoading(false);
    }
  }

  const checks = result?.checks ?? [];
  const passed = checks.filter((c) => c.result === "pass").length;
  const hardFails = checks.filter((c) => c.result === "hard_fail").length;
  const softFails = checks.filter((c) => c.result === "soft_fail").length;
  const failed = hardFails + softFails;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Top bar */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-lg font-bold text-gray-800">
          Identity Cross-Verification Agent
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          FlexiLoans · Underwriting Desk
        </p>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* File selector */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">
            Select Applicant File
          </p>
          <div className="flex gap-3 flex-wrap">
            {FILES.map((f) => (
              <button
                key={f.id}
                onClick={() => handleSelectFile(f)}
                disabled={loading}
                className={`rounded-lg px-5 py-2.5 text-sm font-semibold border transition-colors disabled:opacity-50 ${
                  selectedFile === f.id
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400 hover:text-indigo-600"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="text-sm text-indigo-600 font-medium animate-pulse">
            Running identity checks…
          </div>
        )}

        {/* Placeholder */}
        {!loading && !result && (
          <div className="rounded-xl border-2 border-dashed border-gray-300 py-16 text-center text-gray-400 text-sm">
            Select an applicant file above to begin verification
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <>
            <VerdictBanner verdict={result.verdict} />

            {/* Confidence Score Bar */}
            {result.confidence_score && (
              <div className="bg-white border border-gray-200 rounded-xl p-5">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold text-gray-800">Identity Confidence Score</span>
                  <span className={`font-bold text-lg ${
                    result.confidence_score.color === "green" ? "text-green-600" :
                    result.confidence_score.color === "yellow" ? "text-yellow-600" :
                    "text-red-600"
                  }`}>
                    {result.confidence_score.score}%
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full transition-all duration-700 ${
                      result.confidence_score.color === "green" ? "bg-green-500" :
                      result.confidence_score.color === "yellow" ? "bg-yellow-500" :
                      "bg-red-500"
                    }`}
                    style={{ width: `${result.confidence_score.score}%` }}
                  />
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {result.confidence_score.label}
                  {" · "}Critical checks (DOB, PAN format, Aadhaar) weighted 2×
                </p>
              </div>
            )}

            {/* Agent Analysis card */}
            {result.agent_note && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-indigo-600 text-lg">🤖</span>
                  <span className="font-bold text-indigo-900">Agent Analysis</span>
                  <span
                    className={`ml-auto px-3 py-1 rounded-full text-xs font-bold ${
                      result.recommendation === "PROCEED"
                        ? "bg-green-100 text-green-800"
                        : result.recommendation === "REJECT"
                        ? "bg-red-100 text-red-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}
                  >
                    {result.recommendation}
                  </span>
                </div>
                <p className="text-sm text-indigo-800 mb-2">{result.agent_note}</p>
                <p className="text-xs text-indigo-600">
                  Confidence: {result.confidence} · {result.reasoning}
                </p>
              </div>
            )}

            <LedgerTable checks={result.checks} onAskAI={setAskAICheck} />

            {/* Footer stats */}
            <div className="flex gap-6 text-sm text-gray-600 bg-white rounded-xl border border-gray-200 px-6 py-3">
              <span>
                <span className="font-bold text-gray-800">{checks.length}</span> Checks Run
              </span>
              <span className="text-gray-300">|</span>
              <span>
                <span className="font-bold text-green-700">{passed}</span> Passed
              </span>
              <span className="text-gray-300">|</span>
              <span>
                <span className="font-bold text-red-600">{failed}</span> Failed
                {failed > 0 && (
                  <span className="text-gray-400 ml-1">
                    ({hardFails} hard, {softFails} soft)
                  </span>
                )}
              </span>
            </div>
          </>
        )}
      </main>

      {/* Rule Engine */}
      <div className="max-w-6xl mx-auto px-6 mt-10">
        <RuleEngine />
      </div>

      {/* Live Test Panel */}
      <div className="max-w-6xl mx-auto px-6 mt-10">
        <LiveTestPanel />
      </div>

      {/* Architecture Notes */}
      <div className="max-w-6xl mx-auto px-6 pb-10">
        <button
          onClick={() => setArchOpen((o) => !o)}
          className="flex items-center gap-2 text-xs font-semibold text-gray-400 hover:text-gray-600 transition-colors"
        >
          <span>{archOpen ? "▾" : "▸"}</span>
          Architecture Notes
        </button>
        {archOpen && (
          <div className="mt-2 rounded-lg border border-gray-200 bg-white px-5 py-4 text-xs text-gray-600 leading-relaxed">
            {ARCH_NOTES}
          </div>
        )}
      </div>

      {/* Ask AI Drawer */}
      {askAICheck && (
        <AskAIDrawer
          check={askAICheck}
          profile={profile}
          onClose={() => setAskAICheck(null)}
        />
      )}
    </div>
  );
}
