const VERDICT_CONFIG = {
  CLEAN: {
    bg: "bg-green-600",
    icon: "✅",
    subtitle: "All identity checks passed. File is clear to proceed.",
  },
  "SOFT ISSUES — HUMAN REVIEW": {
    bg: "bg-amber-500",
    icon: "⚠️",
    subtitle: "Minor discrepancies detected. Recommend human review.",
  },
  "HARD BLOCK": {
    bg: "bg-red-600",
    icon: "🚫",
    subtitle: "Critical identity mismatch. Loan cannot proceed without resolution.",
  },
};

export default function VerdictBanner({ verdict }) {
  const config = VERDICT_CONFIG[verdict] ?? {
    bg: "bg-gray-500",
    icon: "❓",
    subtitle: "",
  };

  return (
    <div className={`w-full rounded-xl px-6 py-5 text-white ${config.bg}`}>
      <div className="flex items-center gap-3">
        <span className="text-3xl">{config.icon}</span>
        <div>
          <p className="text-xl font-bold tracking-wide">{verdict}</p>
          <p className="mt-0.5 text-sm font-medium opacity-90">{config.subtitle}</p>
        </div>
      </div>
    </div>
  );
}
