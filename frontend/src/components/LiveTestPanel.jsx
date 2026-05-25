import { useState } from "react";
import VerdictBanner from "./VerdictBanner";

const ROW_BG = { pass: "bg-green-50", soft_fail: "bg-yellow-50", hard_fail: "bg-red-50" };
const BADGE = { pass: "bg-green-100 text-green-800", soft_fail: "bg-yellow-100 text-yellow-800", hard_fail: "bg-red-100 text-red-800" };
const BADGE_LABEL = { pass: "Pass", soft_fail: "Soft Fail", hard_fail: "Hard Fail" };

const DEFAULT = {
  pan: {
    number: "ABCPK1234D",
    name: "P. Kumar",
    dob: "2004 arpil 6th",
    gender: "M",
    father_name: "R. Kumar",
  },
  aadhaar: {
    last4: "1234",
    name: "Prashant Kumar",
    dob: "2004/04/06",
    gender: "M",
    father_name: "Ramesh Kumar",
  },
  bureau: {
    name: "Prashant Kumar",
    dob: "2004-04-06",
    pan_linked: "ABCPK1234D",
    aadhaar_last4: "1234",
  },
};

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

export default function LiveTestPanel() {
  const [fields, setFields] = useState(DEFAULT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  function setField(section, key, value) {
    setFields((prev) => ({
      ...prev,
      [section]: { ...prev[section], [key]: value },
    }));
  }

  async function handleRun() {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("/api/verify-live", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fields),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error("Live test failed:", err);
    } finally {
      setLoading(false);
    }
  }

  const dobCheck = result?.checks?.find((c) => c.check === "DOB (PAN vs Aadhaar)");

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-6 space-y-5">
      {/* Header */}
      <div>
        <h2 className="text-base font-bold text-gray-800">🧪 Live Format Tester</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Type any name or date format — see how the agent handles it
        </p>
      </div>

      {/* PAN + Aadhaar side by side */}
      <div className="grid grid-cols-2 gap-x-8 gap-y-4">
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-widest text-indigo-600">PAN Values</p>
          <InputField label="PAN Number"     value={fields.pan.number}      onChange={(e) => setField("pan", "number", e.target.value)}      placeholder="ABCPK1234D" />
          <InputField label="PAN Name"       value={fields.pan.name}        onChange={(e) => setField("pan", "name", e.target.value)}        placeholder="P. Kumar" />
          <InputField label="Date of Birth"  value={fields.pan.dob}         onChange={(e) => setField("pan", "dob", e.target.value)}         placeholder="2004 arpil 6th" />
          <InputField label="Gender"         value={fields.pan.gender}      onChange={(e) => setField("pan", "gender", e.target.value)}      placeholder="M or F" />
          <InputField label="Father Name"    value={fields.pan.father_name} onChange={(e) => setField("pan", "father_name", e.target.value)} placeholder="R. Kumar" />
        </div>

        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-widest text-teal-600">Aadhaar Values</p>
          <InputField label="Aadhaar Last 4"  value={fields.aadhaar.last4}        onChange={(e) => setField("aadhaar", "last4", e.target.value)}        placeholder="1234" />
          <InputField label="Aadhaar Name"    value={fields.aadhaar.name}         onChange={(e) => setField("aadhaar", "name", e.target.value)}         placeholder="Prashant Kumar" />
          <InputField label="Date of Birth"   value={fields.aadhaar.dob}          onChange={(e) => setField("aadhaar", "dob", e.target.value)}          placeholder="1990/04/06" />
          <InputField label="Gender"          value={fields.aadhaar.gender}       onChange={(e) => setField("aadhaar", "gender", e.target.value)}       placeholder="M or F" />
          <InputField label="Father Name"     value={fields.aadhaar.father_name}  onChange={(e) => setField("aadhaar", "father_name", e.target.value)}  placeholder="Ramesh Kumar" />
        </div>
      </div>

      {/* Bureau — full width, 4 cols */}
      <div className="space-y-3">
        <p className="text-xs font-bold uppercase tracking-widest text-orange-600">Bureau Values</p>
        <div className="grid grid-cols-4 gap-4">
          <InputField label="Bureau Name"         value={fields.bureau.name}          onChange={(e) => setField("bureau", "name", e.target.value)}          placeholder="Prashant Kumar" />
          <InputField label="Bureau DOB"          value={fields.bureau.dob}           onChange={(e) => setField("bureau", "dob", e.target.value)}           placeholder="1990-04-12" />
          <InputField label="Bureau PAN Linked"   value={fields.bureau.pan_linked}    onChange={(e) => setField("bureau", "pan_linked", e.target.value)}    placeholder="ABCPK1234D" />
          <InputField label="Bureau Aadhaar Last4" value={fields.bureau.aadhaar_last4} onChange={(e) => setField("bureau", "aadhaar_last4", e.target.value)} placeholder="1234" />
        </div>
      </div>

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={loading}
        className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
      >
        {loading ? "Running verification…" : "Run Live Verification"}
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {dobCheck && (dobCheck.raw_input_a || dobCheck.raw_input_b) && (
            <div className="rounded-lg bg-gray-100 px-4 py-3 font-mono text-xs text-gray-700 space-y-1">
              <p className="font-sans text-xs font-semibold text-gray-500 mb-1">Date Normalization Preview</p>
              {dobCheck.raw_input_a && <p>{dobCheck.raw_input_a}</p>}
              {dobCheck.raw_input_b && <p>{dobCheck.raw_input_b}</p>}
            </div>
          )}

          <VerdictBanner verdict={result.verdict} />

          {/* Confidence Score Bar */}
          {result.confidence_score && (
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-gray-800">Identity Confidence Score</span>
                <span className={`font-bold text-base ${
                  result.confidence_score.color === "green" ? "text-green-600" :
                  result.confidence_score.color === "yellow" ? "text-yellow-600" :
                  "text-red-600"
                }`}>
                  {result.confidence_score.score}%
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-700 ${
                    result.confidence_score.color === "green" ? "bg-green-500" :
                    result.confidence_score.color === "yellow" ? "bg-yellow-500" :
                    "bg-red-500"
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
                        <span className="ml-2 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-bold text-purple-700">
                          CUSTOM
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-gray-700">{c.input_a ?? "—"}</td>
                    <td className="px-4 py-2 text-gray-700">{c.input_b ?? "—"}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE[c.result]}`}>
                        {BADGE_LABEL[c.result] ?? c.result}
                      </span>
                      {c.fuzzy_score !== undefined && (
                        <span className="ml-2 text-xs text-gray-400">({c.fuzzy_score})</span>
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
