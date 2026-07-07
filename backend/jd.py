"""API routes for the JD Creator wizard (Phase 1)."""

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, File, Form
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uuid

from . import jd_storage
from . import storage
from . import jd_config
from . import jd_excel

router = APIRouter(prefix="/api/jd")

STEP_KEYS = {
    "basics",
    "purpose",
    "dimensions",
    "context",
    "accountabilities",
    "reports_and_relationships",
    "hay_factors",
    "sign_off",
}


class CreateJdDraftRequest(BaseModel):
    lob: str


class GenerateJdRequest(BaseModel):
    pass


@router.get("/config")
async def get_jd_config():
    """Serve JD Creator dropdown options / thresholds / step order to the frontend."""
    return {
        "lob_options": jd_config.LOB_OPTIONS,
        "lob_labels": jd_config.LOB_LABELS,
        "lob_descriptions": jd_config.LOB_DESCRIPTIONS,
        "lob_business_options": jd_config.LOB_BUSINESS_OPTIONS,
        "lob_org_context_templates": jd_config.LOB_ORG_CONTEXT_TEMPLATES,
        "lob_city_options": jd_config.LOB_CITY_OPTIONS,
        "hierarchy_levels": jd_config.HIERARCHY_LEVELS,
        "relationship_frequencies": jd_config.RELATIONSHIP_FREQUENCIES,
        "ambiguity_levels": jd_config.AMBIGUITY_LEVELS,
        "departments_by_function": jd_config.DEPARTMENTS_BY_FUNCTION,
        "minimum_qualification_options": jd_config.MINIMUM_QUALIFICATION_OPTIONS,
        "industry_experience_options": jd_config.INDUSTRY_EXPERIENCE_OPTIONS,
        "min_accountabilities": jd_config.MIN_ACCOUNTABILITIES,
        "max_accountabilities": jd_config.MAX_ACCOUNTABILITIES,
        "min_internal_relationships": jd_config.MIN_INTERNAL_RELATIONSHIPS,
        "min_external_relationships": jd_config.MIN_EXTERNAL_RELATIONSHIPS,
        "min_challenges": jd_config.MIN_CHALLENGES,
        "max_challenges": jd_config.MAX_CHALLENGES,
        "job_purpose_min_chars": jd_config.JOB_PURPOSE_MIN_CHARS,
        "job_purpose_max_chars": jd_config.JOB_PURPOSE_MAX_CHARS,
        "job_context_min_chars": jd_config.JOB_CONTEXT_MIN_CHARS,
        "wizard_steps": jd_config.WIZARD_STEPS,
    }


@router.get("/drafts")
async def list_drafts():
    """List all JD drafts (metadata only)."""
    return await jd_storage.list_jd_drafts()


@router.post("/drafts")
async def create_draft(request: CreateJdDraftRequest):
    """Create a new JD draft for a given line of business."""
    if request.lob not in jd_config.LOB_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid lob: {request.lob}")

    jd_id = str(uuid.uuid4())
    draft = await jd_storage.create_jd_draft(jd_id, request.lob)
    return draft


@router.get("/template")
async def download_template(lob: str):
    """Download a blank Excel template for offline JD authoring."""
    if lob not in jd_config.LOB_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid lob: {lob}")

    content = jd_excel.generate_template(lob)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="JD-Template-{lob}.xlsx"'},
    )


