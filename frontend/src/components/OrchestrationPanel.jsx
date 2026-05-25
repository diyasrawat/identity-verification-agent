const STEP_ICONS = ["🔍", "🆔", "🏠", "🧠", "🚨", "⚖️", "📋"];

export default function OrchestrationPanel({ steps = [] }) {
  if (!steps.length) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h2 className="text-base font-semibold text-gray-800 mb-4">
        Agent Pipeline
      </h2>
      <div className="space-y-2">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 rounded-lg px-4 py-3 border transition-all ${
              step.status === "complete"
                ? "bg-green-50 border-green-200"
                : step.status === "running"
                ? "bg-blue-50 border-blue-200 animate-pulse"
                : "bg-gray-50 border-gray-200"
            }`}
          >
            <span className="text-lg leading-none mt-0.5">
              {STEP_ICONS[i] || "⚙️"}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Step {step.step}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    step.status === "complete"
                      ? "bg-green-100 text-green-700"
                      : step.status === "running"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {step.status === "complete"
                    ? "Complete"
                    : step.status === "running"
                    ? "Running…"
                    : "Pending"}
                </span>
              </div>
              <p className="text-sm font-medium text-gray-800 mt-0.5">
                {step.name}
              </p>
              {step.summary && (
                <p className="text-xs text-gray-500 mt-0.5">{step.summary}</p>
              )}
            </div>
            {step.status === "complete" && (
              <span className="text-green-500 text-base">✓</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
