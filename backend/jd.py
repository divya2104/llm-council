"""API routes for the JD Creator wizard (Phase 1)."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, File, Form
from pydantic import BaseModel
from typing import Any, Dict
import uuid

from . import jd_storage
from . import storage
from . import jd_config
from . import jd_excel
from . import jd_db

router = APIRouter(prefix="/api/jd")

STEP_KEYS = {step["key"] for step in jd_config.WIZARD_STEPS}


class CreateJdDraftRequest(BaseModel):
    lob: str


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
        "db_available": jd_db.is_db_available(),
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


@router.post("/drafts/{jd_id}/generate")
async def generate_jd(jd_id: str, request: Request):
    """Validate completeness, flip status to generated, and return a stub result.

    Phase 1 does not call any AI model — real Hay-style JD assembly is Phase 2.
    """
    draft = await jd_storage.get_jd_draft(jd_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="JD draft not found")

    errors = jd_storage.validate_jd_draft(draft)
    if errors:
        raise HTTPException(status_code=400, detail={"message": "JD draft is incomplete", "errors": errors})

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
