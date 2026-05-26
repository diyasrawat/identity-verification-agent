import { useState, useEffect } from "react";


const SEVERITY_STYLES = {
  CRITICAL: "bg-red-900 text-red-300",
  HIGH:     "bg-orange-900 text-orange-300",
  MEDIUM:   "bg-yellow-900 text-yellow-300",
  LOW:      "bg-green-900 text-green-400",
};

export default function HealingPanel() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`https://flexiloans-backend.onrender.com/api/healing/log`);
        setData(await res.json());
      } catch {}
    };
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const healed      = data?.total_healed ?? 0;
  const patterns    = data?.unique_error_patterns ?? 0;
  const knownErrors = data?.known_errors ?? [];

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-indigo-400">{healed}</p>
          <p className="text-xs font-semibold text-gray-400 mt-1">Checks Self-Healed</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-orange-400">{patterns}</p>
          <p className="text-xs font-semibold text-gray-400 mt-1">Unique Error Patterns</p>
        </div>
      </div>

      {healed === 0 ? (
        <div className="bg-green-950 border border-green-900 rounded-xl p-5">
          <p className="font-semibold text-green-400">All checks running healthy</p>
          <p className="text-xs text-green-600 mt-0.5">No errors detected across any verification runs.</p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Known Error Patterns</p>
          {knownErrors.map((err, i) => (
            <div key={i} className="bg-gray-900 border border-orange-900 rounded-xl p-4">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="font-mono text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">
                  #{err.signature}
                </span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${SEVERITY_STYLES[err.severity] || "bg-gray-800 text-gray-400"}`}>
                  {err.severity}
                </span>
                {err.auto_fixable && (
                  <span className="text-xs bg-blue-900 text-blue-400 font-semibold px-2 py-0.5 rounded-full">AUTO-FIXABLE</span>
                )}
                <span className="ml-auto text-xs text-gray-500">seen {err.count}x in {err.check_name}</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="bg-red-950 rounded-lg px-3 py-2">
                  <p className="text-xs font-semibold text-red-400 mb-0.5">Root Cause</p>
                  <p className="text-gray-300">{err.root_cause}</p>
                </div>
                <div className="bg-blue-950 rounded-lg px-3 py-2">
                  <p className="text-xs font-semibold text-blue-400 mb-0.5">Proposed Fix</p>
                  <p className="text-gray-300">{err.proposed_fix}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
