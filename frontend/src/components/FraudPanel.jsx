const RISK_CONFIG = {
  LOW: { color: "green", bar: "bg-green-500" },
  MEDIUM: { color: "yellow", bar: "bg-yellow-500" },
  HIGH: { color: "red", bar: "bg-red-500" },
};

export default function FraudPanel({ fraudResult }) {
  if (!fraudResult) return null;

  const score = fraudResult.fraud_score ?? 0;
  const risk = fraudResult.risk_level ?? "LOW";
  const cfg = RISK_CONFIG[risk] || RISK_CONFIG.LOW;
  const signals = fraudResult.fraud_signals || [];

  return (
    <div className="space-y-4">
      {/* Score meter */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">
              Fraud Risk Score
            </p>
            <p className={`text-3xl font-bold text-${cfg.color}-600 mt-1`}>
              {score}
              <span className="text-base font-normal text-gray-400">/100</span>
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-sm font-bold text-${cfg.color}-700 bg-${cfg.color}-100`}
          >
            {risk} RISK
          </span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${cfg.bar}`}
            style={{ width: `${score}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>0 — Low</span>
          <span>30 — Medium</span>
          <span>60 — High</span>
          <span>100</span>
        </div>
      </div>

      {/* Fraud signals */}
      {signals.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Fraud Signals
          </p>
          <div className="space-y-2">
            {signals.map((s, i) => (
              <div key={i} className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded font-mono">
                      {s.signal}
                    </span>
                    <span className="text-xs text-red-500 font-semibold">
                      +{s.weight} pts
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{s.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {signals.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
          <p className="text-green-700 font-semibold text-sm">No fraud signals detected</p>
          <p className="text-green-600 text-xs mt-1">All patterns look consistent</p>
        </div>
      )}

      {/* LLM Narrative */}
      {fraudResult.fraud_narrative && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-orange-700 uppercase tracking-wide mb-2">
            Fraud Analysis Narrative
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">
            {fraudResult.fraud_narrative}
          </p>
        </div>
      )}
    </div>
  );
}
