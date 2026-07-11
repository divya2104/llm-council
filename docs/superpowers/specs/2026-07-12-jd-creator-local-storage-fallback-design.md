# JD Creator: local-storage fallback when Postgres is unreachable

## Problem

The Windows contributor's corporate laptop cannot reach the Azure Postgres
instance backing JD Creator storage — a local security proxy (Zscaler, likely
compounded by SentinelOne's firewall control) intercepts/resets the TLS
handshake to port 5432. Confirmed via a stdlib-only diagnostic (no
`asyncpg` involved) failing identically: 4/4 attempts across two runs, no
successes. Full diagnosis: `JD_CREATOR_PHASE1_WINDOWS_SSL_DEBUG.md`.

The real fix is an IT/Zscaler allow-list exception for
`llm-council-dev.postgres.database.azure.com:5432`, which is out of this
repo's control and may take time. In the meantime, the backend should not
require Postgres to be reachable in order to run at all — it should fall
back to local storage, keep working, and make the fallback visible to the
admin so drafts created this way can be migrated once the real DB is back.

## Approach

Local JSON-file fallback storage, detected once at startup, mirroring the
pattern `backend/storage.py` already uses for conversation storage (one
JSON file per record). Rejected alternatives:

- **SQLite fallback** — more "database-shaped" but adds schema-translation
  complexity for no benefit at this data volume (a handful of drafts).
- **Per-request fallback** (try DB, catch, fall back, on every call) —
  would make every save/load eat a slow connect-timeout on the known-failing
  path before falling back. Since the failure is currently 100% consistent,
  this only adds latency with no upside over a single startup check.

## Components

### 1. `backend/jd_db.py`
`init_pool()` no longer crashes the app on connection failure. It tries once
(existing behavior otherwise unchanged — no retry loop, that was a separate,
rejected patch), catches the failure, logs it, and sets a module-level
`DB_AVAILABLE = False` instead of raising. New accessor: `is_db_available() -> bool`.

### 2. `backend/jd_local_storage.py` (new)
JSON-file storage matching `jd_storage.py`'s public function signatures:
`create_jd_draft`, `get_jd_draft`, `save_jd_draft`, `list_jd_drafts`,
`delete_jd_draft`, `update_jd_step`, `set_jd_status`, `link_conversation`.
One file per draft under `data/jd_drafts_local/<id>.json`. A separate small
counters file (`data/jd_drafts_local/_counters.json`) tracks local
jd_number sequences per LOB, independent of the DB's counter table.

### 3. `backend/jd_storage.py`
Each public function becomes a dispatch: check `jd_db.is_db_available()`,
call either the existing Postgres path or the new `jd_local_storage`
function. `backend/jd.py` (the API routes) is untouched — it only ever
calls `jd_storage`, so the branching is centralized in one place.

### 4. jd_number collision avoidance
Locally-created drafts get a visibly distinct number,
`JD-{lob}-LOCAL-{n}`, from the local-only counter — not the shared DB
sequence, since other users may be creating real drafts in Postgres in the
same window and a naive shared counter would collide. On migration, each
draft is assigned a real `JD-{lob}-00042`-style number from the actual DB
counter, replacing the local placeholder.

### 5. UI banner
`/api/jd/config` response gains one field: `db_available: bool`. The
frontend already fetches this config once on load (`App.jsx`, `jdConfig`
state) and passes it down to every JD Creator screen. When
`db_available === false`, `App.jsx` renders a persistent banner directly
under `TopNav`:

> "Working offline — DB connection unavailable. Drafts are saved locally on
> this machine and need to be synced once the connection is fixed."

No new endpoint, no new frontend fetch.

### 6. `scripts/migrate_local_jd_to_db.py` (new)
Run manually once IT confirms the network fix. Connects to Postgres (via
`jd_db.init_pool()`, which should now succeed), reads every file under
`data/jd_drafts_local/`, inserts each as a new row with a freshly-assigned
real jd_number via the existing `_next_jd_number` logic, then deletes the
local file on success. One-off, no scheduling, no UI trigger (decided:
script over UI button — this happens once, rarely, and the person running
it is already comfortable with the terminal).

## Error handling

- Startup DB failure is caught once, logged, and the app boots in local
  mode rather than dying — this is the whole point of the change.
- Sample-template caching (`get_sample_template` / `save_sample_template`,
  which persist generated Excel bytes) is skipped entirely in local mode.
  The calling route already treats a cache miss as "regenerate," so this
  degrades gracefully with no new code needed there.
- No live reconnection while the process is running. If Postgres becomes
  reachable mid-session, the fix is to restart the backend. This is a
  deliberate scope cut (`ponytail:` comment in code) — not worth the added
  complexity for something that, once IT applies the fix, is a one-time
  event.

## Testing

- `backend/test_jd_local_storage.py` — stdlib-only self-check (no test
  framework) exercising create/get/save/list/delete against
  `jd_local_storage` directly.
- Manual verification: run the backend locally with `DATABASE_URL` pointed
  at an unreachable host, confirm the app boots, the banner appears, and a
  full draft can be created/edited/saved through the wizard UI.

## Out of scope

- Live/automatic reconnection without a restart.
- A UI-driven migration trigger (deferred in favor of the script).
- Any change to the actual network/Zscaler block — that's an IT ticket, not
  a code fix.
