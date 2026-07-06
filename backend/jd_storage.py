"""JSON-based storage for JD Creator drafts."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from .jd_config import JD_DATA_DIR


def ensure_jd_data_dir():
    """Ensure the JD data directory exists."""
    Path(JD_DATA_DIR).mkdir(parents=True, exist_ok=True)


def get_jd_path(jd_id: str) -> str:
    """Get the file path for a JD draft."""
    return os.path.join(JD_DATA_DIR, f"{jd_id}.json")


def _empty_hierarchy_box():
    return {"title": "", "band": ""}


_COUNTER_FILE_NAME = "_jd_number_counter.txt"


def _next_jd_number(lob: str) -> str:
    """Generate the next human-readable tracking id, e.g. JD-AMC-00001.

    Backed by a small counter file so ids stay unique and monotonically
    increasing even if drafts are later deleted.
    """
    ensure_jd_data_dir()
    counter_path = os.path.join(JD_DATA_DIR, _COUNTER_FILE_NAME)

    last = 0
    if os.path.exists(counter_path):
        with open(counter_path, 'r') as f:
            last = json.load(f).get("last", 0)

    next_value = last + 1
    with open(counter_path, 'w') as f:
        json.dump({"last": next_value}, f)

    return f"JD-{lob}-{next_value:05d}"


def _new_draft_shape(jd_id: str, lob: str, jd_number: str = None) -> Dict[str, Any]:
    """Build the full empty-shape JD draft document."""
    now = datetime.utcnow().isoformat()
    return {
        "id": jd_id,
        "jd_number": jd_number,
        "status": "draft",
        "lob": lob,
        "created_at": now,
        "updated_at": now,
        "linked_conversation_id": None,
        "basics": {
            "lob": lob,
            "business": "",
            "unit": "",
            "location": "",
            "poornata_position_number": "",
            "reports_to_position_number": "",
            "poornata_position_title": "",
            "reports_to_position_title": "",
            "function": "",
            "reports_to_function": "",
            "department": "",
            "reports_to_department": "",
            "designation_employee": "",
            "designation_manager": "",
            "org_hierarchy_level": "",
            "date_of_writing": now[:10],
            "org_hierarchy_visual": {
                "levels_up_2": [_empty_hierarchy_box()],
                "levels_up_1": [_empty_hierarchy_box()],
                "this_role": _empty_hierarchy_box(),
                "peers": [_empty_hierarchy_box()],
                "levels_down_1": [_empty_hierarchy_box()],
                "levels_down_2": [_empty_hierarchy_box()],
            },
        },
        "purpose": {"text": ""},
        "dimensions": {
            "rows": [
                {"id": 1, "dimension_name": "", "fy_previous": "", "fy_current": "", "remarks": ""},
                {"id": 2, "dimension_name": "", "fy_previous": "", "fy_current": "", "remarks": ""},
                {"id": 3, "dimension_name": "", "fy_previous": "", "fy_current": "", "remarks": ""},
            ]
        },
        "context": {
            "organization_context": "",
            "job_context": "",
            "key_challenges": ["", "", ""],
        },
        "accountabilities": {
            "rows": [
                {"id": i, "accountability": "", "supporting_actions": ""}
                for i in range(1, 6)
            ]
        },
        "reports_and_relationships": {
            "direct_reports": [{"id": 1, "report_title": "", "job_purpose": ""}],
            "internal_relationships": [
                {"id": i, "stakeholder": "", "frequency": "", "nature_of_interaction": ""}
                for i in range(1, 4)
            ],
            "external_relationships": [
                {"id": i, "stakeholder": "", "frequency": "", "nature_of_interaction": ""}
                for i in range(1, 3)
            ],
        },
        "hay_factors": {
            "know_how": {
                "min_qualification": [],
                "years_of_experience": "",
                "technical_expertise_areas": [],
                "certifications": "",
                "industry_experience": "",
            },
            "decision_making": {
                "independent_decisions": "",
                "decisions_needing_approval": "",
                "financial_approval_limit": "",
                "advisory_vs_final_authority": "",
            },
            "problem_solving": {
                "thinking_environment": "",
                "types_of_problems": "",
                "degree_of_ambiguity": "",
            },
        },
        "sign_off": {
            "prepared_by_name": "",
            "prepared_by_email": "",
            "confirmed": False,
            "confirmed_at": None,
            "user_agent": None,
        },
        "generated_result": None,
    }


def create_jd_draft(jd_id: str, lob: str) -> Dict[str, Any]:
    """Create a new JD draft and persist it."""
    ensure_jd_data_dir()

    jd_number = _next_jd_number(lob)
    draft = _new_draft_shape(jd_id, lob, jd_number)

    path = get_jd_path(jd_id)
    with open(path, 'w') as f:
        json.dump(draft, f, indent=2)

    return draft


def delete_jd_draft(jd_id: str) -> bool:
    """Delete a JD draft from storage. Returns False if it didn't exist."""
    path = get_jd_path(jd_id)
    if not os.path.exists(path):
        return False

    os.remove(path)
    return True


