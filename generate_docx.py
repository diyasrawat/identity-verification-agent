"""Generates SYSTEM_CONCEPTS_AND_FLOW.docx from the markdown content."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

doc = Document()

# ── Styles ────────────────────────────────────────────────────────────────────
styles = doc.styles

def set_heading(paragraph, level, text, color=None):
    paragraph.clear()
    run = paragraph.add_run(text)
    run.bold = True
    sizes = {1: 20, 2: 16, 3: 14, 4: 12}
    run.font.size = Pt(sizes.get(level, 12))
    if color:
        run.font.color.rgb = RGBColor(*color)
    paragraph.paragraph_format.space_before = Pt(12)
    paragraph.paragraph_format.space_after = Pt(4)

def add_heading(doc, text, level):
    colors = {
        1: (31, 73, 125),    # dark blue
        2: (54, 96, 146),    # medium blue
        3: (79, 129, 189),   # lighter blue
        4: (100, 100, 100),  # gray
    }
    p = doc.add_paragraph()
    set_heading(p, level, text, colors.get(level))
    return p

def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(6)
    run = p.runs[0] if p.runs else None
    if run:
        run.font.size = Pt(11)
    return p

def add_code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0, 120, 120)
    return p

def add_table_row(table, cells, bold_first=False):
    row = table.add_row()
    for i, cell_text in enumerate(cells):
        cell = row.cells[i]
        cell.text = cell_text
        if bold_first and i == 0:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.bold = True

def add_separator(doc):
    p = doc.add_paragraph()
    p.add_run("─" * 80)
    run = p.runs[0]
    run.font.color.rgb = RGBColor(200, 200, 200)
    run.font.size = Pt(8)

# ── Title Page ────────────────────────────────────────────────────────────────
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("SYSTEM CONCEPTS AND FLOW")
run.bold = True
run.font.size = Pt(24)
run.font.color.rgb = RGBColor(31, 73, 125)

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = subtitle.add_run("VerifyIQ: Identity Cross-Verification Agent")
run2.font.size = Pt(16)
run2.font.color.rgb = RGBColor(54, 96, 146)

tag = doc.add_paragraph()
tag.alignment = WD_ALIGN_PARAGRAPH.CENTER
run3 = tag.add_run("FlexiLoans Hackathon — Complete Technical Documentation")
run3.font.size = Pt(11)
run3.italic = True
run3.font.color.rgb = RGBColor(100, 100, 100)

doc.add_paragraph()
doc.add_page_break()

# ── SECTION 1 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 1 — SYSTEM OVERVIEW", 1)
add_separator(doc)

add_heading(doc, "What Does VerifyIQ Do?", 2)
add_body(doc, "VerifyIQ is an identity cross-verification platform built for Indian loan underwriting. "
              "When a person applies for a loan, they submit documents from three sources:")

tbl1 = doc.add_table(rows=1, cols=2)
tbl1.style = 'Light List Accent 1'
hdr = tbl1.rows[0].cells
hdr[0].text = "Document"
hdr[1].text = "Contents"
rows_data = [
    ("PAN Card", "Name, DOB, gender, father's name, 10-character PAN number (tax ID)"),
    ("Aadhaar", "Name, DOB, gender, father's name, 12-digit number (biometric national ID)"),
    ("Bureau Report", "Name, DOB, linked PAN, Aadhaar last 4 digits (credit bureau data)"),
]
for row in rows_data:
    add_table_row(tbl1, row, bold_first=True)
doc.add_paragraph()

add_body(doc, "All three should describe the same person. But in reality:")
for issue in [
    "Names spelled differently: \"Prashant\" on PAN, \"Prashanth\" on Aadhaar (South Indian variant)",
    "Dates in different formats: \"12/04/1990\" vs \"April 12th 1990\"",
    "Abbreviated names: \"P. Kumar\" on PAN, \"Prashant Kumar\" on Aadhaar",
    "Typos: \"2004 arpil 6th\" instead of \"2004 April 6\"",
    "Father's name prefixes: \"S/O Ramesh Kumar\" vs \"Ramesh Kumar\"",
    "Masked Aadhaar: \"XXXX-XXXX-5678\" in bureau records",
]:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(issue).font.size = Pt(11)

add_body(doc, "VerifyIQ automatically cross-verifies all these documents, handles all edge cases, "
              "gives a structured verdict, explains its reasoning, and gets smarter over time.")

add_heading(doc, "Why Was It Built?", 2)
add_body(doc, "Manual cross-verification is slow (15–30 min/file), inconsistent across underwriters, "
              "and expensive at scale. VerifyIQ provides a consistent, explainable, audit-able first "
              "pass in under 2 seconds.")

add_heading(doc, "Problem Solved", 2)
add_body(doc, "The core challenge: document data is messy and inconsistent — but real people need loans. "
              "A system that is too strict rejects legitimate applicants (Prashanth = Prashant IS the same person). "
              "Too loose and fraud gets through. VerifyIQ uses a hybrid approach:")

for approach in [
    "Deterministic rules for clear-cut cases (DOB exact mismatch → HARD BLOCK)",
    "Multi-layer fuzzy matching for name variants",
    "LLM reasoning for judgment calls that need context",
    "Fraud scoring to detect patterns across multiple signals",
]:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(approach).font.size = Pt(11)

doc.add_page_break()

# ── SECTION 2 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 2 — COMPLETE ARCHITECTURE", 1)
add_separator(doc)

add_heading(doc, "Backend Architecture", 2)
add_body(doc, "The backend is a FastAPI application (Python) running on port 8000, organized in 4 logical layers:")

add_code(doc, "ROUTE LAYER (main.py)\n"
              "  23 REST API endpoints · CORS middleware · Startup init_db()\n\n"
              "AGENT LAYER (agents/)\n"
              "  orchestrator · extraction · address · fraud · verdict\n"
              "  audit · observation · rule_proposer · self_healing\n\n"
              "LOGIC LAYER (checks.py + llm_functions.py + knowledge/)\n"
              "  Normalization · Fuzzy matching · LLM calls\n\n"
              "PERSISTENCE LAYER (persistence/)\n"
              "  memory_store.py (JSON) · audit_db.py (SQLite)")

add_heading(doc, "Frontend Architecture", 2)
add_body(doc, "React 18 SPA built with Vite 5, running on port 5173. "
              "App.jsx owns all shared state. Vite proxy routes /api/* → localhost:8000.")

add_heading(doc, "10 UI Tabs and Their Components", 3)
tbl2 = doc.add_table(rows=1, cols=3)
tbl2.style = 'Light List Accent 1'
hdr2 = tbl2.rows[0].cells
hdr2[0].text = "Tab"
hdr2[1].text = "Component"
hdr2[2].text = "Purpose"
tabs = [
    ("Verification", "OrchestrationPanel + VerdictBanner + LedgerTable", "Pipeline steps, verdict, checks"),
    ("Address", "AddressPanel", "Trust scores, graph results, conflicts"),
    ("Fraud", "FraudPanel", "Fraud score 0–100, signals, narrative"),
    ("Underwriter", "UnderwriterNotes", "PROCEED/REVIEW/REJECT + LLM notes"),
    ("Rules", "RuleEngine", "Create/manage custom rules"),
    ("Live Tester", "LiveTestPanel", "Configurable threshold testing"),
    ("Audit Trail", "AuditTrail", "Session audit log"),
    ("Self-Improving", "SelfImprovingAgent", "Proposals, pattern memory"),
    ("Self-Healing", "HealingPanel", "Error events and known patterns"),
    ("Memory & History", "MemoryDashboard", "SQLite + JSON persistence stats"),
]
for row in tabs:
    add_table_row(tbl2, row)
doc.add_paragraph()

add_heading(doc, "Persistence Layer", 2)
add_body(doc, "Two systems work together:")

add_heading(doc, "JSON Files (memory_store.py)", 3)
for f in [
    "pattern_memory.json — cumulative counters updated by ObservationAgent",
    "proposals.json — pending/approved/rejected improvement proposals",
    "healing_log.json — exception events from self-healing",
    "custom_rules.json — active custom rule function code",
]:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(f).font.size = Pt(11)

add_body(doc, "Key property: Atomic writes using .tmp file + os.replace(). No corruption on crash.")

add_heading(doc, "SQLite Database (audit_db.py) — 6 Tables", 3)
tbl3 = doc.add_table(rows=1, cols=2)
tbl3.style = 'Light List Accent 1'
tbl3.rows[0].cells[0].text = "Table"
tbl3.rows[0].cells[1].text = "Contents"
tables_data = [
    ("verifications", "One row per /orchestrate call — applicant, verdict, confidence, timestamp"),
    ("check_results", "One row per check per verification (FK: verification_id)"),
    ("pattern_observations", "Reserved — future pattern-level SQL queries"),
    ("proposals", "Mirror of proposals.json for SQL queries"),
    ("healing_events", "Each exception caught by heal_check()"),
    ("test_sessions", "Each /verify-live or /test/run-all-judge-cases run"),
]
for row in tables_data:
    add_table_row(tbl3, row, bold_first=True)
doc.add_paragraph()

doc.add_page_break()

# ── SECTION 3 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 3 — UI FLOW", 1)
add_separator(doc)

add_heading(doc, "State Flow: From Click to Render", 2)
add_code(doc, "User clicks 'FL-001 — Clean'\n"
              "  ↓\n"
              "handleSelectFile(fileConfig) in App.jsx\n"
              "  setSelectedFile('FL-001') · setResult(null) · setLoading(true)\n"
              "  ↓\n"
              "fetch('/mock_files/file1_clean.json') → setProfile(data)\n"
              "  ↓\n"
              "fetch('/api/orchestrate', {method: 'POST', body: profile_json})\n"
              "  ↓\n"
              "setResult(responseJson) · setLoading(false)\n"
              "  ↓\n"
              "React re-renders all 10 tabs with new data")

add_heading(doc, "Live Polling", 2)
add_body(doc, "Two setInterval calls run every 10 seconds from App.jsx:")
for item in [
    "GET /self-improve/stats → updates pendingProposals → drives green dot on Self-Improving tab",
    "GET /healing/log → updates healedErrors → drives red dot on Self-Healing tab",
]:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(item).font.size = Pt(11)

add_heading(doc, "Component State Management", 2)
add_body(doc, "Components that manage their own local state (independent of App.jsx):")

tbl4 = doc.add_table(rows=1, cols=2)
tbl4.style = 'Light List Accent 1'
tbl4.rows[0].cells[0].text = "Component"
tbl4.rows[0].cells[1].text = "State Managed"
comp_data = [
    ("LiveTestPanel", "14 input fields, threshold sliders, loading, result"),
    ("RuleEngine", "ruleText, generated code preview, activeRules list"),
    ("SelfImprovingAgent", "proposals, stats, loading states"),
    ("HealingPanel", "log data, loading"),
    ("MemoryDashboard", "stats, verifications, testSessions, patterns"),
    ("AuditTrail", "entries"),
]
for row in comp_data:
    add_table_row(tbl4, row, bold_first=True)
doc.add_paragraph()

doc.add_page_break()

# ── SECTION 4 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 4 — BACKEND FLOW", 1)
add_separator(doc)

add_heading(doc, "Request Lifecycle: POST /orchestrate", 2)
steps = [
    ("1. Request enters FastAPI", "CORS middleware allows. Route handler invoked. _load_custom_rules() reads JSON."),
    ("2. Orchestrator starts", "run_orchestrator(data, custom_rules) called. 7 pipeline steps begin."),
    ("3. ExtractionAgent", "normalize_name, normalize_date, uppercase fields. Returns cleaned_profile."),
    ("4. IdentityAgent (7 checks)", "Each check via heal_check(). Custom rules applied. identity_verdict computed."),
    ("5. Soft fail explanations", "For each soft_fail with no reason: explain_soft_fail() → 1-sentence LLM text."),
    ("6. AddressAgent", "graph_lookup → fuzzy fallback → trust scoring. LLM if hard conflicts."),
    ("7. LLM Reasoning", "agent_analyze() on all failures together → structured verdict JSON."),
    ("8. FraudAgent", "5 signals scored. LLM narrative if score ≥ 30."),
    ("9. VerdictAgent", "PROCEED/REVIEW/REJECT determined. LLM writes underwriter notes."),
    ("10. AuditAgent", "AUD-XXXX created in memory. Pipeline complete."),
    ("11. Post-pipeline (main.py)", "observe_verification() → JSON. save_verification() → SQLite. Response returned."),
]

tbl5 = doc.add_table(rows=1, cols=2)
tbl5.style = 'Light List Accent 1'
tbl5.rows[0].cells[0].text = "Step"
tbl5.rows[0].cells[1].text = "What Happens"
for row in steps:
    add_table_row(tbl5, row, bold_first=True)
doc.add_paragraph()

add_heading(doc, "Confidence Score Algorithm", 2)
add_code(doc, "weights = {pass: 100, soft_fail: 40, hard_fail: 0}\n"
              "critical = ['Date of Birth', 'PAN Format', 'Aadhaar Last']\n\n"
              "For each check:\n"
              "  score  = weights[result]\n"
              "  weight = 2 if check in critical else 1\n\n"
              "final = round((Σ score×weight) / (Σ 100×weight) × 100)\n\n"
              "≥ 85 → HIGH CONFIDENCE (green)\n"
              "≥ 55 → MEDIUM CONFIDENCE (yellow)\n"
              "< 55 → LOW CONFIDENCE (red)")

doc.add_page_break()

# ── SECTION 5 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 5 — AGENT SYSTEM", 1)
add_separator(doc)

agents_info = [
    ("ExtractionAgent", "agents/extraction_agent.py",
     "Data sanitization — makes all downstream agents work with clean, standardized data.",
     "Raw profile dict",
     "cleaned_profile + extraction_log (fields that changed)"),
    ("IdentityAgent (inline)", "agents/orchestrator.py",
     "Core cross-verification. Runs the 7 definitive checks.",
     "Cleaned profile + custom_rules list",
     "checks[], identity_verdict, confidence_score"),
    ("AddressAgent", "agents/address_agent.py",
     "Multi-source address reconciliation with knowledge graph.",
     "addresses dict, doc_dates dict",
     "address_result (verdict, canonical, conflicts, trust scores)"),
    ("LLM Reasoning", "llm_functions.agent_analyze()",
     "Holistic analysis of failures taken together — not in isolation.",
     "Failed checks summary, full profile",
     "agent_note, confidence (HIGH/MEDIUM/LOW), recommendation, reasoning"),
    ("FraudAgent", "agents/fraud_agent.py",
     "Pattern-based fraud risk scoring using 5 weighted signals.",
     "identity_result, address_result, profile",
     "fraud_score (0–100), risk_level, fraud_signals[], fraud_narrative"),
    ("VerdictAgent", "agents/verdict_agent.py",
     "Final decision with professional underwriting notes.",
     "All previous results",
     "final_verdict (PROCEED/REVIEW/REJECT), underwriter_notes"),
    ("AuditAgent", "agents/audit_agent.py",
     "Session audit logging (in-memory only).",
     "Full orchestration result",
     "audit_entry (AUD-XXXX)"),
    ("ObservationAgent", "agents/observation_agent.py",
     "Passive learning — watches every run, records patterns.",
     "profile, checks[], verdict",
     "Updated pattern_memory.json"),
    ("RuleProposerAgent", "agents/rule_proposer_agent.py",
     "Proposes system improvements when patterns exceed threshold.",
     "pattern_memory dict",
     "New proposals in proposals.json + SQLite"),
    ("SelfHealingAgent", "agents/self_healing_agent.py",
     "Exception handling wrapper. heal_check() wraps every check call.",
     "check_name, check_func, profile, *args",
     "Safe soft_fail result or normal check result"),
]

for agent_name, file_path, role, inputs, outputs in agents_info:
    add_heading(doc, agent_name, 3)
    p = doc.add_paragraph()
    p.add_run("File: ").bold = True
    p.add_run(file_path)
    add_body(doc, role)
    p2 = doc.add_paragraph()
    p2.add_run("Inputs: ").bold = True
    p2.add_run(inputs)
    p3 = doc.add_paragraph()
    p3.add_run("Outputs: ").bold = True
    p3.add_run(outputs)

doc.add_page_break()

# ── SECTION 6 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 6 — FUZZY MATCHING CONCEPTS", 1)
add_separator(doc)

add_heading(doc, "The Challenge", 2)
add_body(doc, "Indian names have many legitimate variants that exact matching fails on:")
for variant in [
    "Regional transliteration: Prashant ↔ Prashanth (Karnataka suffix -th)",
    "Vowel variations: Kumar ↔ Kumaar, Raju ↔ Rajoo",
    "Common abbreviations: P. Kumar ↔ Prashant Kumar",
    "Religious name variants: Mohammed ↔ Mohammad ↔ Muhammed ↔ Muhamed",
    "Father name prefixes: 'S/O Ramesh Kumar' vs 'Ramesh Kumar'",
]:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(variant).font.size = Pt(11)

add_heading(doc, "The 6-Layer Approach", 2)
layers = [
    ("Layer 1: normalize_name()",
     "UPPERCASE → strip punctuation → collapse spaces\n'Prashant  Kumar.' → 'PRASHANT KUMAR'"),
    ("Layer 2: apply_transliteration()",
     "Token lookup in TRANSLITERATION_GRAPH\n'PRASHANTH'→'PRASHANT' · 'MOHAMMED'→'MOHAMMAD'"),
    ("Layer 3: is_initial_match()",
     "Detect abbreviated first names\n'P KUMAR' + 'PRASHANT KUMAR' → True (P is initial, surnames match)"),
    ("Layer 4: fuzz.token_sort_ratio()",
     "Computed on raw AND transliterated names\nbest_score = max(raw_score, trans_score)\ntoken_sort_ratio sorts tokens first → order-independent"),
    ("Layer 5: Threshold adjustment",
     "Default: pass=85, soft=55\ninitial_match: adj_pass-=10, adj_soft-=15\ntransliteration applied: adj_soft-=10"),
    ("Layer 6: Final verdict",
     "initial_match + surnames_match → soft_fail (LLM explains)\nbest_score ≥ adj_pass → pass\nbest_score ≥ adj_soft → soft_fail\nbelow both → hard_fail"),
]
for layer_name, desc in layers:
    add_heading(doc, layer_name, 3)
    add_code(doc, desc)

add_heading(doc, "Address Knowledge Graph", 2)
add_body(doc, "15+ major Indian roads pre-defined with aliases, cities, and pincodes. "
              "Resolves 'MG Road' = 'Mahatma Gandhi Road' before fuzzy matching runs. "
              "Catches genuine differences: 'MG Road Bangalore' ≠ 'Marine Drive Mumbai' (different cities).")

doc.add_page_break()

# ── SECTION 7 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 7 — SELF-IMPROVING SYSTEM", 1)
add_separator(doc)

add_heading(doc, "The Learning Loop", 2)
add_code(doc, "Run 1: DD/MM/YYYY seen → count = 1\n"
              "Run 2: DD/MM/YYYY seen → count = 2\n"
              "Run 3: DD/MM/YYYY seen → count = 3 ← THRESHOLD HIT\n\n"
              "→ RuleProposerAgent creates proposal:\n"
              "  'DATE_FORMAT_HANDLER: DD/MM/YYYY seen 3 times → add explicit handler'\n\n"
              "→ Human approves via Self-Improving tab\n"
              "→ LLM generates Python dict describing the code change\n"
              "→ Developer applies change manually")

add_heading(doc, "Proposal Types", 2)
tbl6 = doc.add_table(rows=1, cols=3)
tbl6.style = 'Light List Accent 1'
hdr6 = tbl6.rows[0].cells
hdr6[0].text = "Type"
hdr6[1].text = "Trigger"
hdr6[2].text = "Auto-Generate"
prop_types = [
    ("DATE_FORMAT_HANDLER", "Non-standard date format seen ≥3×", "Yes"),
    ("NAME_THRESHOLD_ADJUSTMENT", "INITIAL_FIRST_NAME pattern seen ≥3×", "Yes"),
    ("TYPO_CORRECTION_RULE", "Known typo seen in input ≥3×", "Yes (HIGH priority)"),
    ("SYSTEMATIC_HARD_FAIL", "Same check hard-failing ≥6×", "No — needs human judgment"),
]
for row in prop_types:
    add_table_row(tbl6, row)
doc.add_paragraph()

add_heading(doc, "Pattern Memory", 2)
add_body(doc, "Stored in pattern_memory.json, updated atomically after every /orchestrate call:")
add_code(doc, "date_formats:     {'YYYY-MM-DD': 20, 'DD/MM/YYYY': 4}\n"
              "name_patterns:    {'FULL_NAME': 18, 'INITIAL_FIRST_NAME': 4}\n"
              "soft_fail_patterns: {'INITIAL_FIRST_NAME': 4}\n"
              "hard_fail_patterns: {'Date of Birth (PAN vs Aadhaar)': 2}\n"
              "total_runs: 15\n"
              "observations: [last 50 observation dicts]")

doc.add_page_break()

# ── SECTION 8 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 8 — SELF-HEALING SYSTEM", 1)
add_separator(doc)

add_heading(doc, "How heal_check() Works", 2)
add_code(doc, "heal_check('PAN Format Validity', check_pan_format, profile, pan_number)\n\n"
              "  try:\n"
              "    return check_pan_format(pan_number)   # Normal path\n\n"
              "  except Exception as e:\n"
              "    sig = MD5(error_type + error_message[:50])[:8]\n"
              "    analysis = LLM.analyze(error, traceback, input_data)\n"
              "    # Returns: root_cause, error_category, proposed_fix,\n"
              "    #          severity, auto_fixable, fix_code\n"
              "    log_to_healing_log_json()\n"
              "    save_to_sqlite_healing_events()\n"
              "    return {'result': 'soft_fail', 'reason': '[Self-Healed] ...'}\n"
              "    # Pipeline CONTINUES — never crashes")

add_heading(doc, "Error Categories", 2)
for cat in ["FORMAT_ERROR — Unexpected data format", "NULL_VALUE — Missing required field",
            "TYPE_MISMATCH — Wrong data type", "ENCODING — Character encoding issue",
            "THRESHOLD — Logic threshold issue", "UNKNOWN — Unclassified error"]:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(cat).font.size = Pt(11)

add_heading(doc, "Error Signature System", 2)
add_body(doc, "Each unique error gets an 8-character MD5 fingerprint. "
              "Recurring errors increment a count. High counts indicate systematic data quality issues "
              "that the self-improving system would eventually surface as SYSTEMATIC_HARD_FAIL proposals.")

doc.add_page_break()

# ── SECTION 9 ─────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 9 — COMPLETE END-TO-END FLOW", 1)
add_separator(doc)

add_heading(doc, "Full Lifecycle: User Upload → UI Rendering → Learning Loop", 2)
e2e_steps = [
    ("User Action", "Clicks 'FL-001 — Clean' file button in the browser"),
    ("Browser", "Fetches mock file JSON, sends POST /api/orchestrate with profile data"),
    ("Vite Proxy", "Strips /api prefix, forwards to http://localhost:8000/orchestrate"),
    ("FastAPI", "CORS check, loads custom rules, calls run_orchestrator()"),
    ("ExtractionAgent", "Normalizes names, dates, fields → cleaned_profile"),
    ("IdentityAgent", "Runs 7 checks via heal_check(). Computes identity_verdict = CLEAN"),
    ("LLM Reasoning", "No failures → returns static 'All checks passed. PROCEED. HIGH'"),
    ("AddressAgent", "Graph confirms MG Road = Mahatma Gandhi Road → CONSISTENT"),
    ("FraudAgent", "No signals → fraud_score = 0, LOW RISK"),
    ("VerdictAgent", "PROCEED → LLM writes professional underwriter notes"),
    ("AuditAgent", "Creates AUD-0001 in memory"),
    ("Post-pipeline", "observe_verification() → pattern_memory.json updated"),
    ("Post-pipeline", "save_verification() → SQLite: 1 verification + 7 check rows"),
    ("Response", "Full JSON with all agent results returned to browser"),
    ("Browser", "setResult() triggers React re-render of all 10 tabs"),
    ("UI", "Verification tab: CLEAN banner, 100% confidence, 7 green rows"),
    ("UI", "Address tab: CONSISTENT, MG Road graph match, trust scores"),
    ("UI", "Memory tab: 1 new verification shown in history"),
    ("Learning Loop", "If patterns hit threshold: new proposals appear in Self-Improving tab"),
]

tbl7 = doc.add_table(rows=1, cols=2)
tbl7.style = 'Light List Accent 1'
tbl7.rows[0].cells[0].text = "Stage"
tbl7.rows[0].cells[1].text = "Detail"
for row in e2e_steps:
    add_table_row(tbl7, row, bold_first=True)
doc.add_paragraph()

doc.add_page_break()

# ── SECTION 10 ────────────────────────────────────────────────────────────────
add_heading(doc, "SECTION 10 — LEARNING NOTES", 1)
add_separator(doc)

notes = [
    ("Why Separate Agents?",
     "Single Responsibility Principle. ExtractionAgent knows nothing about fraud. FraudAgent doesn't run fuzzy matching. "
     "Each agent is independently testable, replaceable, and debuggable. A bug in AddressAgent doesn't affect IdentityAgent."),

    ("Why Fuzzy Matching Beats Exact Matching",
     "Exact matching fails because names have legitimate variations. Prashanth and Prashant are the same name — "
     "one is the South Indian spelling, one is North Indian. Rejecting this blocks legitimate applicants. "
     "The multi-layer approach handles all common Indian name variants."),

    ("Why Persistence Is Needed",
     "Without persistence: server restart = all learning lost, no audit trail, custom rules disappear. "
     "With persistence: system gets smarter over time, full regulatory audit trail, custom rules survive deployments."),

    ("Why the Address Knowledge Graph Improves Matching",
     "'MG Road' and 'Mahatma Gandhi Road' have ~30% string similarity. Without the graph, this looks like a fraud signal. "
     "The graph knows they are the same location, preventing false conflicts. "
     "It also catches genuine differences: MG Road Bangalore vs Marine Drive Mumbai (different cities → GRAPH_CONFIRMED_DIFFERENT)."),

    ("Why Orchestration Matters",
     "Without an orchestrator, you'd have one giant function with all logic mixed. The orchestrator makes the pipeline "
     "visible (pipeline_steps in response), allows each step to fail gracefully, makes it easy to add/remove steps, "
     "and separates 'what order' from 'what does each thing do'."),

    ("Why LLM Only on Failures",
     "Clean files never call the LLM for reasoning (except VerdictAgent which always calls for notes). "
     "This keeps cost near zero for the majority of verifications and only uses expensive AI when context is needed."),

    ("Why Confidence Score ≠ Verdict",
     "The verdict is binary in each direction (hard_fail → HARD BLOCK). The confidence score shows how certain we are "
     "within that verdict. Two CLEAN verdicts might have 100% vs 75% confidence. "
     "Critical checks weighted 2× because a DOB mismatch is far more serious than a father name soft fail."),

    ("Why Atomic Writes for JSON",
     "Writing directly to a file and crashing mid-write = corrupted JSON = server fails to start. "
     "The .tmp → os.replace() pattern is atomic: you either have the old complete file or the new complete file. "
     "Never a partial. Critical for production reliability."),
]

for title_text, body_text in notes:
    add_heading(doc, title_text, 2)
    add_body(doc, body_text)

# ── Save ──────────────────────────────────────────────────────────────────────
doc.save("SYSTEM_CONCEPTS_AND_FLOW.docx")
print("SYSTEM_CONCEPTS_AND_FLOW.docx created successfully")
