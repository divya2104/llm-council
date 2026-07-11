# JD Creator Local-Storage DB Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the JD Creator backend boot and stay usable even when Postgres is unreachable (e.g. the Windows corporate-laptop Zscaler block documented in `JD_CREATOR_PHASE1_WINDOWS_SSL_DEBUG.md`), by falling back to local JSON-file storage and telling the admin in the UI that drafts aren't in the DB yet.

**Architecture:** `jd_db.init_pool()` stops crashing the app on connection failure and instead sets an `is_db_available()` flag. `jd_storage.py` (the single module all API routes go through) dispatches every read/write to either the existing Postgres code or a new `jd_local_storage.py` module (JSON files, one per draft, mirroring the existing `backend/storage.py` pattern) based on that flag. The frontend already fetches `/api/jd/config` once on load; it gains one new field, `db_available`, which drives a persistent banner. A one-off script later pushes locally-saved drafts into Postgres once the connection is fixed.

**Tech Stack:** Python 3.10+ (FastAPI, asyncpg), stdlib `json`/`unittest.mock` for tests (no test framework in this repo), React (frontend).

## Global Constraints

- `requires-python = ">=3.10"` (pyproject.toml) — don't use syntax newer than 3.10 supports.
- No new dependencies — stdlib only for the fallback storage and tests.
- No test framework (no pytest in this repo) — tests are stdlib `unittest.mock`-based `__main__` self-checks, run via `uv run python -m backend.test_X` or `uv run python scripts/test_X.py`, matching the existing convention in this codebase.
- Local-mode jd_numbers use the format `JD-{lob}-LOCAL-{n}` (from a counter separate from the DB's, to avoid colliding with numbers assigned to other users' drafts created directly in Postgres during the same window).
- No live reconnection while the process is running — DB availability is decided once at startup; if Postgres becomes reachable mid-session, the backend must be restarted to pick it up. This is a deliberate scope cut.
- Sample-template caching (`get_sample_template`/`save_sample_template`, which persist generated Excel bytes) is skipped entirely in local mode — the calling route already regenerates on a cache miss, so no new code is needed there beyond a no-op guard.
- Migration from local storage to Postgres is a manually-run script (`scripts/migrate_local_jd_to_db.py`), not a UI-triggered action — confirmed with the user during design.
- Spec: `docs/superpowers/specs/2026-07-12-jd-creator-local-storage-fallback-design.md`.

---

### Task 1: Local JSON-file storage primitives

**Files:**
- Modify: `backend/jd_config.py` (add one constant)
- Create: `backend/jd_local_storage.py`
- Test: `backend/test_jd_local_storage.py`

**Interfaces:**
- Consumes: nothing new (self-contained).
- Produces: `jd_config.LOCAL_DRAFTS_DIR: str`; `jd_local_storage.ensure_dir()`, `next_jd_number(lob: str) -> str`, `write_draft(draft: dict)`, `load_draft(jd_id: str) -> Optional[dict]`, `delete_draft(jd_id: str) -> bool`, `list_draft_files() -> List[dict]`. Task 3 depends on all six of these.

- [ ] **Step 1: Write the failing test**

Create `backend/test_jd_local_storage.py`:

