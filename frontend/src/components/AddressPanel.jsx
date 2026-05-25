const VERDICT_CONFIG = {
  CONSISTENT: { color: "green", label: "Consistent", bg: "bg-green-50 border-green-200" },
  LIKELY_SAME: { color: "yellow", label: "Likely Same", bg: "bg-yellow-50 border-yellow-200" },
  CONFLICTING: { color: "red", label: "Conflicting", bg: "bg-red-50 border-red-200" },
  NO_ADDRESS_DATA: { color: "gray", label: "No Data", bg: "bg-gray-50 border-gray-200" },
};

const scoreColor = (t) =>
  t >= 75 ? "text-green-600" : t >= 50 ? "text-yellow-600" : "text-red-500";

const scoreBarColor = (t) =>
  t >= 75 ? "bg-green-500" : t >= 50 ? "bg-yellow-500" : "bg-red-400";

export default function AddressPanel({ addressResult }) {
  if (!addressResult) return null;

  const cfg = VERDICT_CONFIG[addressResult.verdict] || VERDICT_CONFIG.NO_ADDRESS_DATA;
  const conflicts = addressResult.conflicts || [];
  const trustScores = addressResult.trust_scores || addressResult.trust_ranking || {};
  const trustReasoning = addressResult.trust_reasoning || {};
  const normalized = addressResult.normalized_addresses || {};
  const graphLookups = addressResult.graph_lookups || {};

  return (
    <div className="space-y-4">
      {/* Verdict badge */}
      <div className={`border rounded-xl p-4 ${cfg.bg}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">
              Address Verdict
            </p>
            <p className={`text-xl font-bold text-${cfg.color}-700 mt-1`}>
              {cfg.label}
            </p>
          </div>
          <div className="text-right text-sm text-gray-600">
            <p>{addressResult.hard_conflicts || 0} hard conflicts</p>
            <p>{addressResult.soft_conflicts || 0} soft conflicts</p>
          </div>
        </div>
        {addressResult.canonical_address && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide">
              Canonical Address ({addressResult.canonical_source})
            </p>
            <p className="text-sm text-gray-800 mt-1">
              {addressResult.canonical_address}
            </p>
          </div>
        )}
      </div>

      {/* Trust Ranking — with recency reasoning */}
      {Object.keys(trustScores).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Source Trust Ranking (Recency-Aware)
          </p>
          <div className="space-y-3">
            {Object.entries(trustScores)
              .sort(([, a], [, b]) => b - a)
              .map(([src, trust]) => (
                <div key={src}>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-700 font-medium w-28 capitalize">
                      {src.replace(/_/g, " ")}
                    </span>
                    <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                      <div
                        className={`h-2.5 rounded-full ${scoreBarColor(trust)}`}
                        style={{ width: `${trust}%` }}
                      />
                    </div>
                    <span className={`text-sm font-bold w-10 text-right ${scoreColor(trust)}`}>
                      {trust}
                    </span>
                  </div>
                  {trustReasoning[src] && (
                    <p className="text-xs text-gray-400 mt-0.5 pl-[7.5rem]">
                      {trustReasoning[src]}
                    </p>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Knowledge Graph Resolution */}
      {Object.keys(graphLookups).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Knowledge Graph Resolution
          </p>
          <div className="space-y-2">
            {Object.entries(graphLookups).map(([src, lookup]) => (
              <div key={src} className="flex items-start gap-3">
                <span className="text-xs text-gray-600 w-28 capitalize flex-shrink-0">
                  {src.replace(/_/g, " ")}
                </span>
                {lookup.found ? (
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs bg-green-100 text-green-700 font-semibold px-2 py-0.5 rounded-full">
                      IN GRAPH
                    </span>
                    <span className="text-xs text-gray-700">
                      {lookup.canonical_road}
                      {lookup.matched_via !== lookup.canonical_road && (
                        <span className="text-gray-400"> (via "{lookup.matched_via}")</span>
                      )}
                    </span>
                  </div>
                ) : (
                  <span className="text-xs bg-gray-100 text-gray-500 font-medium px-2 py-0.5 rounded-full">
                    NOT IN GRAPH — fuzzy matching used
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conflicts */}
      {conflicts.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Conflicts Detected
          </p>
          <div className="space-y-2">
            {conflicts.map((c, i) => (
              <div
                key={i}
                className={`rounded-lg px-3 py-2 text-sm border ${
                  c.severity === "hard" || c.method === "knowledge_graph"
                    ? "bg-red-50 border-red-200"
                    : "bg-yellow-50 border-yellow-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  {c.method === "knowledge_graph" && (
                    <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
                      🔗 GRAPH
                    </span>
                  )}
                  <span
                    className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                      c.severity === "hard"
                        ? "bg-red-100 text-red-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {c.type}
                  </span>
                  <span className="text-gray-500 text-xs">
                    {c.source_a} vs {c.source_b}
                  </span>
                </div>
                <p className="text-gray-700 mt-1 text-xs">
                  {c.method === "knowledge_graph" ? `🔗 Graph confirmed: ${c.detail}` : c.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* LLM Analysis */}
      {addressResult.agent_analysis && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2">
            AI Address Analysis
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">
            {addressResult.agent_analysis}
          </p>
        </div>
      )}

      {/* Normalized addresses */}
      {Object.keys(normalized).length > 0 && (
        <details className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <summary className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer hover:bg-gray-50">
            Normalized Addresses
          </summary>
          <div className="px-4 pb-4 space-y-2">
            {Object.entries(normalized).map(([src, addr]) => (
              <div key={src}>
                <p className="text-xs text-gray-400 capitalize">{src.replace(/_/g, " ")}</p>
                <p className="text-xs text-gray-700 font-mono">{addr}</p>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
