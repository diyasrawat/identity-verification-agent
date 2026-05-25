import { useState, useEffect } from "react";

const SEVERITY_STYLES = {
  CRITICAL: "bg-red-100 text-red-800",
  HIGH: "bg-orange-100 text-orange-800",
  MEDIUM: "bg-yellow-100 text-yellow-800",
  LOW: "bg-green-100 text-green-700",
};

export default function HealingPanel() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetch_ = async () => {
      try {
        const res = await fetch("/api/healing/log");
        setData(await res.json());
      } catch {}
    };
    fetch_();
    const id = setInterval(fetch_, 5000);
    return () => clearInterval(id);
  }, []);

  const healed = data?.total_healed ?? 0;
  const patterns = data?.unique_error_patterns ?? 0;
  const knownErrors = data?.known_errors ?? [];

  return (
    <div className="space-y-5">
      {/* Stats bar */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-indigo-600">{healed}</p>
          <p className="text-xs font-semibold text-gray-600 mt-1">Checks Self-Healed</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-orange-500">{patterns}</p>
          <p className="text-xs font-semibold text-gray-600 mt-1">Unique Error Patterns</p>
        </div>
      </div>

      {/* Status */}
      {healed === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-xl p-5 flex items-center gap-3">
          <span className="text-2xl">✅</span>
          <div>
            <p className="font-semibold text-green-800">All checks running healthy</p>
            <p className="text-xs text-green-600 mt-0.5">No errors detected across any verification runs.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Known Error Patterns
          </p>
          {knownErrors.map((err, i) => (
            <div key={i} className="bg-white border border-orange-200 rounded-xl p-4">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="font-mono text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                  #{err.signature}
                </span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${SEVERITY_STYLES[err.severity] || "bg-gray-100 text-gray-600"}`}>
                  {err.severity}
                </span>
                {err.auto_fixable && (
                  <span className="text-xs bg-blue-100 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
                    AUTO-FIXABLE
                  </span>
                )}
                <span className="ml-auto text-xs text-gray-400">
                  seen {err.count}× in {err.check_name}
                </span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="bg-red-50 rounded-lg px-3 py-2">
                  <p className="text-xs font-semibold text-red-600 mb-0.5">Root Cause</p>
                  <p className="text-gray-700">{err.root_cause}</p>
                </div>
                <div className="bg-blue-50 rounded-lg px-3 py-2">
                  <p className="text-xs font-semibold text-blue-600 mb-0.5">Proposed Fix</p>
                  <p className="text-gray-700">{err.proposed_fix}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
