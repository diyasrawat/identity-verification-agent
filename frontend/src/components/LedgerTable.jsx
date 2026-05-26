const ROW_BG = {
  pass: "border-l-2 border-green-600",
  soft_fail: "border-l-2 border-yellow-500",
  hard_fail: "border-l-2 border-red-500",
};

const BADGE = {
  pass: "bg-green-900 text-green-400",
  soft_fail: "bg-yellow-900 text-yellow-400",
  hard_fail: "bg-red-900 text-red-400",
};

const BADGE_LABEL = {
  pass: "Pass",
  soft_fail: "Soft Fail",
  hard_fail: "Hard Fail",
};

export default function LedgerTable({ checks, onAskAI }) {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-gray-800 shadow-sm">
      <table className="w-full text-sm text-left">
        <thead className="bg-gray-800 text-xs uppercase text-gray-400 tracking-wider">
          <tr>
            <th className="px-4 py-3">Check</th>
            <th className="px-4 py-3">Input A</th>
            <th className="px-4 py-3">Input B</th>
            <th className="px-4 py-3">Result</th>
            <th className="px-4 py-3">Reason</th>
            <th className="px-4 py-3">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {checks.map((check, i) => (
            <tr key={i} className={`bg-gray-900 ${ROW_BG[check.result] ?? ""}`}>
              <td className="px-4 py-3 font-medium text-gray-100 whitespace-nowrap">
                {check.check}
                {check.is_custom && (
                  <span className="ml-2 rounded-full bg-violet-900 px-2 py-0.5 text-xs font-bold text-violet-300">
                    CUSTOM RULE
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-gray-300">
                {check.input_a ?? <span className="text-gray-600">—</span>}
              </td>
              <td className="px-4 py-3 text-gray-300">
                {check.input_b ?? <span className="text-gray-600">—</span>}
              </td>
              <td className="px-4 py-3">
                <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE[check.result]}`}>
                  {BADGE_LABEL[check.result] ?? check.result}
                </span>
                {check.fuzzy_score !== undefined && (check.result === "soft_fail" || check.result === "hard_fail") && (
                  <div className="text-xs text-gray-500 mt-0.5">({check.fuzzy_score}% match)</div>
                )}
              </td>
              <td className="px-4 py-3 text-gray-400 max-w-xs">
                {check.reason ?? <span className="text-gray-600">—</span>}
              </td>
              <td className="px-4 py-3">
                {(check.result === "soft_fail" || check.result === "hard_fail") && (
                  <button
                    onClick={() => onAskAI(check)}
                    className="rounded bg-indigo-700 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-600 transition-colors"
                  >
                    Ask AI
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
