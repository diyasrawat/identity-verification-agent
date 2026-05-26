const RISK_CONFIG = {
  LOW:    { textColor: "text-green-400",  bar: "bg-green-500",  badge: "bg-green-900 text-green-400"  },
  MEDIUM: { textColor: "text-yellow-400", bar: "bg-yellow-500", badge: "bg-yellow-900 text-yellow-400" },
  HIGH:   { textColor: "text-red-400",    bar: "bg-red-500",    badge: "bg-red-900 text-red-400"   },
};

export default function FraudPanel({ fraudResult }) {
  if (!fraudResult) return null;

  const score = fraudResult.fraud_score ?? 0;
  const risk = fraudResult.risk_level ?? "LOW";
  const cfg = RISK_CONFIG[risk] || RISK_CONFIG.LOW;
  const signals = fraudResult.fraud_signals || [];

  return (
    <div className="space-y-4">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">Fraud Risk Score</p>
            <p className={`text-3xl font-bold mt-1 ${cfg.textColor}`}>
              {score}
              <span className="text-base font-normal text-gray-500">/100</span>
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-bold ${cfg.badge}`}>
            {risk} RISK
          </span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-3">
          <div className={`h-3 rounded-full transition-all duration-500 ${cfg.bar}`} style={{ width: `${score}%` }} />
        </div>
        <div className="flex justify-between text-xs text-gray-600 mt-1">
          <span>0 — Low</span>
          <span>30 — Medium</span>
          <span>60 — High</span>
          <span>100</span>
        </div>
      </div>

      {signals.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Fraud Signals</p>
          <div className="space-y-2">
            {signals.map((s, i) => (
              <div key={i} className="flex items-start gap-3 bg-red-950 border border-red-900 rounded-lg px-3 py-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-red-400 bg-red-900 px-1.5 py-0.5 rounded font-mono">
                      {s.signal}
                    </span>
                    <span className="text-xs text-red-400 font-semibold">+{s.weight} pts</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{s.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {signals.length === 0 && (
        <div className="bg-green-950 border border-green-900 rounded-xl p-4 text-center">
          <p className="text-green-400 font-semibold text-sm">No fraud signals detected</p>
          <p className="text-green-600 text-xs mt-1">All patterns look consistent</p>
        </div>
      )}

      {fraudResult.fraud_narrative && (
        <div className="bg-gray-900 border border-amber-900 rounded-xl p-4">
          <p className="text-xs font-semibold text-amber-500 uppercase tracking-wide mb-2">Fraud Analysis</p>
          <p className="text-sm text-gray-300 leading-relaxed">{fraudResult.fraud_narrative}</p>
        </div>
      )}
    </div>
  );
}
