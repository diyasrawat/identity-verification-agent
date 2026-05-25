import { useState, useEffect } from "react";

const EXAMPLE_RULES = [
  "Gender on PAN and Aadhaar must match exactly",
  "Bureau linked PAN must exactly match the submitted PAN number",
  "Aadhaar last 4 digits must appear in the bureau record",
  "Father name on PAN must have at least 2 words",
  "PAN number must start with 5 uppercase letters",
  "Name on bureau and Aadhaar must be at least 70% similar",
];

export default function RuleEngine() {
  const [ruleText, setRuleText] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(null); // { func_name, generated_code, rule_description }
  const [saving, setSaving] = useState(false);
  const [activeRules, setActiveRules] = useState([]);

  useEffect(() => {
    fetchRules();
  }, []);

  async function fetchRules() {
    try {
      const res = await fetch("/api/rules/list");
      const data = await res.json();
      setActiveRules(data.rules ?? []);
    } catch (_) {}
  }

  async function handleGenerate() {
    if (!ruleText.trim()) return;
    setGenerating(true);
    setGenerated(null);
    try {
      const res = await fetch("/api/rules/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule_description: ruleText.trim() }),
      });
      const data = await res.json();
      setGenerated(data);
    } catch (err) {
      console.error("Rule generation failed:", err);
    } finally {
      setGenerating(false);
    }
  }

  async function handleSave() {
    if (!generated) return;
    setSaving(true);
    try {
      await fetch("/api/rules/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(generated),
      });
      await fetchRules();
      setGenerated(null);
      setRuleText("");
    } catch (err) {
      console.error("Save failed:", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(func_name) {
    try {
      await fetch(`/api/rules/${func_name}`, { method: "DELETE" });
      await fetchRules();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-base font-bold text-gray-800">⚙️ Rule Engine</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Write a rule in plain English — the agent converts it to a live verification check
        </p>
      </div>

      {/* SECTION A — Rule Input */}
      <div className="space-y-3">
        <textarea
          rows={4}
          value={ruleText}
          onChange={(e) => setRuleText(e.target.value)}
          placeholder="e.g. PAN number last 4 characters before the final letter must be numeric digits only"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
        />

        {/* Example chips */}
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_RULES.map((ex) => (
            <button
              key={ex}
              onClick={() => setRuleText(ex)}
              className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs text-indigo-700 hover:bg-indigo-100 transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating || !ruleText.trim()}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
        >
          {generating ? "🤖 Agent is writing your rule…" : "Generate Rule"}
        </button>
      </div>

      {/* SECTION B — Generated Code Preview */}
      {generated && (
        <div className="space-y-3 border-t border-gray-100 pt-5">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-gray-600">
              Rule:{" "}
              <span className="font-mono text-indigo-700">{generated.func_name}</span>
            </p>
          </div>

          <pre className="overflow-auto max-h-52 rounded-lg bg-gray-900 p-4 text-xs text-green-300 font-mono leading-relaxed">
            {generated.generated_code}
          </pre>

          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60 transition-colors"
            >
              {saving ? "Adding…" : "✅ Add to Engine"}
            </button>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex-1 rounded-lg bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-300 disabled:opacity-60 transition-colors"
            >
              🔄 Regenerate
            </button>
          </div>
        </div>
      )}

      {/* SECTION C — Active Rules */}
      <div className="border-t border-gray-100 pt-5 space-y-3">
        <p className="text-sm font-bold text-gray-700">
          Active Custom Rules ({activeRules.length})
        </p>

        {activeRules.length === 0 && (
          <p className="text-xs text-gray-400">
            No custom rules yet. Generate and add one above.
          </p>
        )}

        {activeRules.map((rule) => (
          <div
            key={rule.func_name}
            className="flex items-start justify-between rounded-lg border border-purple-100 bg-purple-50 px-4 py-3"
          >
            <div className="space-y-0.5">
              <p className="text-sm text-gray-800">{rule.rule_description}</p>
              <p className="font-mono text-xs text-gray-400">{rule.func_name}</p>
            </div>
            <div className="flex items-center gap-2 ml-4 shrink-0">
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-bold text-green-700">
                ACTIVE
              </span>
              <button
                onClick={() => handleDelete(rule.func_name)}
                className="rounded bg-red-100 px-2 py-1 text-xs font-semibold text-red-700 hover:bg-red-200 transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        ))}

        {activeRules.length > 0 && (
          <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-xs text-green-800">
            These {activeRules.length} custom rule{activeRules.length > 1 ? "s are" : " is"} now
            running on every verification — including the 3 mock files above and the Live
            Tester below.
          </div>
        )}
      </div>
    </div>
  );
}
