"""JSON-file fallback storage for JD Creator drafts, used when Postgres is unreachable.

Mirrors the pattern in backend/storage.py (one JSON file per record). See
docs/superpowers/specs/2026-07-12-jd-creator-local-storage-fallback-design.md.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import jd_config


def ensure_dir():
    """Ensure the local drafts directory exists."""
    Path(jd_config.LOCAL_DRAFTS_DIR).mkdir(parents=True, exist_ok=True)


def _draft_path(jd_id: str) -> str:
    return os.path.join(jd_config.LOCAL_DRAFTS_DIR, f"{jd_id}.json")


def _counters_path() -> str:
    return os.path.join(jd_config.LOCAL_DRAFTS_DIR, "_counters.json")


def next_jd_number(lob: str) -> str:
    """Generate the next local-only tracking id, e.g. JD-AMC-LOCAL-1.

    Uses a counter file separate from the DB's jd_number_counters table, so
    numbers assigned while offline never collide with numbers other users'
    drafts get assigned directly in Postgres during the same window.
    """
    ensure_dir()
    path = _counters_path()
    counters = {}
    if os.path.exists(path):
        with open(path) as f:
            counters = json.load(f)
    counters[lob] = counters.get(lob, 0) + 1
    with open(path, "w") as f:
        json.dump(counters, f, indent=2)
    return f"JD-{lob}-LOCAL-{counters[lob]}"


def write_draft(draft: Dict[str, Any]):
    """Write (create or overwrite) a draft's JSON file."""
    ensure_dir()
    with open(_draft_path(draft["id"]), "w") as f:
        json.dump(draft, f, indent=2)


def load_draft(jd_id: str) -> Optional[Dict[str, Any]]:
    """Load a single draft by id, or None if it doesn't exist locally."""
    path = _draft_path(jd_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def delete_draft(jd_id: str) -> bool:
    """Delete a draft's JSON file. Returns False if it didn't exist."""
    path = _draft_path(jd_id)
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True


def list_draft_files() -> List[Dict[str, Any]]:
    """Return the raw draft dicts for every locally-stored draft."""
    ensure_dir()
    drafts = []
    for filename in os.listdir(jd_config.LOCAL_DRAFTS_DIR):
        if filename.endswith(".json") and not filename.startswith("_"):
            with open(os.path.join(jd_config.LOCAL_DRAFTS_DIR, filename)) as f:
                drafts.append(json.load(f))
    return drafts