@router.get("/sample-template")
async def download_sample_template(lob: str):
    """Download a fully-filled example template, generating and caching it in the DB on first request."""
    if lob not in jd_config.LOB_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid lob: {lob}")

    sample = await jd_storage.get_sample_template(lob)
    if sample is None:
        filename = f"JD-Sample-{lob}.xlsx"
        content = jd_excel.generate_sample_template(lob)
        await jd_storage.save_sample_template(lob, filename, content)
        sample = {"filename": filename, "content": content}

    return Response(
        content=sample["content"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{sample["filename"]}"'},
    )


@router.post("/drafts/upload")
async def upload_draft(lob: str = Form(...), file: UploadFile = File(...)):
    """Create a new JD draft pre-filled from an uploaded Excel template."""
    if lob not in jd_config.LOB_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid lob: {lob}")

    file_bytes = await file.read()
    try:
        parsed_steps = jd_excel.parse_uploaded_workbook(file_bytes, lob)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    jd_id = str(uuid.uuid4())
    draft = await jd_storage.create_jd_draft(jd_id, lob)
    for step_key in STEP_KEYS:
        draft = await jd_storage.update_jd_step(jd_id, step_key, parsed_steps[step_key])

    return {"draft": draft, "warnings": []}


@router.get("/drafts/{jd_id}")
async def get_draft(jd_id: str):
    """Get a specific JD draft."""
    draft = await jd_storage.get_jd_draft(jd_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="JD draft not found")
    return draft


@router.patch("/drafts/{jd_id}/steps/{step_key}")
async def save_step(jd_id: str, step_key: str, step_data: Dict[str, Any]):
    """Autosave a single wizard step's data."""
    if step_key not in STEP_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown step: {step_key}")

    draft = await jd_storage.update_jd_step(jd_id, step_key, step_data)
    if draft is None:
        raise HTTPException(status_code=404, detail="JD draft not found")

    return draft


@router.post("/drafts/{jd_id}/steps/{step_key}/clear")
async def clear_step(jd_id: str, step_key: str):
    """Reset a single wizard step back to its blank default."""
    if step_key not in STEP_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown step: {step_key}")

    existing = await jd_storage.get_jd_draft(jd_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="JD draft not found")

    default_value = jd_storage.default_step_value(step_key, existing["lob"])
    draft = await jd_storage.update_jd_step(jd_id, step_key, default_value)

    return draft


@router.delete("/drafts/{jd_id}")
async def delete_draft(jd_id: str):
    """Permanently delete a JD draft."""
    deleted = await jd_storage.delete_jd_draft(jd_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="JD draft not found")

    return {"deleted": True}


def _validate_for_generate(draft: Dict[str, Any]) -> Dict[str, list]:
    """Re-validate NON-NEGOTIABLE completeness server-side. Returns {step_key: [errors]}."""
    errors: Dict[str, list] = {}

    basics = draft.get("basics", {})
    required_basics = [
        "business", "unit", "location", "poornata_position_number",
        "reports_to_position_number", "poornata_position_title",
        "reports_to_position_title", "function", "reports_to_function",
        "department", "reports_to_department", "designation_employee",
        "designation_manager", "org_hierarchy_level", "date_of_writing",
    ]
    missing = [f for f in required_basics if not str(basics.get(f, "")).strip()]
    if missing:
        errors["basics"] = [f"Missing required field: {f}" for f in missing]

    purpose_text = draft.get("purpose", {}).get("text", "")
    if not (jd_config.JOB_PURPOSE_MIN_CHARS <= len(purpose_text) <= jd_config.JOB_PURPOSE_MAX_CHARS):
        errors["purpose"] = [
            f"Job purpose must be between {jd_config.JOB_PURPOSE_MIN_CHARS} and "
            f"{jd_config.JOB_PURPOSE_MAX_CHARS} characters (currently {len(purpose_text)})"
        ]

    context = draft.get("context", {})
    context_errors = []
    if len(context.get("job_context", "")) < jd_config.JOB_CONTEXT_MIN_CHARS:
        context_errors.append(
            f"Job context must be at least {jd_config.JOB_CONTEXT_MIN_CHARS} characters"
        )
    challenges = [c for c in context.get("key_challenges", []) if str(c).strip()]
    if len(challenges) < jd_config.MIN_CHALLENGES:
        context_errors.append(f"At least {jd_config.MIN_CHALLENGES} distinct challenges required")
    if context_errors:
        errors["context"] = context_errors

    accountability_rows = [
        r for r in draft.get("accountabilities", {}).get("rows", [])
        if str(r.get("accountability", "")).strip() and str(r.get("supporting_actions", "")).strip()
    ]
    if len(accountability_rows) < jd_config.MIN_ACCOUNTABILITIES:
        errors["accountabilities"] = [
            f"At least {jd_config.MIN_ACCOUNTABILITIES} accountabilities required "
            f"(currently {len(accountability_rows)})"
        ]

    reports = draft.get("reports_and_relationships", {})
    reports_errors = []
    internal = [r for r in reports.get("internal_relationships", []) if str(r.get("stakeholder", "")).strip()]
    if len(internal) < jd_config.MIN_INTERNAL_RELATIONSHIPS:
        reports_errors.append(f"At least {jd_config.MIN_INTERNAL_RELATIONSHIPS} internal relationships required")
    external = [r for r in reports.get("external_relationships", []) if str(r.get("stakeholder", "")).strip()]
    if len(external) < jd_config.MIN_EXTERNAL_RELATIONSHIPS:
        reports_errors.append(f"At least {jd_config.MIN_EXTERNAL_RELATIONSHIPS} external relationships required")
    if reports_errors:
        errors["reports_and_relationships"] = reports_errors

    hay = draft.get("hay_factors", {})
    know_how = hay.get("know_how", {})
    decision_making = hay.get("decision_making", {})
    hay_errors = []
    if not know_how.get("min_qualification"):
        hay_errors.append("Minimum qualification is required")
    if not str(know_how.get("years_of_experience", "")).strip():
        hay_errors.append("Years of experience is required")
    if not know_how.get("technical_expertise_areas"):
        hay_errors.append("At least one technical expertise area is required")
    if not str(know_how.get("industry_experience", "")).strip():
        hay_errors.append("Industry experience is required")
    for field in ["independent_decisions", "decisions_needing_approval", "financial_approval_limit", "advisory_vs_final_authority"]:
        if not str(decision_making.get(field, "")).strip():
            hay_errors.append(f"Missing required field: {field}")
    if hay_errors:
        errors["hay_factors"] = hay_errors

    sign_off = draft.get("sign_off", {})
    sign_off_errors = []
    if not str(sign_off.get("prepared_by_name", "")).strip():
        sign_off_errors.append("Name is required")
    if not str(sign_off.get("prepared_by_email", "")).strip():
        sign_off_errors.append("Email is required")
    if not sign_off.get("confirmed"):
        sign_off_errors.append("Confirmation checkbox must be checked")
    if sign_off_errors:
        errors["sign_off"] = sign_off_errors

    return errors


@router.post("/drafts/{jd_id}/generate")
async def generate_jd(jd_id: str, request: Request, body: Optional[GenerateJdRequest] = None):
    """Validate completeness, flip status to generated, and return a stub result.

    Phase 1 does not call any AI model — real Hay-style JD assembly is Phase 2.
    """
    draft = await jd_storage.get_jd_draft(jd_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="JD draft not found")

    errors = _validate_for_generate(draft)
    if errors:
        raise HTTPException(status_code=400, detail={"message": "JD draft is incomplete", "errors": errors})

    from datetime import datetime

    sign_off = draft.get("sign_off", {})
    sign_off["confirmed_at"] = datetime.utcnow().isoformat()
    sign_off["user_agent"] = request.headers.get("user-agent")
    await jd_storage.update_jd_step(jd_id, "sign_off", sign_off)

    generated_result = {
        "placeholder": True,
        "message": "JD generation (AI-assisted Hay-style assembly) is coming in Phase 2.",
    }
    draft = await jd_storage.set_jd_status(jd_id, "generated", generated_result)

    return draft


@router.post("/drafts/{jd_id}/link-conversation")
async def link_conversation(jd_id: str):
    """Lazily create (or return existing) a council conversation linked to this JD draft."""
    draft = await jd_storage.get_jd_draft(jd_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="JD draft not found")

    if draft.get("linked_conversation_id"):
        return {"conversation_id": draft["linked_conversation_id"]}

    conversation_id = str(uuid.uuid4())
    storage.create_conversation(conversation_id)
    await jd_storage.link_conversation(jd_id, conversation_id)

    return {"conversation_id": conversation_id}
