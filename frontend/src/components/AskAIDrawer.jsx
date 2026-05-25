import { useState } from "react";

export default function AskAIDrawer({ check, profile, onClose }) {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleExplain() {
    setLoading(true);
    setExplanation(null);
    try {
      const res = await fetch("/api/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ check, full_profile: profile }),
      });
      const data = await res.json();
      setExplanation(data.explanation);
    } catch (err) {
      setExplanation("Error fetching explanation. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed top-0 right-0 h-full w-96 bg-white shadow-2xl z-50 flex flex-col"
        style={{ width: "384px" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <h2 className="text-sm font-bold text-gray-800 truncate pr-4">
            Ask AI — {check.check}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 text-xl font-bold leading-none"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {/* Context card */}
          <div className="rounded-lg bg-gray-100 p-4 space-y-2 text-sm">
            <div>
              <span className="font-semibold text-gray-600">Input A: </span>
              <span className="text-gray-800">{check.input_a ?? "—"}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-600">Input B: </span>
              <span className="text-gray-800">{check.input_b ?? "—"}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-600">Result: </span>
              <span
                className={
                  check.result === "hard_fail"
                    ? "text-red-700 font-semibold"
                    : "text-yellow-700 font-semibold"
                }
              >
                {check.result}
              </span>
            </div>
          </div>

          {/* Explain button */}
          <button
            onClick={handleExplain}
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            {loading ? "Analysing…" : "Explain this discrepancy"}
          </button>

          {/* Result */}
          {explanation && (
            <div className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-900 leading-relaxed">
              {explanation}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
