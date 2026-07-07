"""Excel template generation + parsing for bulk-filling a JD draft.

One workbook = one JD, one sheet per wizard step. Scalar fields are laid out
as Field/Value pairs; repeatable fields are small tables. Parsing scans for
label/header text rather than relying on fixed row numbers, so it tolerates
inserted/reordered rows in a human-edited spreadsheet.
"""

import io
from typing import Any, Dict, List, Optional, Tuple

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from . import jd_config
from . import jd_storage

SHEET_BASICS = "Basics"
SHEET_PURPOSE = "Purpose"
SHEET_DIMENSIONS = "Dimensions"
SHEET_CONTEXT = "Context"
SHEET_ACCOUNTABILITIES = "Accountabilities"
SHEET_REPORTS = "Reports & Relationships"
SHEET_HAY = "Hay Factors"
SHEET_SIGNOFF = "Sign-Off"

REQUIRED_SHEETS = [
    SHEET_BASICS, SHEET_PURPOSE, SHEET_DIMENSIONS, SHEET_CONTEXT,
    SHEET_ACCOUNTABILITIES, SHEET_REPORTS, SHEET_HAY, SHEET_SIGNOFF,
]

BASICS_FIELDS = [
    ("business", "Business"),
    ("unit", "Unit"),
    ("location", "Location"),
    ("poornata_position_number", "Poornata Position Number"),
    ("reports_to_position_number", "Reports To: Position Number"),
    ("poornata_position_title", "Poornata Position Title"),
    ("reports_to_position_title", "Reports To: Position Title"),
    ("function", "Function"),
    ("reports_to_function", "Reports To: Function"),
    ("department", "Department"),
    ("reports_to_department", "Reports To: Department"),
    ("designation_employee", "Designation of Employee"),
    ("designation_manager", "Designation of Manager"),
    ("org_hierarchy_level", "Organization Hierarchy Level"),
    ("date_of_writing", "Date of Writing (YYYY-MM-DD)"),
]

HIERARCHY_TABLE_HEADER = ["Hierarchy Level", "Role Title", "Band"]
HIERARCHY_LEVEL_LABELS = [
    ("levels_up_2", "2 Levels Up"),
    ("levels_up_1", "1 Level Up"),
    ("this_role", "This Role"),
    ("peers", "Parallel (Peer)"),
    ("levels_down_1", "1 Level Down"),
    ("levels_down_2", "2 Levels Down"),
]

PURPOSE_FIELDS = [
    ("text", f"Job Purpose ({jd_config.JOB_PURPOSE_MIN_CHARS}-{jd_config.JOB_PURPOSE_MAX_CHARS} characters)"),
]

DIMENSIONS_TABLE_HEADER = ["Dimension Name", "FY Previous", "FY Current", "Remarks"]

CONTEXT_FIELDS = [
    ("organization_context", "Organization Context"),
    ("job_context", f"Job Context (min {jd_config.JOB_CONTEXT_MIN_CHARS} characters)"),
]
CHALLENGES_TABLE_HEADER = ["Key Challenge"]

ACCOUNTABILITIES_TABLE_HEADER = ["Accountability", "Supporting Actions"]

DIRECT_REPORTS_MARKER = "Direct Reports"
DIRECT_REPORTS_TABLE_HEADER = ["Report Title", "Job Purpose"]
INTERNAL_RELATIONSHIPS_MARKER = "Internal Relationships"
EXTERNAL_RELATIONSHIPS_MARKER = "External Relationships"
RELATIONSHIP_TABLE_HEADER = ["Stakeholder", "Frequency", "Nature of Interaction"]