def default_step_value(step_key: str, lob: str) -> Any:
    """The blank/default value for a single wizard step, used to clear a step in place."""
    fresh = _new_draft_shape("_template", lob)
    return fresh.get(step_key)


def get_jd_draft(jd_id: str) -> Optional[Dict[str, Any]]:
    """Load a JD draft from storage."""
    path = get_jd_path(jd_id)

    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        return json.load(f)


def save_jd_draft(draft: Dict[str, Any]):
    """Save a JD draft to storage, bumping updated_at."""
    ensure_jd_data_dir()

    draft["updated_at"] = datetime.utcnow().isoformat()

    path = get_jd_path(draft['id'])
    with open(path, 'w') as f:
        json.dump(draft, f, indent=2)


def _calculate_completion_percent(draft: Dict[str, Any]) -> int:
    """Rough percent-complete across the 8 wizard steps, mirroring generate-readiness checks."""
    total_steps = 8
    complete = 0

    basics = draft.get("basics", {})
    required_basics = [
        "business", "unit", "location", "poornata_position_number",
        "reports_to_position_number", "poornata_position_title",
        "reports_to_position_title", "function", "reports_to_function",
        "department", "reports_to_department", "designation_employee",
        "designation_manager", "org_hierarchy_level",
    ]
    if all(str(basics.get(f, "")).strip() for f in required_basics):
        complete += 1

    if len(draft.get("purpose", {}).get("text", "")) >= 100:
        complete += 1

    complete += 1  # dimensions is negotiable, always counts as done

    context = draft.get("context", {})
    challenges = [c for c in context.get("key_challenges", []) if str(c).strip()]
    if len(context.get("job_context", "")) >= 200 and len(challenges) >= 3:
        complete += 1

    accountability_rows = [
        r for r in draft.get("accountabilities", {}).get("rows", [])
        if str(r.get("accountability", "")).strip() and str(r.get("supporting_actions", "")).strip()
    ]
    if len(accountability_rows) >= 5:
        complete += 1

    reports = draft.get("reports_and_relationships", {})
    internal = [r for r in reports.get("internal_relationships", []) if str(r.get("stakeholder", "")).strip()]
    external = [r for r in reports.get("external_relationships", []) if str(r.get("stakeholder", "")).strip()]
    if len(internal) >= 3 and len(external) >= 2:
        complete += 1

    hay = draft.get("hay_factors", {})
    know_how = hay.get("know_how", {})
    decision_making = hay.get("decision_making", {})
    hay_ok = (
        bool(know_how.get("min_qualification"))
        and str(know_how.get("years_of_experience", "")).strip() != ""
        and bool(know_how.get("technical_expertise_areas"))
        and str(know_how.get("industry_experience", "")).strip() != ""
        and all(
            str(decision_making.get(f, "")).strip()
            for f in ["independent_decisions", "decisions_needing_approval", "financial_approval_limit", "advisory_vs_final_authority"]
        )
    )
    if hay_ok:
        complete += 1

    sign_off = draft.get("sign_off", {})
    if (
        str(sign_off.get("prepared_by_name", "")).strip()
        and str(sign_off.get("prepared_by_email", "")).strip()
        and sign_off.get("confirmed")
    ):
        complete += 1

    return round((complete / total_steps) * 100)


def list_jd_drafts() -> List[Dict[str, Any]]:
    """List all JD drafts (metadata only)."""
    ensure_jd_data_dir()

    drafts = []
    for filename in os.listdir(JD_DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(JD_DATA_DIR, filename)
            with open(path, 'r') as f:
                data = json.load(f)
                drafts.append({
                    "id": data["id"],
                    "jd_number": data.get("jd_number"),
                    "lob": data.get("lob"),
                    "business": data.get("basics", {}).get("business", ""),
                    "status": data.get("status", "draft"),
                    "title": data.get("basics", {}).get("poornata_position_title") or "Untitled JD",
                    "created_at": data["created_at"],
                    "updated_at": data.get("updated_at", data["created_at"]),
                    "linked_conversation_id": data.get("linked_conversation_id"),
                    "prepared_by_name": data.get("sign_off", {}).get("prepared_by_name", ""),
                    "completion_percent": 100 if data.get("status") == "generated" else _calculate_completion_percent(data),
                })

    drafts.sort(key=lambda x: x["updated_at"], reverse=True)

    return drafts


def update_jd_step(jd_id: str, step_key: str, step_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Merge new data into a specific step section of a draft and save."""
    draft = get_jd_draft(jd_id)
    if draft is None:
        return None

    draft[step_key] = step_data
    save_jd_draft(draft)

    return draft


def set_jd_status(jd_id: str, status: str, generated_result: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Transition a draft's status (e.g. draft -> generated)."""
    draft = get_jd_draft(jd_id)
    if draft is None:
        return None

    draft["status"] = status
    if generated_result is not None:
        draft["generated_result"] = generated_result
    save_jd_draft(draft)

    return draft


def link_conversation(jd_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
    """Link a JD draft to a council conversation id."""
    draft = get_jd_draft(jd_id)
    if draft is None:
        return None

    draft["linked_conversation_id"] = conversation_id
    save_jd_draft(draft)

    return draft
