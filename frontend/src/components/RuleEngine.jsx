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
  const [ruleText,    setRuleText]    = useState("");
  const [generating,  setGenerating]  = useState(false);
  const [generated,   setGenerated]   = useState(null);
  const [saving,      setSaving]      = useState(false);
  const [activeRules, setActiveRules] = useState([]);

  useEffect(() => { fetchRules(); }, []);

  async function fetchRules() {
    try {
      const res  = await fetch(`https://flexiloans-backend.onrender.com/api/rules/list`);
      const data = await res.json();
      setActiveRules(data.rules ?? []);
    } catch {}
  }

  async function handleGenerate() {
    if (!ruleText.trim()) return;
    setGenerating(true);
    setGenerated(null);
    try {
      const res  = await fetch(`https://flexiloans-backend.onrender.com/api/rules/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule_description: ruleText.trim() }),
      });
      setGenerated(await res.json());
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
      await fetch(`https://flexiloans-backend.onrender.com/api/rules/save`, {
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
      await fetch(`https://flexiloans-backend.onrender.com/api/rules/${func_name}`, { method: "DELETE" });
      await fetchRules();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 shadow-sm p-6 space-y-6">
      <div>
        <h2 className="text-base font-bold text-gray-100">Rule Engine</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Write a rule in plain English — the agent converts it to a live verification check
        </p>
      </div>

      <div className="space-y-3">
        <textarea
          rows={4}
          value={ruleText}
          onChange={(e) => setRuleText(e.target.value)}
          placeholder="e.g. PAN number last 4 characters before the final letter must be numeric digits only"
          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
        />

        <div className="flex flex-wrap gap-2">
          {EXAMPLE_RULES.map((ex) => (
            <button
              key={ex}
              onClick={() => setRuleText(ex)}
              className="rounded-full border border-indigo-800 bg-indigo-950 px-3 py-1 text-xs text-indigo-300 hover:bg-indigo-900 transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating || !ruleText.trim()}
          className="w-full rounded-lg bg-indigo-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-600 disabled:opacity-60 transition-colors"
        >
          {generating ? "Agent is writing your rule..." : "Generate Rule"}
        </button>
      </div>

      {generated && (
        <div className="space-y-3 border-t border-gray-800 pt-5">
          <p className="text-xs font-semibold text-gray-400">
            Rule: <span className="font-mono text-indigo-400">{generated.func_name}</span>
          </p>
          <pre className="overflow-auto max-h-52 rounded-lg bg-gray-950 border border-gray-800 p-4 text-xs text-green-400 font-mono leading-relaxed">
            {generated.generated_code}
          </pre>
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 rounded-lg bg-green-700 px-4 py-2 text-sm font-semibold text-white hover:bg-green-600 disabled:opacity-60 transition-colors"
            >
              {saving ? "Adding..." : "Add to Engine"}
            </button>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex-1 rounded-lg bg-gray-700 px-4 py-2 text-sm font-semibold text-gray-200 hover:bg-gray-600 disabled:opacity-60 transition-colors"
            >
              Regenerate
            </button>
          </div>
        </div>
      )}

      <div className="border-t border-gray-800 pt-5 space-y-3">
        <p className="text-sm font-bold text-gray-200">Active Custom Rules ({activeRules.length})</p>

        {activeRules.length === 0 && (
          <p className="text-xs text-gray-500">No custom rules yet. Generate and add one above.</p>
        )}

        {activeRules.map((rule) => (
          <div key={rule.func_name} className="flex items-start justify-between rounded-lg border border-violet-900 bg-violet-950 px-4 py-3">
            <div className="space-y-0.5">
              <p className="text-sm text-gray-200">{rule.rule_description}</p>
              <p className="font-mono text-xs text-gray-500">{rule.func_name}</p>
            </div>
            <div className="flex items-center gap-2 ml-4 shrink-0">
              <span className="rounded-full bg-green-900 px-2 py-0.5 text-xs font-bold text-green-400">ACTIVE</span>
              <button
                onClick={() => handleDelete(rule.func_name)}
                className="rounded bg-red-900 px-2 py-1 text-xs font-semibold text-red-300 hover:bg-red-800 transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        ))}

        {activeRules.length > 0 && (
          <div className="rounded-lg border border-green-900 bg-green-950 px-4 py-3 text-xs text-green-300">
            These {activeRules.length} custom rule{activeRules.length > 1 ? "s are" : " is"} now
            running on every verification.
          </div>
        )}
      </div>
    </div>
  );
}