HAY_KNOW_HOW_FIELDS = [
    ("min_qualification", "Minimum Qualification (comma-separated)"),
    ("years_of_experience", "Years of Experience"),
    ("technical_expertise_areas", "Technical Expertise Areas (comma-separated)"),
    ("certifications", "Certifications (optional)"),
    ("industry_experience", "Industry Experience"),
]
HAY_DECISION_FIELDS = [
    ("independent_decisions", "Independent Decisions"),
    ("decisions_needing_approval", "Decisions Needing Approval"),
    ("financial_approval_limit", "Financial Approval Limit"),
    ("advisory_vs_final_authority", "Advisory vs Final Authority"),
]
HAY_PROBLEM_FIELDS = [
    ("thinking_environment", "Thinking Environment (optional)"),
    ("types_of_problems", "Types of Problems (optional)"),
    ("degree_of_ambiguity", "Degree of Ambiguity (optional)"),
]

SIGNOFF_FIELDS = [
    ("prepared_by_name", "Prepared By Name"),
    ("prepared_by_email", "Prepared By Email"),
]


# ---------- shared helpers ----------

def _cell_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _dropdown(ws: Worksheet, options: List[str], cell_range: str):
    if not options:
        return
    formula = '"' + ",".join(str(o) for o in options) + '"'
    dv = DataValidation(type="list", formula1=formula, allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(cell_range)


def _write_kv_block(ws: Worksheet, start_row: int, fields: List[Tuple[str, str]], values: Dict[str, Any]) -> int:
    ws.cell(row=start_row, column=1, value="Field")
    ws.cell(row=start_row, column=2, value="Value")
    row = start_row + 1
    for key, label in fields:
        ws.cell(row=row, column=1, value=label)
        value = values.get(key, "")
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        ws.cell(row=row, column=2, value=value)
        row += 1
    return row + 1  # next free row after a blank separator


def _find_row(ws: Worksheet, header_values: List[str], start_row: int = 1) -> Optional[int]:
    """Find a row whose first len(header_values) cells match header_values (case-insensitive)."""
    target = [h.strip().lower() for h in header_values]
    for r in range(start_row, ws.max_row + 2):
        vals = [_cell_str(ws.cell(row=r, column=c).value).lower() for c in range(1, len(header_values) + 1)]
        if vals == target:
            return r
    return None


def _read_kv_block(ws: Worksheet, fields: List[Tuple[str, str]]) -> Dict[str, str]:
    label_to_key = {label: key for key, label in fields}
    result: Dict[str, str] = {}
    for row in ws.iter_rows():
        if not row:
            continue
        label = _cell_str(row[0].value)
        if label in label_to_key and len(row) > 1:
            result[label_to_key[label]] = _cell_str(row[1].value)
    return result


def _write_table(ws: Worksheet, start_row: int, header: List[str], seed_rows: List[List[str]]) -> int:
    for c, h in enumerate(header, start=1):
        ws.cell(row=start_row, column=c, value=h)
    row = start_row + 1
    for seed in seed_rows:
        for c, v in enumerate(seed, start=1):
            ws.cell(row=row, column=c, value=v)
        row += 1
    return row + 1


def _read_table(ws: Worksheet, header: List[str], start_row: int = 1) -> List[List[str]]:
    header_row = _find_row(ws, header, start_row=start_row)
    if header_row is None:
        return []
    ncols = len(header)
    rows_out = []
    r = header_row + 1
    while r <= ws.max_row:
        cells = [_cell_str(ws.cell(row=r, column=c).value) for c in range(1, ncols + 1)]
        if not any(cells):
            break
        rows_out.append(cells)
        r += 1
    return rows_out


# ---------- template generation ----------

def generate_template(lob: str) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)

    # Basics
    ws = wb.create_sheet(SHEET_BASICS)
    next_row = _write_kv_block(ws, 1, BASICS_FIELDS, {})
    next_row += 1
    hierarchy_seed = [[label, "", ""] for _, label in HIERARCHY_LEVEL_LABELS]
    _write_table(ws, next_row, HIERARCHY_TABLE_HEADER, hierarchy_seed)
    business_options = jd_config.LOB_BUSINESS_OPTIONS.get(lob, [])
    business_row = 1 + 1 + [k for k, _ in BASICS_FIELDS].index("business")
    _dropdown(ws, business_options, f"B{business_row}")
    level_row = 1 + 1 + [k for k, _ in BASICS_FIELDS].index("org_hierarchy_level")
    _dropdown(ws, jd_config.HIERARCHY_LEVELS, f"B{level_row}")
    _dropdown(ws, jd_config.HIERARCHY_LEVELS, f"C{next_row + 1}:C{next_row + len(HIERARCHY_LEVEL_LABELS)}")
    ws.column_dimensions['A'].width = 34
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 20

    # Purpose
    ws = wb.create_sheet(SHEET_PURPOSE)
    _write_kv_block(ws, 1, PURPOSE_FIELDS, {})
    ws.column_dimensions['A'].width = 34
    ws.column_dimensions['B'].width = 60

    # Dimensions
    ws = wb.create_sheet(SHEET_DIMENSIONS)
    _write_table(ws, 1, DIMENSIONS_TABLE_HEADER, [["", "", "", ""] for _ in range(3)])
    for col in "ABCD":
        ws.column_dimensions[col].width = 22

    # Context
    ws = wb.create_sheet(SHEET_CONTEXT)
    org_context_default = jd_config.LOB_ORG_CONTEXT_TEMPLATES.get(lob, "")
    next_row = _write_kv_block(ws, 1, CONTEXT_FIELDS, {"organization_context": org_context_default})
    next_row += 1
    _write_table(ws, next_row, CHALLENGES_TABLE_HEADER, [[""] for _ in range(jd_config.MIN_CHALLENGES)])
    ws.column_dimensions['A'].width = 34
    ws.column_dimensions['B'].width = 60

    # Accountabilities
    ws = wb.create_sheet(SHEET_ACCOUNTABILITIES)
    _write_table(ws, 1, ACCOUNTABILITIES_TABLE_HEADER, [["", ""] for _ in range(jd_config.MIN_ACCOUNTABILITIES)])
    ws.column_dimensions['A'].width = 40
    ws.column_dimensions['B'].width = 50

    # Reports & Relationships
    ws = wb.create_sheet(SHEET_REPORTS)
    ws.cell(row=1, column=1, value=DIRECT_REPORTS_MARKER)
    next_row = _write_table(ws, 2, DIRECT_REPORTS_TABLE_HEADER, [["", ""]])
    next_row += 1
    ws.cell(row=next_row, column=1, value=INTERNAL_RELATIONSHIPS_MARKER)
    internal_header_row = next_row + 1
    next_row = _write_table(ws, internal_header_row, RELATIONSHIP_TABLE_HEADER,
                             [["", "", ""] for _ in range(jd_config.MIN_INTERNAL_RELATIONSHIPS)])
    _dropdown(ws, jd_config.RELATIONSHIP_FREQUENCIES,
              f"B{internal_header_row + 1}:B{internal_header_row + jd_config.MIN_INTERNAL_RELATIONSHIPS}")
    next_row += 1
    ws.cell(row=next_row, column=1, value=EXTERNAL_RELATIONSHIPS_MARKER)
    external_header_row = next_row + 1
    _write_table(ws, external_header_row, RELATIONSHIP_TABLE_HEADER,
                 [["", "", ""] for _ in range(jd_config.MIN_EXTERNAL_RELATIONSHIPS)])
    _dropdown(ws, jd_config.RELATIONSHIP_FREQUENCIES,
              f"B{external_header_row + 1}:B{external_header_row + jd_config.MIN_EXTERNAL_RELATIONSHIPS}")
    ws.column_dimensions['A'].width = 34
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['C'].width = 40

    # Hay Factors
    ws = wb.create_sheet(SHEET_HAY)
    next_row = _write_kv_block(ws, 1, HAY_KNOW_HOW_FIELDS, {})
    industry_row = 1 + 1 + [k for k, _ in HAY_KNOW_HOW_FIELDS].index("industry_experience")
    _dropdown(ws, jd_config.INDUSTRY_EXPERIENCE_OPTIONS, f"B{industry_row}")
    next_row = _write_kv_block(ws, next_row, HAY_DECISION_FIELDS, {})
    next_row = _write_kv_block(ws, next_row, HAY_PROBLEM_FIELDS, {})
    ambiguity_row = next_row - 1  # last field written is degree_of_ambiguity
    _dropdown(ws, jd_config.AMBIGUITY_LEVELS, f"B{ambiguity_row}")
    ws.column_dimensions['A'].width = 38
    ws.column_dimensions['B'].width = 60

    # Sign-Off
    ws = wb.create_sheet(SHEET_SIGNOFF)
    _write_kv_block(ws, 1, SIGNOFF_FIELDS, {})
    ws.column_dimensions['A'].width = 24
    ws.column_dimensions['B'].width = 40

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ---------- upload parsing ----------

