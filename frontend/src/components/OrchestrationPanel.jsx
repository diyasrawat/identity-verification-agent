const STEP_LABELS = ["Extraction", "Identity", "Address", "Reasoning", "Fraud", "Verdict", "Audit"];

export default function OrchestrationPanel({ steps = [] }) {
  if (!steps.length) return null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h2 className="text-base font-semibold text-gray-100 mb-4">Agent Pipeline</h2>
      <div className="space-y-2">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 rounded-lg px-4 py-3 border transition-all ${
              step.status === "complete"
                ? "bg-green-950 border-green-800"
                : step.status === "running"
                ? "bg-blue-950 border-blue-800 animate-pulse"
                : "bg-gray-800 border-gray-700"
            }`}
          >
            <div className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mt-0.5
              bg-gray-700 text-gray-300">
              {step.step}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {STEP_LABELS[i] ?? `Step ${step.step}`}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  step.status === "complete"
                    ? "bg-green-900 text-green-400"
                    : step.status === "running"
                    ? "bg-blue-900 text-blue-400"
                    : "bg-gray-700 text-gray-400"
                }`}>
                  {step.status === "complete" ? "Complete" : step.status === "running" ? "Running" : "Pending"}
                </span>
              </div>
              <p className="text-sm font-medium text-gray-200 mt-0.5">{step.name}</p>
              {step.summary && (
                <p className="text-xs text-gray-500 mt-0.5">{step.summary}</p>
              )}
            </div>
            {step.status === "complete" && (
              <span className="text-green-500 text-sm font-bold">+</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
