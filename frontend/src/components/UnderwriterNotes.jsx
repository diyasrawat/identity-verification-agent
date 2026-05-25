import { useState } from "react";

const VERDICT_STYLES = {
  PROCEED: {
    header: "bg-green-700",
    badge: "bg-green-100 text-green-800",
    border: "border-green-200",
  },
  REVIEW: {
    header: "bg-yellow-600",
    badge: "bg-yellow-100 text-yellow-800",
    border: "border-yellow-200",
  },
  REJECT: {
    header: "bg-red-700",
    badge: "bg-red-100 text-red-800",
    border: "border-red-200",
  },
};

export default function UnderwriterNotes({ verdictResult, applicantId }) {
  const [copied, setCopied] = useState(false);

  if (!verdictResult) return null;

  const verdict = verdictResult.final_verdict;
  const styles = VERDICT_STYLES[verdict] || VERDICT_STYLES.REVIEW;
  const notes = verdictResult.underwriter_notes || "";
  const factors = verdictResult.decision_factors || {};

  const handleCopy = () => {
    const text = `UNDERWRITER NOTES\nApplicant: ${applicantId || "UNKNOWN"}\nDecision: ${verdict}\n\n${notes}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className={`border rounded-xl overflow-hidden ${styles.border}`}>
      {/* Header bar */}
      <div className={`${styles.header} px-5 py-4 flex items-center justify-between`}>
        <div>
          <p className="text-white/70 text-xs font-semibold uppercase tracking-widest">
            Underwriter Notes
          </p>
          <p className="text-white font-bold text-lg mt-0.5">
            {applicantId || "UNKNOWN"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-sm font-bold ${styles.badge}`}>
            {verdict}
          </span>
          <button
            onClick={handleCopy}
            className="text-white/80 hover:text-white text-sm border border-white/30 px-3 py-1 rounded-lg transition-colors"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      {/* Notes body */}
      <div className="bg-white p-5">
        {notes ? (
          <div className="prose prose-sm max-w-none">
            {notes.split("\n").map((line, i) => {
              if (!line.trim()) return <div key={i} className="h-2" />;
              if (line.match(/^\d+\./)) {
                return (
                  <p key={i} className="font-semibold text-gray-800 mt-3 mb-1">
                    {line}
                  </p>
                );
              }
              if (line.startsWith("•") || line.startsWith("-")) {
                return (
                  <p key={i} className="text-gray-700 pl-3 text-sm leading-relaxed">
                    {line}
                  </p>
                );
              }
              return (
                <p key={i} className="text-gray-700 text-sm leading-relaxed">
                  {line}
                </p>
              );
            })}
          </div>
        ) : (
          <p className="text-gray-400 text-sm italic">No underwriter notes available.</p>
        )}
      </div>

      {/* Decision factors footer */}
      {Object.keys(factors).length > 0 && (
        <div className="border-t border-gray-100 bg-gray-50 px-5 py-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Factor label="Identity" value={factors.identity_verdict} />
          <Factor label="Address" value={factors.address_verdict} />
          <Factor label="Fraud Score" value={factors.fraud_score != null ? `${factors.fraud_score}/100` : "—"} />
          <Factor label="Confidence" value={factors.confidence_score != null ? `${factors.confidence_score}%` : "—"} />
        </div>
      )}
    </div>
  );
}

function Factor({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-400 font-medium">{label}</p>
      <p className="text-sm font-semibold text-gray-700 truncate">{value ?? "—"}</p>
    </div>
  );
}