def parse_uploaded_workbook(file_bytes: bytes, lob: str) -> Dict[str, Any]:
    """Parse an uploaded workbook into {step_key: step_data} matching jd_storage's draft shape."""
    try:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as e:
        raise ValueError(f"Could not read the uploaded file as an Excel workbook: {e}")

    missing = [s for s in REQUIRED_SHEETS if s not in wb.sheetnames]
    if missing:
        raise ValueError(f"Uploaded file is missing expected sheet(s): {', '.join(missing)}")

    steps: Dict[str, Any] = {}

    # Basics
    ws = wb[SHEET_BASICS]
    basics = jd_storage.default_step_value("basics", lob)
    kv = _read_kv_block(ws, BASICS_FIELDS)
    for key, value in kv.items():
        if value:
            basics[key] = value
    boxes_by_key = {key: [] for key, _ in HIERARCHY_LEVEL_LABELS}
    label_to_key = {label: key for key, label in HIERARCHY_LEVEL_LABELS}
    for row in _read_table(ws, HIERARCHY_TABLE_HEADER):
        level_label, title, band = (row + ["", "", ""])[:3]
        key = label_to_key.get(level_label)
        if key and (title or band):
            boxes_by_key[key].append({"title": title, "band": band})
    visual = basics.get("org_hierarchy_visual", {})
    for key, _ in HIERARCHY_LEVEL_LABELS:
        if key == "this_role":
            visual[key] = boxes_by_key[key][0] if boxes_by_key[key] else {"title": "", "band": ""}
        else:
            visual[key] = boxes_by_key[key] if boxes_by_key[key] else visual.get(key, [{"title": "", "band": ""}])
    basics["org_hierarchy_visual"] = visual
    basics["lob"] = lob
    steps["basics"] = basics

    # Purpose
    kv = _read_kv_block(wb[SHEET_PURPOSE], PURPOSE_FIELDS)
    steps["purpose"] = {"text": kv.get("text", "")}

    # Dimensions
    rows = _read_table(wb[SHEET_DIMENSIONS], DIMENSIONS_TABLE_HEADER)
    steps["dimensions"] = {
        "rows": [
            {"id": i + 1, "dimension_name": r[0], "fy_previous": r[1], "fy_current": r[2], "remarks": r[3]}
            for i, r in enumerate(rows)
        ]
    }

    # Context
    ws = wb[SHEET_CONTEXT]
    kv = _read_kv_block(ws, CONTEXT_FIELDS)
    challenge_rows = _read_table(ws, CHALLENGES_TABLE_HEADER)
    steps["context"] = {
        "organization_context": kv.get("organization_context", ""),
        "job_context": kv.get("job_context", ""),
        "key_challenges": [r[0] for r in challenge_rows if r[0]],
    }

    # Accountabilities
    rows = _read_table(wb[SHEET_ACCOUNTABILITIES], ACCOUNTABILITIES_TABLE_HEADER)
    steps["accountabilities"] = {
        "rows": [
            {"id": i + 1, "accountability": r[0], "supporting_actions": r[1]}
            for i, r in enumerate(rows)
        ]
    }

    # Reports & Relationships
    ws = wb[SHEET_REPORTS]
    direct_marker_row = _find_row(ws, [DIRECT_REPORTS_MARKER]) or 1
    direct_rows = _read_table(ws, DIRECT_REPORTS_TABLE_HEADER, start_row=direct_marker_row)
    internal_marker_row = _find_row(ws, [INTERNAL_RELATIONSHIPS_MARKER]) or 1
    internal_rows = _read_table(ws, RELATIONSHIP_TABLE_HEADER, start_row=internal_marker_row)
    external_marker_row = _find_row(ws, [EXTERNAL_RELATIONSHIPS_MARKER]) or 1
    external_rows = _read_table(ws, RELATIONSHIP_TABLE_HEADER, start_row=external_marker_row)
    steps["reports_and_relationships"] = {
        "direct_reports": [
            {"id": i + 1, "report_title": r[0], "job_purpose": r[1]} for i, r in enumerate(direct_rows)
        ] or [{"id": 1, "report_title": "", "job_purpose": ""}],
        "internal_relationships": [
            {"id": i + 1, "stakeholder": r[0], "frequency": r[1], "nature_of_interaction": r[2]}
            for i, r in enumerate(internal_rows)
        ],
        "external_relationships": [
            {"id": i + 1, "stakeholder": r[0], "frequency": r[1], "nature_of_interaction": r[2]}
            for i, r in enumerate(external_rows)
        ],
    }

    # Hay Factors
    ws = wb[SHEET_HAY]
    know_how_kv = _read_kv_block(ws, HAY_KNOW_HOW_FIELDS)
    decision_kv = _read_kv_block(ws, HAY_DECISION_FIELDS)
    problem_kv = _read_kv_block(ws, HAY_PROBLEM_FIELDS)

    def _split_list(value: str) -> List[str]:
        return [v.strip() for v in value.split(",") if v.strip()]

    steps["hay_factors"] = {
        "know_how": {
            "min_qualification": _split_list(know_how_kv.get("min_qualification", "")),
            "years_of_experience": know_how_kv.get("years_of_experience", ""),
            "technical_expertise_areas": _split_list(know_how_kv.get("technical_expertise_areas", "")),
            "certifications": know_how_kv.get("certifications", ""),
            "industry_experience": know_how_kv.get("industry_experience", ""),
        },
        "decision_making": {
            "independent_decisions": decision_kv.get("independent_decisions", ""),
            "decisions_needing_approval": decision_kv.get("decisions_needing_approval", ""),
            "financial_approval_limit": decision_kv.get("financial_approval_limit", ""),
            "advisory_vs_final_authority": decision_kv.get("advisory_vs_final_authority", ""),
        },
        "problem_solving": {
            "thinking_environment": problem_kv.get("thinking_environment", ""),
            "types_of_problems": problem_kv.get("types_of_problems", ""),
            "degree_of_ambiguity": problem_kv.get("degree_of_ambiguity", ""),
        },
    }

    # Sign-Off
    kv = _read_kv_block(wb[SHEET_SIGNOFF], SIGNOFF_FIELDS)
    signoff = jd_storage.default_step_value("sign_off", lob)
    signoff["prepared_by_name"] = kv.get("prepared_by_name", "")
    signoff["prepared_by_email"] = kv.get("prepared_by_email", "")
    steps["sign_off"] = signoff

    return steps


