const ROW_BG = {
  pass: "bg-green-50",
  soft_fail: "bg-yellow-50",
  hard_fail: "bg-red-50",
};

const BADGE = {
  pass: "bg-green-100 text-green-800",
  soft_fail: "bg-yellow-100 text-yellow-800",
  hard_fail: "bg-red-100 text-red-800",
};

const BADGE_LABEL = {
  pass: "Pass",
  soft_fail: "Soft Fail",
  hard_fail: "Hard Fail",
};

export default function LedgerTable({ checks, onAskAI }) {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
      <table className="w-full text-sm text-left">
        <thead className="bg-gray-100 text-xs uppercase text-gray-600 tracking-wider">
          <tr>
            <th className="px-4 py-3">Check</th>
            <th className="px-4 py-3">Input A</th>
            <th className="px-4 py-3">Input B</th>
            <th className="px-4 py-3">Result</th>
            <th className="px-4 py-3">Reason</th>
            <th className="px-4 py-3">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {checks.map((check, i) => (
            <tr key={i} className={ROW_BG[check.result] ?? ""}>
              <td className="px-4 py-3 font-medium text-gray-800 whitespace-nowrap">
                {check.check}
              </td>
              <td className="px-4 py-3 text-gray-700">
                {check.input_a ?? <span className="text-gray-400">—</span>}
              </td>
              <td className="px-4 py-3 text-gray-700">
                {check.input_b ?? <span className="text-gray-400">—</span>}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE[check.result]}`}
                >
                  {BADGE_LABEL[check.result] ?? check.result}
                </span>
                {check.fuzzy_score !== undefined && (
                  <span className="ml-2 text-xs text-gray-400">
                    ({check.fuzzy_score})
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-gray-600 max-w-xs">
                {check.reason ?? <span className="text-gray-400">—</span>}
              </td>
              <td className="px-4 py-3">
                {(check.result === "soft_fail" || check.result === "hard_fail") && (
                  <button
                    onClick={() => onAskAI(check)}
                    className="rounded bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-700 transition-colors"
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
