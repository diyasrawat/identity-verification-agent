const VERDICT_CONFIG = {
  CLEAN: {
    bg: "bg-green-700",
    label: "CLEAN",
    subtitle: "All identity checks passed. File is clear to proceed.",
  },
  "SOFT ISSUES — HUMAN REVIEW": {
    bg: "bg-amber-600",
    label: "SOFT ISSUES — HUMAN REVIEW",
    subtitle: "Minor discrepancies detected. Recommend human review.",
  },
  "HARD BLOCK": {
    bg: "bg-red-700",
    label: "HARD BLOCK",
    subtitle: "Critical identity mismatch. Loan cannot proceed without resolution.",
  },
};

export default function VerdictBanner({ verdict }) {
  const config = VERDICT_CONFIG[verdict] ?? {
    bg: "bg-gray-700",
    label: verdict ?? "UNKNOWN",
    subtitle: "",
  };

  return (
    <div className={`w-full rounded-xl px-6 py-5 text-white ${config.bg}`}>
      <p className="text-xl font-bold tracking-wide">{config.label}</p>
      {config.subtitle && (
        <p className="mt-1 text-sm font-medium opacity-80">{config.subtitle}</p>
      )}
    </div>
  );
}