# ---------- sample (fully filled) template generation ----------

SAMPLE_TEMPLATE_DATA = {
    "AMC": dict(
        business="ABSLAMC", unit="Fund Operations", location="Mumbai",
        title="AVP - Fund Accounting", function="Investments", department="Equity",
        reports_to_function="Finance", reports_to_department="Treasury",
        industry="Asset Management",
    ),
    "NBFC": dict(
        business="ABHFL", unit="Retail Lending", location="Mumbai",
        title="Manager - Credit Underwriting", function="Credit", department="Retail Credit",
        reports_to_function="Risk", reports_to_department="Credit Risk",
        industry="NBFC / Lending",
    ),
}


def generate_sample_template(lob: str) -> bytes:
    """Build a fully-filled example workbook for a LOB, satisfying every generate-time
    validation rule except the manual sign-off confirmation checkbox (kept manual by design)."""
    sample = SAMPLE_TEMPLATE_DATA[lob]
    business, unit, location, title, function = sample["business"], sample["unit"], sample["location"], sample["title"], sample["function"]
    department, reports_to_function, reports_to_department, industry = (
        sample["department"], sample["reports_to_function"], sample["reports_to_department"], sample["industry"]
    )

    wb = load_workbook(io.BytesIO(generate_template(lob)))

    # Basics
    ws = wb[SHEET_BASICS]
    kv = {
        "Business": business, "Unit": unit, "Location": location,
        "Poornata Position Number": "PPN-10001", "Reports To: Position Number": "PPN-10000",
        "Poornata Position Title": title, "Reports To: Position Title": f"Head of {function}",
        "Function": function, "Reports To: Function": reports_to_function,
        "Department": department, "Reports To: Department": reports_to_department,
        "Designation of Employee": title, "Designation of Manager": f"Head of {function}",
        "Organization Hierarchy Level": "JB 4",
    }
    hierarchy_kv = {
        "2 Levels Up": (f"CXO - {function}", "JB 7"),
        "1 Level Up": (f"Head of {function}", "JB 5"),
        "This Role": (title, "JB 4"),
        "Parallel (Peer)": (f"AVP - {function} Peer", "JB 4"),
        "1 Level Down": ("Manager - Team Lead", "JB 3"),
        "2 Levels Down": ("Associate", "JB 2"),
    }
    for row in ws.iter_rows():
        label = row[0].value
        if label in kv:
            row[1].value = kv[label]
        if label in hierarchy_kv:
            row[1].value, row[2].value = hierarchy_kv[label]

    # Purpose
    for row in wb[SHEET_PURPOSE].iter_rows():
        if row[0].value and "Job Purpose" in str(row[0].value):
            row[1].value = (
                f"Lead and manage the {unit} function within {business}, ensuring operational "
                f"excellence, regulatory compliance, and stakeholder satisfaction across all "
                f"day-to-day activities. Drive process improvements and mentor the team."
            )

    # Dimensions
    ws = wb[SHEET_DIMENSIONS]
    sample_dims = [
        ("AUM Managed", "3200 Cr", "3800 Cr", "YoY growth"),
        ("Team Size", "8", "10", "Includes 2 new hires"),
        ("Budget Owned", "2 Cr", "2.5 Cr", "Opex budget"),
    ]
    for r, (name, prev, cur, remarks) in zip(ws.iter_rows(min_row=2), sample_dims):
        r[0].value, r[1].value, r[2].value, r[3].value = name, prev, cur, remarks

    # Context
    ws = wb[SHEET_CONTEXT]
    for row in ws.iter_rows():
        if row[0].value == CONTEXT_FIELDS[1][1]:
            row[1].value = (
                f"This role operates within a fast-paced {business} environment, working closely "
                f"with cross-functional teams including operations, compliance, and technology. "
                f"The incumbent must navigate evolving regulatory requirements while driving "
                f"efficiency and supporting business growth targets across the {unit} function."
            )
    challenges_header = _find_row(ws, CHALLENGES_TABLE_HEADER)
    challenges = ["Regulatory change management", "Cross-functional coordination", "Talent retention in a competitive market"]
    for i, c in enumerate(challenges):
        ws.cell(row=challenges_header + 1 + i, column=1, value=c)

    # Accountabilities
    ws = wb[SHEET_ACCOUNTABILITIES]
    sample_acc = [
        ("Operational oversight", "Monitor daily operations and resolve escalations"),
        ("Regulatory compliance", "Ensure adherence to SEBI/RBI guidelines"),
        ("Team leadership", "Mentor and develop direct reports"),
        ("Stakeholder management", "Liaise with internal and external stakeholders"),
        ("Process improvement", "Identify and implement efficiency initiatives"),
    ]
    for r, (a, s) in zip(ws.iter_rows(min_row=2), sample_acc):
        r[0].value, r[1].value = a, s

    # Reports & Relationships
    ws = wb[SHEET_REPORTS]
    direct_marker = _find_row(ws, [DIRECT_REPORTS_MARKER])
    direct_header = _find_row(ws, DIRECT_REPORTS_TABLE_HEADER, start_row=direct_marker)
    ws.cell(row=direct_header + 1, column=1, value="Team Lead")
    ws.cell(row=direct_header + 1, column=2, value="Own day-to-day execution")

    internal_marker = _find_row(ws, [INTERNAL_RELATIONSHIPS_MARKER])
    internal_header = _find_row(ws, RELATIONSHIP_TABLE_HEADER, start_row=internal_marker)
    internal_data = [
        ("Compliance Team", "Weekly", "Regulatory alignment"),
        ("Finance Team", "Monthly", "Budget reviews"),
        ("Technology Team", "Need Basis", "System issues"),
    ]
    for i, (stake, freq, nature) in enumerate(internal_data):
        r = internal_header + 1 + i
        ws.cell(row=r, column=1, value=stake)
        ws.cell(row=r, column=2, value=freq)
        ws.cell(row=r, column=3, value=nature)

    external_marker = _find_row(ws, [EXTERNAL_RELATIONSHIPS_MARKER])
    external_header = _find_row(ws, RELATIONSHIP_TABLE_HEADER, start_row=external_marker)
    external_data = [
        ("Regulators (SEBI/RBI)", "Quarterly", "Compliance reporting"),
        ("External Auditors", "Quarterly", "Audit support"),
    ]
    for i, (stake, freq, nature) in enumerate(external_data):
        r = external_header + 1 + i
        ws.cell(row=r, column=1, value=stake)
        ws.cell(row=r, column=2, value=freq)
        ws.cell(row=r, column=3, value=nature)

    # Hay Factors
    ws = wb[SHEET_HAY]
    hay_kv = {
        "Minimum Qualification (comma-separated)": "MBA, CFA",
        "Years of Experience": "10-15 years",
        "Technical Expertise Areas (comma-separated)": f"{function}, Risk Management, Reporting",
        "Certifications (optional)": "CFA Level 2",
        "Industry Experience": industry,
        "Independent Decisions": "Approve expense budgets up to Rs 10L, hire within approved headcount",
        "Decisions Needing Approval": "Capital expenditure above Rs 25L requires CXO approval",
        "Financial Approval Limit": "Rs 10L (independently)",
        "Advisory vs Final Authority": "Advisory on strategy, Final on team operations",
        "Thinking Environment (optional)": "Moderately structured with periodic ambiguity",
        "Types of Problems (optional)": "Operational bottlenecks, compliance edge cases",
        "Degree of Ambiguity (optional)": "Moderately Structured",
    }
    for row in ws.iter_rows():
        if row[0].value in hay_kv:
            row[1].value = hay_kv[row[0].value]

    # Sign-Off
    for row in wb[SHEET_SIGNOFF].iter_rows():
        if row[0].value == "Prepared By Name":
            row[1].value = "Devanshi Tyagi"
        if row[0].value == "Prepared By Email":
            row[1].value = "devanshi27tyagi@gmail.com"

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