```python
"""Self-check for jd_local_storage.py. Run directly: python -m backend.test_jd_local_storage"""

import shutil
import tempfile

from . import jd_config, jd_local_storage


def main():
    original_dir = jd_config.LOCAL_DRAFTS_DIR
    tmp_dir = tempfile.mkdtemp()
    jd_config.LOCAL_DRAFTS_DIR = tmp_dir
    try:
        _check_next_jd_number_increments_per_lob()
        _check_write_load_round_trip()
        _check_list_draft_files()
        _check_delete_draft()
        print("OK: jd_local_storage create/get/save/list/delete round-trip correctly")
    finally:
        jd_config.LOCAL_DRAFTS_DIR = original_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _check_next_jd_number_increments_per_lob():
    assert jd_local_storage.next_jd_number("AMC") == "JD-AMC-LOCAL-1"
    assert jd_local_storage.next_jd_number("AMC") == "JD-AMC-LOCAL-2"
    assert jd_local_storage.next_jd_number("NBFC") == "JD-NBFC-LOCAL-1"


def _check_write_load_round_trip():
    draft = {"id": "abc123", "lob": "AMC", "status": "draft"}
    jd_local_storage.write_draft(draft)
    loaded = jd_local_storage.load_draft("abc123")
    assert loaded == draft, f"expected {draft}, got {loaded}"
    assert jd_local_storage.load_draft("does-not-exist") is None


def _check_list_draft_files():
    jd_local_storage.write_draft({"id": "d1", "lob": "AMC", "status": "draft"})
    jd_local_storage.write_draft({"id": "d2", "lob": "NBFC", "status": "draft"})
    ids = {d["id"] for d in jd_local_storage.list_draft_files()}
    assert {"abc123", "d1", "d2"} <= ids, f"missing drafts, got {ids}"


def _check_delete_draft():
    jd_local_storage.write_draft({"id": "to-delete", "lob": "AMC", "status": "draft"})
    assert jd_local_storage.delete_draft("to-delete") is True
    assert jd_local_storage.load_draft("to-delete") is None
    assert jd_local_storage.delete_draft("to-delete") is False


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m backend.test_jd_local_storage`
Expected: `ModuleNotFoundError: No module named 'backend.jd_local_storage'` (module doesn't exist yet).

- [ ] **Step 3: Add the constant and write the implementation**

In `backend/jd_config.py`, right after the existing `DATABASE_URL = os.getenv("DATABASE_URL")` line, add:

```python

# Local JSON-file fallback storage for JD drafts, used when Postgres is unreachable
LOCAL_DRAFTS_DIR = "data/jd_drafts_local"
```

Create `backend/jd_local_storage.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m backend.test_jd_local_storage`
Expected: `OK: jd_local_storage create/get/save/list/delete round-trip correctly`

- [ ] **Step 5: Commit**

```bash
git add backend/jd_config.py backend/jd_local_storage.py backend/test_jd_local_storage.py
git commit -m "Add local JSON-file fallback storage for JD drafts"
```

---

### Task 2: `jd_db.init_pool()` falls back instead of crashing

**Files:**
- Modify: `backend/jd_db.py`
- Test: `backend/test_jd_db_fallback.py`

**Interfaces:**
- Consumes: nothing from Task 1 (independent).
- Produces: `jd_db.is_db_available() -> bool`. `jd_db.init_pool()` no longer raises on any connection failure. Task 3 and Task 4 both depend on `is_db_available()`.

- [ ] **Step 1: Write the failing test**

Create `backend/test_jd_db_fallback.py`:

```python
"""Self-check for jd_db.init_pool()'s fallback-on-failure behavior. Run directly: python -m backend.test_jd_db_fallback"""

import asyncio
from unittest.mock import patch

from . import jd_config, jd_db


class _FakeAcquireCtx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **kw):
        pass


class _FakePool:
    def acquire(self):
        return _FakeAcquireCtx()

    async def close(self):
        pass


async def _check_falls_back_on_connection_failure():
    jd_config.DATABASE_URL = "postgresql://fake"

    async def always_fails(*args, **kwargs):
        raise ConnectionResetError("simulated reset")

    with patch("backend.jd_db.asyncpg.create_pool", side_effect=always_fails):
        await jd_db.init_pool()  # must not raise

    assert jd_db.is_db_available() is False


async def _check_succeeds_when_connection_works():
    jd_config.DATABASE_URL = "postgresql://fake"

    async def succeeds(*args, **kwargs):
        return _FakePool()

    with patch("backend.jd_db.asyncpg.create_pool", side_effect=succeeds):
        await jd_db.init_pool()

    assert jd_db.is_db_available() is True
    await jd_db.close_pool()


async def _check_falls_back_when_url_unset():
    jd_config.DATABASE_URL = None
    await jd_db.init_pool()
    assert jd_db.is_db_available() is False


async def main():
    await _check_falls_back_on_connection_failure()
    await _check_succeeds_when_connection_works()
    await _check_falls_back_when_url_unset()
    print("OK: init_pool() falls back to local mode on any failure, succeeds when DB reachable")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m backend.test_jd_db_fallback`
Expected: `AttributeError: module 'backend.jd_db' has no attribute 'is_db_available'`

- [ ] **Step 3: Write the implementation**

Replace `backend/jd_db.py`'s `init_pool`/`close_pool`/`get_pool` section (everything from `_pool: asyncpg.Pool = None` down) with:

```python
_pool: asyncpg.Pool = None
_db_available = False


async def _init_connection(conn):
    """Auto-encode/decode Python dicts <-> jsonb for every connection in the pool."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jd_drafts (
    id TEXT PRIMARY KEY,
    jd_number TEXT UNIQUE,
    lob TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    title TEXT,
    prepared_by_name TEXT,
    linked_conversation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jd_drafts_status ON jd_drafts(status);
CREATE INDEX IF NOT EXISTS idx_jd_drafts_lob ON jd_drafts(lob);

CREATE TABLE IF NOT EXISTS jd_number_counters (
    lob TEXT PRIMARY KEY,
    last_value INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS jd_sample_templates (
    lob TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    content BYTEA NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
"""


async def init_pool():
    """Try to create the connection pool and bootstrap the schema. Called on app startup.

    Does NOT raise if Postgres is unreachable — sets is_db_available() to
    False instead, so the app boots in local-storage fallback mode (see
    jd_local_storage.py and JD_CREATOR_PHASE1_WINDOWS_SSL_DEBUG.md). Catches
    broadly (not just OSError) since the goal is "any connection problem ->
    fall back," whether that's a network block, bad credentials, or a typo
    in DATABASE_URL.
    """
    # ponytail: availability is decided once at startup, no background
    # reconnect loop. If Postgres comes back mid-session, restart the
    # process — add a periodic recheck only if that restart step becomes
    # a real pain point in practice.
    global _pool, _db_available
    if not jd_config.DATABASE_URL:
        print("[jd_db] DATABASE_URL not set — running in local-storage fallback mode.")
        _db_available = False
        return
    try:
        _pool = await asyncpg.create_pool(
            jd_config.DATABASE_URL, min_size=1, max_size=5, init=_init_connection, timeout=15
        )
        async with _pool.acquire() as conn:
            await conn.execute(_SCHEMA)
        _db_available = True
    except Exception as e:
        print(f"[jd_db] Could not connect to Postgres ({e!r}) — running in local-storage fallback mode.")
        _pool = None
        _db_available = False


def is_db_available() -> bool:
    return _db_available


async def close_pool():
    """Close the connection pool. Called on app shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("JD DB pool not initialized — did the app startup hook run?")
    return _pool
```

Note: the file's top (`"""Postgres connection pool..."""` docstring, `import json`, `import asyncpg`, `from . import jd_config`) stays unchanged — only the code from `_pool: asyncpg.Pool = None` onward is replaced.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m backend.test_jd_db_fallback`
Expected: `OK: init_pool() falls back to local mode on any failure, succeeds when DB reachable`

- [ ] **Step 5: Commit**

```bash
git add backend/jd_db.py backend/test_jd_db_fallback.py
git commit -m "Make jd_db.init_pool() fall back instead of crashing on connection failure"
```

---

### Task 3: `jd_storage.py` dispatches between Postgres and local storage

**Files:**
- Modify: `backend/jd_storage.py`
- Test: `backend/test_jd_storage_fallback.py`

**Interfaces:**
- Consumes: `jd_local_storage.next_jd_number`, `write_draft`, `load_draft`, `delete_draft`, `list_draft_files` (Task 1); `jd_db.is_db_available()` (Task 2).
- Produces: no change to `jd_storage.py`'s public function signatures — `jd.py` (Task 4 and beyond) needs no changes to call sites.

- [ ] **Step 1: Write the failing test**

Create `backend/test_jd_storage_fallback.py`:

```python
"""Self-check for jd_storage.py's DB/local dispatch logic. Run directly: python -m backend.test_jd_storage_fallback"""

import asyncio
import shutil
import tempfile
from unittest.mock import patch

from . import jd_config, jd_storage


async def main():
    original_dir = jd_config.LOCAL_DRAFTS_DIR
    tmp_dir = tempfile.mkdtemp()
    jd_config.LOCAL_DRAFTS_DIR = tmp_dir
    try:
        with patch("backend.jd_db.is_db_available", return_value=False):
            await _check_full_round_trip_via_local_storage()
        print("OK: jd_storage dispatches to local storage end-to-end when DB is unavailable")
    finally:
        jd_config.LOCAL_DRAFTS_DIR = original_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def _check_full_round_trip_via_local_storage():
    draft = await jd_storage.create_jd_draft("test-id-1", "AMC")
    assert draft["jd_number"] == "JD-AMC-LOCAL-1", draft["jd_number"]

    loaded = await jd_storage.get_jd_draft("test-id-1")
    assert loaded["id"] == "test-id-1"

    updated = await jd_storage.update_jd_step("test-id-1", "purpose", {"text": "hello"})
    assert updated["purpose"]["text"] == "hello"

    drafts = await jd_storage.list_jd_drafts()
    assert any(d["id"] == "test-id-1" for d in drafts)

    sample = await jd_storage.get_sample_template("AMC")
    assert sample is None  # not cached in local mode

    deleted = await jd_storage.delete_jd_draft("test-id-1")
    assert deleted is True
    assert await jd_storage.get_jd_draft("test-id-1") is None


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m backend.test_jd_storage_fallback`
Expected: `AssertionError` on the `jd_number` check — `create_jd_draft` currently calls `jd_db.get_pool()` unconditionally and raises `RuntimeError: JD DB pool not initialized` instead.

- [ ] **Step 3: Write the implementation**

In `backend/jd_storage.py`, change the import line:

```python
from . import jd_config, jd_db
```

to:

```python
from . import jd_config, jd_db, jd_local_storage
```

Replace `_next_jd_number`:

```python
async def _next_jd_number(lob: str) -> str:
    """Generate the next human-readable tracking id, e.g. JD-AMC-00001.

    Backed by an atomic upsert-and-increment on jd_number_counters, so ids
    stay unique even under concurrent draft creation. Falls back to a
    local-only counter (JD-{lob}-LOCAL-{n}) when Postgres is unreachable.
    """
    if not jd_db.is_db_available():
        return jd_local_storage.next_jd_number(lob)
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
```

Replace `create_jd_draft`:

```python
async def create_jd_draft(jd_id: str, lob: str) -> Dict[str, Any]:
    """Create a new JD draft and persist it."""
    jd_number = await _next_jd_number(lob)
    draft = _new_draft_shape(jd_id, lob, jd_number)

    if not jd_db.is_db_available():
        jd_local_storage.write_draft(draft)
        return draft

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
```

Replace `delete_jd_draft`:

```python
async def delete_jd_draft(jd_id: str) -> bool:
    """Delete a JD draft from storage. Returns False if it didn't exist."""
    if not jd_db.is_db_available():
        return jd_local_storage.delete_draft(jd_id)
    pool = jd_db.get_pool()
    result = await pool.execute("DELETE FROM jd_drafts WHERE id = $1", jd_id)
    return result != "DELETE 0"
```

Replace `get_jd_draft`:

```python
async def get_jd_draft(jd_id: str) -> Optional[Dict[str, Any]]:
    """Load a JD draft from storage."""
    if not jd_db.is_db_available():
        return jd_local_storage.load_draft(jd_id)
    pool = jd_db.get_pool()
    row = await pool.fetchrow("SELECT data FROM jd_drafts WHERE id = $1", jd_id)
    if row is None:
        return None
    return row["data"]
```

Replace `save_jd_draft`:

```python
async def save_jd_draft(draft: Dict[str, Any]):
    """Save a JD draft to storage, bumping updated_at."""
    draft["updated_at"] = datetime.utcnow().isoformat()

    if not jd_db.is_db_available():
        jd_local_storage.write_draft(draft)
        return

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
```

Replace `list_jd_drafts` — and add a `_draft_metadata` helper right before it — with:

```python
def _draft_metadata(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Build the list-view metadata shape for a locally-stored draft dict."""
    return {
        "id": draft["id"],
        "jd_number": draft.get("jd_number"),
        "lob": draft["lob"],
        "business": draft.get("basics", {}).get("business", ""),
        "status": draft["status"],
        "title": _draft_title(draft),
        "created_at": draft["created_at"],
        "updated_at": draft["updated_at"],
        "linked_conversation_id": draft.get("linked_conversation_id"),
        "prepared_by_name": draft.get("sign_off", {}).get("prepared_by_name", ""),
        "completion_percent": 100 if draft["status"] == "generated" else _calculate_completion_percent(draft),
    }


async def list_jd_drafts() -> List[Dict[str, Any]]:
    """List all JD drafts (metadata only)."""
    if not jd_db.is_db_available():
        drafts = [_draft_metadata(d) for d in jd_local_storage.list_draft_files()]
        drafts.sort(key=lambda d: d["updated_at"], reverse=True)
        return drafts

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
```

Replace `get_sample_template` and `save_sample_template`:

```python
async def get_sample_template(lob: str) -> Optional[Dict[str, Any]]:
    """Load a stored sample (fully-filled) template for a LOB, if one has been generated yet."""
    if not jd_db.is_db_available():
        return None  # not cached in local mode; caller regenerates on every request
    pool = jd_db.get_pool()
    row = await pool.fetchrow(
        "SELECT filename, content FROM jd_sample_templates WHERE lob = $1", lob
    )
    if row is None:
        return None
    return {"filename": row["filename"], "content": row["content"]}


async def save_sample_template(lob: str, filename: str, content: bytes):
    """Persist a generated sample template so future downloads don't regenerate it."""
    if not jd_db.is_db_available():
        return  # no-op in local mode
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
```

`update_jd_step`, `set_jd_status`, `link_conversation`, `validate_jd_draft`, `default_step_value`, `_new_draft_shape`, `_draft_title`, `_empty_hierarchy_box`, and `_calculate_completion_percent` are unchanged — they only call the now-dispatching `get_jd_draft`/`save_jd_draft`, or operate purely on the draft dict.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m backend.test_jd_storage_fallback`
Expected: `OK: jd_storage dispatches to local storage end-to-end when DB is unavailable`

Also re-run Tasks 1 and 2's tests to confirm nothing broke:

Run: `uv run python -m backend.test_jd_local_storage && uv run python -m backend.test_jd_db_fallback`
Expected: both `OK: ...` lines.

- [ ] **Step 5: Commit**

```bash
git add backend/jd_storage.py backend/test_jd_storage_fallback.py
git commit -m "Dispatch JD draft storage between Postgres and local fallback"
```

---

### Task 4: Expose `db_available` on `/api/jd/config`

**Files:**
- Modify: `backend/jd.py`
- Test: `backend/test_jd_config_endpoint.py`

**Interfaces:**
- Consumes: `jd_db.is_db_available()` (Task 2).
- Produces: `/api/jd/config` response gains `db_available: bool`. Task 5 (frontend) depends on this exact field name.

- [ ] **Step 1: Write the failing test**

Create `backend/test_jd_config_endpoint.py`:

```python
"""Self-check that /api/jd/config exposes db_available. Run directly: python -m backend.test_jd_config_endpoint"""

import asyncio
from unittest.mock import patch

from . import jd


async def main():
    with patch("backend.jd.jd_db.is_db_available", return_value=False):
        config = await jd.get_jd_config()
    assert config["db_available"] is False

    with patch("backend.jd.jd_db.is_db_available", return_value=True):
        config = await jd.get_jd_config()
    assert config["db_available"] is True

    print("OK: /api/jd/config exposes db_available correctly")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m backend.test_jd_config_endpoint`
Expected: `KeyError: 'db_available'`

- [ ] **Step 3: Write the implementation**

In `backend/jd.py`, change the imports at the top:

```python
from . import jd_storage
from . import storage
from . import jd_config
from . import jd_excel
```

to:

```python
from . import jd_storage
from . import storage
from . import jd_config
from . import jd_excel
from . import jd_db
```

In `get_jd_config`, add one line at the end of the returned dict (right after `"wizard_steps": jd_config.WIZARD_STEPS,`):

```python
        "wizard_steps": jd_config.WIZARD_STEPS,
        "db_available": jd_db.is_db_available(),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m backend.test_jd_config_endpoint`
Expected: `OK: /api/jd/config exposes db_available correctly`

- [ ] **Step 5: Commit**

```bash
git add backend/jd.py backend/test_jd_config_endpoint.py
git commit -m "Expose db_available on /api/jd/config"
```

---

### Task 5: Frontend offline banner

**Files:**
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/App.css`

**Interfaces:**
- Consumes: `jdConfig.db_available` (Task 4), already available in `App.jsx`'s existing `jdConfig` state (no new fetch needed — `loadJdConfig()` already calls `jdApi.getConfig()` on mount).
- Produces: `.jd-offline-banner` CSS class; no new exports.

- [ ] **Step 1: Add the banner CSS**

In `frontend/src/App.css`, add (matching the existing `--warning`/`--warning-wash` tokens used elsewhere, e.g. `components/jd/JdWizard.css`, and the `.jd-generated-banner` pattern in `components/jd/JdGeneratedPanel.css`):

```css
.jd-offline-banner {
  padding: 10px 24px;
  background: var(--warning-wash);
  color: var(--warning);
  font-size: 13px;
  border-bottom: 1px solid var(--rule);
}
```

- [ ] **Step 2: Render the banner in App.jsx**

In `frontend/src/App.jsx`, find the render's return statement:

```jsx
  return (
    <div className="app-shell">
      <TopNav />
      <div className="app">
```

Change it to:

```jsx
  return (
    <div className="app-shell">
      <TopNav />
      {jdConfig && !jdConfig.db_available && (
        <div className="jd-offline-banner">
          Working offline — DB connection unavailable. Drafts are saved locally on this machine and need to be synced once the connection is fixed.
        </div>
      )}
      <div className="app">
```

- [ ] **Step 3: Verify in the browser**

Start the backend with an unreachable `DATABASE_URL` (temporarily, e.g. `DATABASE_URL=postgresql://user:pass@127.0.0.1:1/doesnotexist` in `.env`) and the frontend dev server, then:

1. Open the app in the browser preview.
2. Confirm the banner reading "Working offline — DB connection unavailable..." appears directly under the top nav, on every screen (landing, dashboard, wizard).
3. Create a draft, fill in a step, confirm it saves without error (autosave shouldn't throw).
4. Restore the real `DATABASE_URL` in `.env` afterward.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.jsx frontend/src/App.css
git commit -m "Show an offline banner when the JD DB connection is unavailable"
```

---

### Task 6: Migration script for locally-saved drafts

**Files:**
- Create: `scripts/migrate_local_jd_to_db.py`
- Test: `scripts/test_migrate_local_jd_to_db.py`

**Interfaces:**
- Consumes: `jd_local_storage.list_draft_files`, `delete_draft` (Task 1); `jd_db.init_pool`, `is_db_available`, `get_pool` (Task 2); `jd_storage._next_jd_number`, `_draft_title` (Task 3, existing).
- Produces: standalone script, run manually — nothing else depends on it.

- [ ] **Step 1: Write the failing test**

Create `scripts/test_migrate_local_jd_to_db.py`:

```python
"""Self-check for migrate_local_jd_to_db.py's INSERT-arg construction.
Run directly: python scripts/test_migrate_local_jd_to_db.py
"""

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_spec = importlib.util.spec_from_file_location(
    "migrate_local_jd_to_db",
    os.path.join(os.path.dirname(__file__), "migrate_local_jd_to_db.py"),
)
migrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate)


def main():
    draft = {
        "id": "abc123",
        "jd_number": "JD-AMC-LOCAL-1",
        "lob": "AMC",
        "status": "draft",
        "basics": {"poornata_position_title": "Fund Manager"},
        "sign_off": {"prepared_by_name": "Devanshi"},
        "linked_conversation_id": None,
        "created_at": "2026-07-12T10:00:00",
        "updated_at": "2026-07-12T11:00:00",
    }

    args = migrate._insert_args(draft, "JD-AMC-00042")

    assert args[0] == "abc123"
    assert args[1] == "JD-AMC-00042"
    assert args[2] == "AMC"
    assert args[3] == "draft"
    assert args[4] == "Fund Manager"
    assert args[5] == "Devanshi"
    assert args[6] is None
    assert args[9] == draft
    assert len(args) == 10

    print("OK: migration script builds INSERT args in the correct column order")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python scripts/test_migrate_local_jd_to_db.py`
Expected: `FileNotFoundError` (the module file `scripts/migrate_local_jd_to_db.py` doesn't exist yet).

- [ ] **Step 3: Write the implementation**

Create `scripts/migrate_local_jd_to_db.py`:

```python
"""One-off migration: push locally-saved JD drafts (created while Postgres was
unreachable) into the real database, assigning each a proper jd_number.

Run manually once IT confirms the Postgres connection is fixed:
    uv run python scripts/migrate_local_jd_to_db.py

Safe to run more than once — migrated drafts are removed from the local
fallback directory as they're migrated, so a second run just finds nothing
left to do.
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import jd_db, jd_local_storage, jd_storage


def _insert_args(draft: dict, new_number: str) -> tuple:
    """Build the positional args for the jd_drafts INSERT, in column order."""
    return (
        draft["id"], new_number, draft["lob"], draft["status"],
        jd_storage._draft_title(draft),
        draft.get("sign_off", {}).get("prepared_by_name", ""),
        draft.get("linked_conversation_id"),
        datetime.fromisoformat(draft["created_at"]),
        datetime.fromisoformat(draft["updated_at"]),
        draft,
    )


async def main():
    await jd_db.init_pool()
    if not jd_db.is_db_available():
        print("Still can't reach Postgres — nothing migrated. Fix the connection first.")
        return

    local_drafts = jd_local_storage.list_draft_files()
    if not local_drafts:
        print("No locally-saved drafts to migrate.")
        return

    pool = jd_db.get_pool()
    for draft in local_drafts:
        old_number = draft.get("jd_number")
        new_number = await jd_storage._next_jd_number(draft["lob"])

        await pool.execute(
            """
            INSERT INTO jd_drafts
                (id, jd_number, lob, status, title, prepared_by_name,
                 linked_conversation_id, created_at, updated_at, data)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            *_insert_args(draft, new_number),
        )
        jd_local_storage.delete_draft(draft["id"])
        print(f"Migrated {old_number} -> {new_number} ({draft['id']})")

    print(f"Done. Migrated {len(local_drafts)} draft(s).")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python scripts/test_migrate_local_jd_to_db.py`
Expected: `OK: migration script builds INSERT args in the correct column order`

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_local_jd_to_db.py scripts/test_migrate_local_jd_to_db.py
git commit -m "Add one-off migration script for locally-saved JD drafts"
```

