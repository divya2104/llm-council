"""Postgres-backed storage for JD Creator drafts."""

from datetime import datetime
from typing import List, Dict, Any, Optional

from . import jd_db


def _empty_hierarchy_box():
    return {"title": "", "band": ""}


async def _next_jd_number(lob: str) -> str:
    """Generate the next human-readable tracking id, e.g. JD-AMC-00001.

    Backed by an atomic upsert-and-increment on jd_number_counters, so ids
    stay unique even under concurrent draft creation.
    """
    pool = jd_db.get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO jd_number_counters (lob, last_value)
        VALUES ($1, 1)
        ON CONFLICT (lob) DO UPDATE SET last_value = jd_number_counters.last_value + 1
        RETURNING last_value
        """,
        lob,
    )
    return f"JD-{lob}-{row['last_value']:05d}"


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


def _draft_title(draft: Dict[str, Any]) -> str:
    return draft.get("basics", {}).get("poornata_position_title") or "Untitled JD"


async def create_jd_draft(jd_id: str, lob: str) -> Dict[str, Any]:
    """Create a new JD draft and persist it."""
    jd_number = await _next_jd_number(lob)
    draft = _new_draft_shape(jd_id, lob, jd_number)

    pool = jd_db.get_pool()
    created_at = datetime.fromisoformat(draft["created_at"])
    await pool.execute(
        """
        INSERT INTO jd_drafts
            (id, jd_number, lob, status, title, prepared_by_name,
             linked_conversation_id, created_at, updated_at, data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        jd_id, jd_number, lob, draft["status"], _draft_title(draft),
        draft["sign_off"]["prepared_by_name"], draft["linked_conversation_id"],
        created_at, created_at, draft,
    )

    return draft


async def delete_jd_draft(jd_id: str) -> bool:
    """Delete a JD draft from storage. Returns False if it didn't exist."""
    pool = jd_db.get_pool()
    result = await pool.execute("DELETE FROM jd_drafts WHERE id = $1", jd_id)
    return result != "DELETE 0"


def default_step_value(step_key: str, lob: str) -> Any:
    """The blank/default value for a single wizard step, used to clear a step in place."""
    fresh = _new_draft_shape("_template", lob)
    return fresh.get(step_key)


async def get_jd_draft(jd_id: str) -> Optional[Dict[str, Any]]:
    """Load a JD draft from storage."""
    pool = jd_db.get_pool()
    row = await pool.fetchrow("SELECT data FROM jd_drafts WHERE id = $1", jd_id)
    if row is None:
        return None
    return row["data"]


async def save_jd_draft(draft: Dict[str, Any]):
    """Save a JD draft to storage, bumping updated_at."""
    draft["updated_at"] = datetime.utcnow().isoformat()

    pool = jd_db.get_pool()
    await pool.execute(
        """
        UPDATE jd_drafts
        SET jd_number = $1, lob = $2, status = $3, title = $4, prepared_by_name = $5,
            linked_conversation_id = $6, updated_at = $7, data = $8
        WHERE id = $9
        """,
        draft.get("jd_number"), draft["lob"], draft["status"], _draft_title(draft),
        draft.get("sign_off", {}).get("prepared_by_name", ""),
        draft.get("linked_conversation_id"),
        datetime.fromisoformat(draft["updated_at"]), draft, draft["id"],
    )


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


async def list_jd_drafts() -> List[Dict[str, Any]]:
    """List all JD drafts (metadata only)."""
    pool = jd_db.get_pool()
    rows = await pool.fetch(
        """
        SELECT id, jd_number, lob, status, title, prepared_by_name,
               linked_conversation_id, created_at, updated_at, data
        FROM jd_drafts
        ORDER BY updated_at DESC
        """
    )

    drafts = []
    for row in rows:
        data = row["data"]
        drafts.append({
            "id": str(row["id"]),
            "jd_number": row["jd_number"],
            "lob": row["lob"],
            "business": data.get("basics", {}).get("business", ""),
            "status": row["status"],
            "title": row["title"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
            "linked_conversation_id": row["linked_conversation_id"],
            "prepared_by_name": row["prepared_by_name"],
            "completion_percent": 100 if row["status"] == "generated" else _calculate_completion_percent(data),
        })

    return drafts


async def update_jd_step(jd_id: str, step_key: str, step_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Merge new data into a specific step section of a draft and save."""
    draft = await get_jd_draft(jd_id)
    if draft is None:
        return None

    draft[step_key] = step_data
    await save_jd_draft(draft)

    return draft


async def set_jd_status(jd_id: str, status: str, generated_result: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Transition a draft's status (e.g. draft -> generated)."""
    draft = await get_jd_draft(jd_id)
    if draft is None:
        return None

    draft["status"] = status
    if generated_result is not None:
        draft["generated_result"] = generated_result
    await save_jd_draft(draft)

    return draft


async def link_conversation(jd_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
    """Link a JD draft to a council conversation id."""
    draft = await get_jd_draft(jd_id)
    if draft is None:
        return None

    draft["linked_conversation_id"] = conversation_id
    await save_jd_draft(draft)

    return draft


async def get_sample_template(lob: str) -> Optional[Dict[str, Any]]:
    """Load a stored sample (fully-filled) template for a LOB, if one has been generated yet."""
    pool = jd_db.get_pool()
    row = await pool.fetchrow(
        "SELECT filename, content FROM jd_sample_templates WHERE lob = $1", lob
    )
    if row is None:
        return None
    return {"filename": row["filename"], "content": row["content"]}


async def save_sample_template(lob: str, filename: str, content: bytes):
    """Persist a generated sample template so future downloads don't regenerate it."""
    pool = jd_db.get_pool()
    await pool.execute(
        """
        INSERT INTO jd_sample_templates (lob, filename, content, updated_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (lob) DO UPDATE
        SET filename = $2, content = $3, updated_at = $4
        """,
        lob, filename, content, datetime.utcnow(),
    )
