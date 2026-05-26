import { useState } from "react";


export default function AskAIDrawer({ check, profile, onClose }) {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleExplain() {
    setLoading(true);
    setExplanation(null);
    try {
      const res = await fetch(`https://flexiloans-backend.onrender.com/api/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ check, full_profile: profile }),
      });
      const data = await res.json();
      setExplanation(data.explanation);
    } catch {
      setExplanation("Error fetching explanation. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 z-40" onClick={onClose} />
      <div className="fixed top-0 right-0 h-full w-96 bg-gray-900 border-l border-gray-800 shadow-2xl z-50 flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
          <h2 className="text-sm font-bold text-gray-100 truncate pr-4">
            AI Analysis — {check.check}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-200 text-xl font-bold leading-none"
          >
            x
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          <div className="rounded-lg bg-gray-800 border border-gray-700 p-4 space-y-2 text-sm">
            <div>
              <span className="font-semibold text-gray-400">Input A: </span>
              <span className="text-gray-200">{check.input_a ?? "—"}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-400">Input B: </span>
              <span className="text-gray-200">{check.input_b ?? "—"}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-400">Result: </span>
              <span className={check.result === "hard_fail" ? "text-red-400 font-semibold" : "text-yellow-400 font-semibold"}>
                {check.result}
              </span>
            </div>
          </div>

          <button
            onClick={handleExplain}
            disabled={loading}
            className="w-full rounded-lg bg-indigo-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-600 disabled:opacity-60 transition-colors"
          >
            {loading ? "Analysing..." : "Explain this discrepancy"}
          </button>

          {explanation && (
            <div className="rounded-lg border border-indigo-800 bg-indigo-950 px-4 py-3 text-sm text-indigo-200 leading-relaxed">
              {explanation}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