---

### Task 7: End-to-end verification

**Files:** none (verification only).

**Interfaces:**
- Consumes: everything from Tasks 1–5.
- Produces: confidence the whole thing actually works before calling this done.

- [ ] **Step 1: Run every self-check together**

```bash
uv run python -m backend.test_jd_local_storage
uv run python -m backend.test_jd_db_fallback
uv run python -m backend.test_jd_storage_fallback
uv run python -m backend.test_jd_config_endpoint
uv run python scripts/test_migrate_local_jd_to_db.py
```

Expected: five `OK: ...` lines, no errors.

- [ ] **Step 2: Boot the real backend in fallback mode**

Temporarily set `DATABASE_URL=postgresql://user:pass@127.0.0.1:1/doesnotexist` in `.env`, then:

```bash
uv run python -m backend.main
```

Expected: the server starts and logs `[jd_db] Could not connect to Postgres (...) — running in local-storage fallback mode.` — it must NOT crash or exit.

- [ ] **Step 3: Full wizard flow through the browser**

With the backend still running in fallback mode and the frontend dev server up:

1. Load the app — confirm the offline banner appears.
2. Create a new JD draft — confirm its jd_number matches `JD-{lob}-LOCAL-1`.
3. Fill in a few wizard steps, confirm autosave works (no console errors).
4. Reload the page, reopen the draft, confirm the data persisted (i.e. it's reading back from `data/jd_drafts_local/`).
5. Delete the draft, confirm it disappears from the dashboard list.

- [ ] **Step 4: Restore real DB config and confirm normal mode still works**

Put the real `DATABASE_URL` back in `.env`, restart the backend, confirm:
- The offline banner does NOT appear.
- `list_jd_drafts` / draft creation still work against Postgres as before (unchanged code path).

- [ ] **Step 5: Final commit (if any cleanup was needed)**

If verification surfaced no code changes, there's nothing to commit here — Tasks 1–6 already covered the implementation. If a bug was found and fixed during verification, commit it with a message describing what broke and why.
