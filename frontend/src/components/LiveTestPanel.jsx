import { useState } from "react";
import VerdictBanner from "./VerdictBanner";

const ROW_BG = { pass: "bg-green-50", soft_fail: "bg-yellow-50", hard_fail: "bg-red-50" };
const BADGE = { pass: "bg-green-100 text-green-800", soft_fail: "bg-yellow-100 text-yellow-800", hard_fail: "bg-red-100 text-red-800" };
const BADGE_LABEL = { pass: "Pass", soft_fail: "Soft Fail", hard_fail: "Hard Fail" };

const DEFAULT_FIELDS = {
  pan: { number: "ABCPK1234D", name: "P. Kumar", dob: "2004 arpil 6th", gender: "M", father_name: "R. Kumar" },
  aadhaar: { last4: "1234", name: "Prashant Kumar", dob: "2004/04/06", gender: "M", father_name: "Ramesh Kumar" },
  bureau: { name: "Prashant Kumar", dob: "2004-04-06", pan_linked: "ABCPK1234D", aadhaar_last4: "1234" },
};

const DEFAULT_THRESHOLDS = { pass: 85, soft: 55, leniency: true };

function InputField({ label, value, onChange, placeholder }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600">{label}</label>
      <input
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
      />
    </div>
  );
}

function previewResult(score, pass_t, soft_t) {
  if (score >= pass_t) return { label: "✅ PASS", cls: "text-green-600" };
  if (score >= soft_t) return { label: "⚠️ SOFT FAIL", cls: "text-yellow-600" };
  return { label: "🚫 HARD FAIL", cls: "text-red-600" };
}

const CATEGORIES = ["manual", "name_test", "dob_test", "gender_test", "pan_test", "judge_demo"];

