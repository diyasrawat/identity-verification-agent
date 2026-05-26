import { useState } from "react";

const VERDICT_STYLES = {
  PROCEED: { header: "bg-green-800",  badge: "bg-green-900 text-green-300",  border: "border-green-800"  },
  REVIEW:  { header: "bg-amber-700",  badge: "bg-amber-900 text-amber-300",  border: "border-amber-800"  },
  REJECT:  { header: "bg-red-800",    badge: "bg-red-900 text-red-300",      border: "border-red-800"    },
};

export default function UnderwriterNotes({ verdictResult, applicantId }) {
  const [copied, setCopied] = useState(false);

  if (!verdictResult) return null;

  const verdict = verdictResult.final_verdict;
  const styles  = VERDICT_STYLES[verdict] || VERDICT_STYLES.REVIEW;
  const notes   = verdictResult.underwriter_notes || "";
  const factors = verdictResult.decision_factors || {};

  const handleCopy = () => {
    const text = `UNDERWRITER NOTES\nApplicant: ${applicantId || "UNKNOWN"}\nDecision: ${verdict}\n\n${notes}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className={`border ${styles.border} rounded-xl overflow-hidden`}>
      <div className={`${styles.header} px-5 py-4 flex items-center justify-between`}>
        <div>
          <p className="text-white/60 text-xs font-semibold uppercase tracking-widest">Underwriter Notes</p>
          <p className="text-white font-bold text-lg mt-0.5">{applicantId || "UNKNOWN"}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-sm font-bold ${styles.badge}`}>{verdict}</span>
          <button
            onClick={handleCopy}
            className="text-white/70 hover:text-white text-sm border border-white/20 px-3 py-1 rounded-lg transition-colors"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      <div className="bg-gray-900 p-5">
        {notes ? (
          <div>
            {notes.split("\n").map((line, i) => {
              if (!line.trim()) return <div key={i} className="h-2" />;
              if (line.match(/^\d+\./)) return <p key={i} className="font-semibold text-gray-100 mt-3 mb-1">{line}</p>;
              if (line.startsWith("•") || line.startsWith("-")) return <p key={i} className="text-gray-300 pl-3 text-sm leading-relaxed">{line}</p>;
              return <p key={i} className="text-gray-300 text-sm leading-relaxed">{line}</p>;
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-sm italic">No underwriter notes available.</p>
        )}
      </div>

      {Object.keys(factors).length > 0 && (
        <div className="border-t border-gray-800 bg-gray-900 px-5 py-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Factor label="Identity"    value={factors.identity_verdict} />
          <Factor label="Address"     value={factors.address_verdict} />
          <Factor label="Fraud Score" value={factors.fraud_score != null ? `${factors.fraud_score}/100` : "—"} />
          <Factor label="Confidence"  value={factors.confidence_score != null ? `${factors.confidence_score}%` : "—"} />
        </div>
      )}
    </div>
  );
}

function Factor({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-500 font-medium">{label}</p>
      <p className="text-sm font-semibold text-gray-200 truncate">{value ?? "—"}</p>
    </div>
  );
}