export default function LiveTestPanel() {
  const [fields, setFields] = useState(DEFAULT_FIELDS);
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS);
  const [thresholdOpen, setThresholdOpen] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testCaseName, setTestCaseName] = useState("");
  const [testCategory, setTestCategory] = useState("manual");
  const [lastSaved, setLastSaved] = useState(null);

  function setField(section, key, value) {
    setFields((prev) => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
  }

  const isCustomThreshold =
    thresholds.pass !== DEFAULT_THRESHOLDS.pass ||
    thresholds.soft !== DEFAULT_THRESHOLDS.soft ||
    thresholds.leniency !== DEFAULT_THRESHOLDS.leniency;

  async function handleRun() {
    setLoading(true);
    setResult(null);
    setLastSaved(null);
    try {
      const sessionId = testCaseName ? `sess-${Date.now()}` : "";
      const res = await fetch("/api/verify-live", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...fields,
          pass_threshold: thresholds.pass,
          soft_threshold: thresholds.soft,
          initial_leniency: thresholds.leniency,
          test_case_name: testCaseName,
          test_category: testCategory,
          session_id: sessionId,
        }),
      });
      const data = await res.json();
      setResult(data);
      if (testCaseName) setLastSaved(testCaseName);
    } catch (err) {
      console.error("Live test failed:", err);
    } finally {
      setLoading(false);
    }
  }

  const dobCheck = result?.checks?.find((c) => c.check?.includes("Date of Birth"));
  const PREVIEW_SCORES = [90, 70, 40];

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-6 space-y-5">
      <div>
        <h2 className="text-base font-bold text-gray-800">🧪 Live Format Tester</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Type any name or date format — see how the agent handles it
        </p>
      </div>

      {/* Threshold controls */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <button
          onClick={() => setThresholdOpen((o) => !o)}
          className={`w-full flex items-center justify-between px-4 py-3 text-sm font-semibold transition-colors ${
            isCustomThreshold ? "bg-yellow-50 text-yellow-800" : "bg-gray-50 text-gray-700 hover:bg-gray-100"
          }`}
        >
          <span>⚙️ Fuzzy Matching Thresholds{isCustomThreshold ? " (custom)" : ""}</span>
          <span>{thresholdOpen ? "▲" : "▼"}</span>
        </button>

        {thresholdOpen && (
          <div className="px-5 py-4 space-y-4 border-t border-gray-200">
            {/* Pass threshold */}
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs font-semibold text-gray-700">
                  Pass Threshold (currently: {thresholds.pass}%)
                </label>
                <span className="text-xs text-gray-400">Score above this = PASS</span>
              </div>
              <input
                type="range" min={70} max={95} step={5}
                value={thresholds.pass}
                onChange={(e) => setThresholds((t) => ({ ...t, pass: Number(e.target.value) }))}
                className="w-full accent-green-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                <span>70%</span><span>95%</span>
              </div>
            </div>

            {/* Soft fail threshold */}
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs font-semibold text-gray-700">
                  Soft Fail Threshold (currently: {thresholds.soft}%)
                </label>
                <span className="text-xs text-gray-400">Between this and pass = SOFT FAIL</span>
              </div>
              <input
                type="range" min={30} max={70} step={5}
                value={thresholds.soft}
                onChange={(e) => setThresholds((t) => ({ ...t, soft: Number(e.target.value) }))}
                className="w-full accent-yellow-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                <span>30%</span><span>70%</span>
              </div>
            </div>

            {/* Initial name leniency toggle */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-700">Initial Name Leniency</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  When ON: "P. Kumar" vs "Prashant Kumar" gets extra leniency if last names match
                </p>
              </div>
              <button
                onClick={() => setThresholds((t) => ({ ...t, leniency: !t.leniency }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  thresholds.leniency ? "bg-indigo-600" : "bg-gray-300"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    thresholds.leniency ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>

            {/* Live preview */}
            <div className={`rounded-lg px-4 py-3 text-xs space-y-1 ${isCustomThreshold ? "bg-yellow-50 border border-yellow-200" : "bg-gray-50 border border-gray-100"}`}>
              <p className="font-semibold text-gray-700">
                With these thresholds {isCustomThreshold ? "(custom)" : "(default)"}:
              </p>
              {PREVIEW_SCORES.map((s) => {
                const r = previewResult(s, thresholds.pass, thresholds.soft);
                return (
                  <p key={s} className={`font-medium ${r.cls}`}>
                    Score {s}% → {r.label}
                  </p>
                );
              })}
              {isCustomThreshold && (
                <button
                  onClick={() => setThresholds(DEFAULT_THRESHOLDS)}
                  className="mt-1 text-indigo-600 underline text-xs"
                >
                  Reset to defaults
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* PAN + Aadhaar side by side */}
      <div className="grid grid-cols-2 gap-x-8 gap-y-4">
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-widest text-indigo-600">PAN Values</p>
          <InputField label="PAN Number"    value={fields.pan.number}      onChange={(e) => setField("pan", "number", e.target.value)}      placeholder="ABCPK1234D" />
          <InputField label="PAN Name"      value={fields.pan.name}        onChange={(e) => setField("pan", "name", e.target.value)}        placeholder="P. Kumar" />
          <InputField label="Date of Birth" value={fields.pan.dob}         onChange={(e) => setField("pan", "dob", e.target.value)}         placeholder="2004 arpil 6th" />
          <InputField label="Gender"        value={fields.pan.gender}      onChange={(e) => setField("pan", "gender", e.target.value)}      placeholder="M or F" />
          <InputField label="Father Name"   value={fields.pan.father_name} onChange={(e) => setField("pan", "father_name", e.target.value)} placeholder="R. Kumar" />
        </div>
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-widest text-teal-600">Aadhaar Values</p>
          <InputField label="Aadhaar Last 4"  value={fields.aadhaar.last4}       onChange={(e) => setField("aadhaar", "last4", e.target.value)}        placeholder="1234" />
          <InputField label="Aadhaar Name"    value={fields.aadhaar.name}        onChange={(e) => setField("aadhaar", "name", e.target.value)}         placeholder="Prashant Kumar" />
          <InputField label="Date of Birth"   value={fields.aadhaar.dob}         onChange={(e) => setField("aadhaar", "dob", e.target.value)}          placeholder="1990/04/06" />
          <InputField label="Gender"          value={fields.aadhaar.gender}      onChange={(e) => setField("aadhaar", "gender", e.target.value)}       placeholder="M or F" />
          <InputField label="Father Name"     value={fields.aadhaar.father_name} onChange={(e) => setField("aadhaar", "father_name", e.target.value)}  placeholder="Ramesh Kumar" />
        </div>
      </div>

      {/* Bureau */}
      <div className="space-y-3">
        <p className="text-xs font-bold uppercase tracking-widest text-orange-600">Bureau Values</p>
        <div className="grid grid-cols-4 gap-4">
          <InputField label="Bureau Name"          value={fields.bureau.name}          onChange={(e) => setField("bureau", "name", e.target.value)}          placeholder="Prashant Kumar" />
          <InputField label="Bureau DOB"           value={fields.bureau.dob}           onChange={(e) => setField("bureau", "dob", e.target.value)}           placeholder="1990-04-12" />
          <InputField label="Bureau PAN Linked"    value={fields.bureau.pan_linked}    onChange={(e) => setField("bureau", "pan_linked", e.target.value)}    placeholder="ABCPK1234D" />
          <InputField label="Bureau Aadhaar Last4" value={fields.bureau.aadhaar_last4} onChange={(e) => setField("bureau", "aadhaar_last4", e.target.value)} placeholder="1234" />
        </div>
      </div>

      {/* Test session metadata */}
      <div className="border border-dashed border-gray-300 rounded-xl p-4 space-y-3">
        <p className="text-xs font-bold uppercase tracking-widest text-purple-600">Save to History (optional)</p>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-gray-600">Test Case Name</label>
            <input
              type="text"
              value={testCaseName}
              onChange={(e) => setTestCaseName(e.target.value)}
              placeholder="e.g. P_Kumar_initial_name"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-gray-600">Category</label>
            <select
              value={testCategory}
              onChange={(e) => setTestCategory(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>
        {testCaseName && (
          <p className="text-xs text-purple-600">
            This run will be saved to Memory &gt; Test Sessions under "{testCategory}"
          </p>
        )}
      </div>

      <button
        onClick={handleRun}
        disabled={loading}
        className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
      >
        {loading ? "Running verification…" : "Run Live Verification"}
      </button>

      {lastSaved && (
        <div className="rounded-lg bg-purple-50 border border-purple-200 px-4 py-2 text-xs text-purple-700 font-medium">
          Saved to history as "{lastSaved}" — view in 💾 Memory & History tab
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Threshold note */}
          {result.thresholds_used && (
            <div className={`rounded-lg px-4 py-2 text-xs flex flex-wrap items-center gap-3 ${
              isCustomThreshold ? "bg-yellow-50 border border-yellow-200" : "bg-gray-50 border border-gray-100"
            }`}>
              <span className="font-semibold text-gray-700">⚙️ Thresholds used:</span>
              <span>Pass ≥{result.thresholds_used.pass_threshold}%</span>
              <span>Soft ≥{result.thresholds_used.soft_threshold}%</span>
              <span>Initial leniency: {result.thresholds_used.initial_leniency ? "ON" : "OFF"}</span>
              {isCustomThreshold && (
                <>
                  <span className="text-yellow-600 font-medium">⚠ Custom thresholds active</span>
                  <button onClick={() => setThresholds(DEFAULT_THRESHOLDS)} className="text-indigo-600 underline">
                    Reset to defaults
                  </button>
                </>
              )}
            </div>
          )}

          {dobCheck && (dobCheck.raw_input_a || dobCheck.raw_input_b) && (
            <div className="rounded-lg bg-gray-100 px-4 py-3 font-mono text-xs text-gray-700 space-y-1">
              <p className="font-sans text-xs font-semibold text-gray-500 mb-1">Date Normalization Preview</p>
              {dobCheck.raw_input_a && <p>{dobCheck.raw_input_a}</p>}
              {dobCheck.raw_input_b && <p>{dobCheck.raw_input_b}</p>}
            </div>
          )}

          <VerdictBanner verdict={result.verdict} />

          {result.confidence_score && (
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-gray-800">Identity Confidence Score</span>
                <span className={`font-bold text-base ${
                  result.confidence_score.color === "green" ? "text-green-600" :
                  result.confidence_score.color === "yellow" ? "text-yellow-600" : "text-red-600"
                }`}>
                  {result.confidence_score.score}%
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-700 ${
                    result.confidence_score.color === "green" ? "bg-green-500" :
                    result.confidence_score.color === "yellow" ? "bg-yellow-500" : "bg-red-500"
                  }`}
                  style={{ width: `${result.confidence_score.score}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{result.confidence_score.label}</p>
            </div>
          )}

          <div className="overflow-x-auto rounded-xl border border-gray-200">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-100 text-xs uppercase text-gray-600 tracking-wider">
                <tr>
                  <th className="px-4 py-2">Check</th>
                  <th className="px-4 py-2">Input A</th>
                  <th className="px-4 py-2">Input B</th>
                  <th className="px-4 py-2">Result</th>
                  <th className="px-4 py-2">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {result.checks.map((c, i) => (
                  <tr key={i} className={ROW_BG[c.result] ?? ""}>
                    <td className="px-4 py-2 font-medium text-gray-800 whitespace-nowrap">
                      {c.check}
                      {c.is_custom && (
                        <span className="ml-2 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-bold text-purple-700">CUSTOM</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-gray-700">{c.input_a ?? "—"}</td>
                    <td className="px-4 py-2 text-gray-700">{c.input_b ?? "—"}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE[c.result]}`}>
                        {BADGE_LABEL[c.result] ?? c.result}
                      </span>
                      {c.fuzzy_score !== undefined && (
                        <span className="ml-2 text-xs text-gray-400">({c.fuzzy_score}%)</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-gray-600 max-w-xs">{c.reason ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
