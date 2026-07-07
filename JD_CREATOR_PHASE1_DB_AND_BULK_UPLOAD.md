# JD Creator — Postgres Migration, Excel Bulk Upload & Wizard Refinements

Follow-up session to [`JD_CREATOR_PHASE1_UI_POLISH.md`](JD_CREATOR_PHASE1_UI_POLISH.md). Covers moving JD draft storage off local JSON files onto Azure-hosted Postgres, a new Excel template download/upload flow (including DB-backed sample templates), and a batch of wizard UI refinements. Everything here is still local/uncommitted on `feature/jd-creator-phase1` — nothing in this session has been pushed.

## Why: local JSON files weren't enough

`data/jd_drafts/*.json` worked for single-machine dev, but broke the actual goal — data available across sessions and contributors — in two ways: locally it only works if everyone hits the same laptop's backend, and in production the backend runs as an Azure Container App whose local filesystem is ephemeral, so `data/jd_drafts` would silently get wiped on every redeploy/restart. No real prod data existed yet, so this was fixed proactively rather than as a recovery.

## Postgres migration

- **New database**: Azure Database for PostgreSQL Flexible Server (Burstable B1ms), `llm-council-dev.postgres.database.azure.com`, database `jdcreator`, same resource group/region as the container app (`RG-Environment9`, Central India). Provisioned manually in the Portal — no infra-as-code in this repo.
- **Schema** (`backend/jd_db.py`, bootstrapped idempotently at FastAPI startup via `lifespan`):
  - `jd_drafts` — hybrid design: real indexed columns for what the dashboard already filters/sorts by (`id`, `jd_number`, `lob`, `status`, `title`, `prepared_by_name`, `linked_conversation_id`, timestamps), plus one `JSONB data` column holding the full nested wizard body. Avoids migrations every time a wizard step's shape changes.
  - `jd_number_counters` — replaces the old file-based read-modify-write counter with an atomic `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`, fixing a real race condition (two simultaneous draft creations could previously collide on the same `jd_number`).
  - `jd_sample_templates` — see Excel section below.
- **`backend/jd_storage.py`** was rewritten against `asyncpg` (connection pool in `backend/jd_db.py`) but keeps every existing function name/signature (`create_jd_draft`, `get_jd_draft`, `save_jd_draft`, `delete_jd_draft`, `list_jd_drafts`, `update_jd_step`, `set_jd_status`, `link_conversation`, `default_step_value`) — now `async def`. This meant `backend/jd.py`'s route logic barely changed, just `await` added at each call site.
- **`backend/jd_config.py`**: new `DATABASE_URL` env var (same `load_dotenv()` pattern as `backend/config.py`); documented in `.env.example`.
- **Local dev**: both contributors point at the same Azure Postgres instance via `.env` — no local Postgres install needed on either machine, including the Windows corporate laptop.

### Firewall gotcha: dynamic/CGNAT IPs

Per-IP firewall rules kept failing because the dev machine's public IP changed within minutes (consistent with an ISP CGNAT pool, not a slow reassignment). **Resolution**: widened the Postgres firewall rule to `0.0.0.0`–`255.255.255.255`, relying on the admin password + enforced SSL (`sslmode=require`, on by default for Flexible Server) instead of IP allow-listing. Acceptable now since there's no real employee data in the DB yet — flagged to revisit (tighten back down or move to VNet-private access) before this ever holds real HR data.

### Still deferred from this migration

- `DATABASE_URL` is **not yet wired into the Container App's deploy workflow** (`.github/workflows/llm-council-containerapp-...yml`) — same class of gap as the already-flagged `OPENROUTER_API_KEY` wiring issue. Neither secret currently reaches the deployed container.
- The Windows corporate laptop was verified running the **pre-Postgres, file-based** version earlier this session (see IP/firewall debugging in chat history). It has not yet been re-verified against the DB-backed version or the Excel upload feature — needs a fresh `git pull` + `.env` update with `DATABASE_URL` before that contributor can test this session's work.
- `Dockerfile` still hardcodes its pip install list rather than installing from `pyproject.toml`/`uv.lock` (pre-existing, flagged again, not fixed) — `asyncpg`, `openpyxl`, and `python-multipart` were added to the hardcoded list so the container doesn't silently break, but the underlying drift risk remains.

## Excel bulk upload/download

New product feature (not just a dev convenience): HR preparers can fill in a role offline in Excel instead of the web wizard.

- **New `backend/jd_excel.py`**: one workbook = one JD, one sheet per wizard step. Scalar fields are Field/Value pairs; repeatable fields (accountabilities, dimensions, relationships, challenges) are small tables with no artificial max-row-count — the parser reads however many rows are filled in. Known-enum fields (hierarchy level, relationship frequency, ambiguity level, business options, etc.) get real Excel dropdown validation via `openpyxl`, pulled straight from `jd_config.py`. Parsing scans for label/header text rather than fixed row numbers, so it tolerates a human reordering/inserting rows.
  - `generate_template(lob)` — blank template.
  - `parse_uploaded_workbook(bytes, lob)` — returns the same nested per-step shape `jd_storage.default_step_value()` produces, so it plugs directly into the existing per-step save path. Raises a clear error only on **structural** problems (wrong file type, missing/renamed sheet); a template can be uploaded half-filled, same as a fresh draft starts empty.
  - `generate_sample_template(lob)` — a fully-filled, realistic example (AMC: "AVP - Fund Accounting"; NBFC: "Manager - Credit Underwriting") that satisfies every validation rule except the sign-off confirmation checkbox, which is intentionally left for a human to check manually rather than something bulk upload can set.
- **New routes in `backend/jd.py`**:
  - `GET /api/jd/template?lob=` — blank template download.
  - `GET /api/jd/sample-template?lob=` — serves a DB-cached sample, generating + caching it on first request per LOB (self-healing, no separate seed script or startup job needed).
  - `POST /api/jd/drafts/upload` — multipart upload (`lob` + `file`), creates a new draft via the same `jd_storage.create_jd_draft`/`update_jd_step` calls the manual wizard uses, so it gets a real `jd_number` through the same atomic counter. Returns `{draft, warnings: []}` (warnings slot exists in the response shape but isn't populated with granular row-level detail yet).
- **`jd_sample_templates` table**: `lob` (PK), `filename`, `content BYTEA`, `updated_at` — makes the generated sample files durable and shared across contributors/deploys instead of living only on whichever machine generated them.
- **Frontend**: `frontend/src/jdApi.js` gained `downloadTemplate`, `downloadSampleTemplate`, `uploadDraft`; `JdLobDashboard.jsx`/`.css` got "Download Template" / "Download Sample (Filled)" / "Upload Filled Template" controls next to "+ New Job Description", plus a dismissible warning/error notice banner for failed uploads.
- New deps: `openpyxl`, `python-multipart` (added to `pyproject.toml` and the `Dockerfile`'s hardcoded pip list).

## Wizard UI refinements

- LOB-picker card button: "Submit" → "Select" (`JdLanding.jsx`).
- LOB Dashboard hero: removed the separate blue "AMC · JOB DESCRIPTIONS" eyebrow line; the subtitle now reads "...Offshore, AIF - AMC Job Descriptions" directly (`JdLobDashboard.jsx`/`.css`).
- The `jd_number` badge moved out of the left rail into the main content area, positioned inline-right of "Step N: ..." (implemented as an absolutely-positioned badge inside `.jd-wizard-body` rather than touching all 8 step components individually).
- New **Save Draft** button (explicit manual save, stays on the current step) placed where "Clear content" used to sit, in `#FFBF00` with dark ink text for contrast; "Clear content" moved next to "← Back". Both reuse the existing `flushSave`/`clearStep` logic — no new backend behavior, since autosave-per-step already persisted to Postgres.
- Stepper now reflects **real per-step completion** instead of "have I navigated past this yet": a new `getStepCompletionMap()` in `JdValidation.js` reuses the existing per-step validators (the same ones that gate Generate) across all 8 steps, including the negotiable "Dimensions" step (always valid, so always green). Incomplete steps show yellow + a list icon; complete steps show green + a checkmark — matching the color language the LOB dashboard already used for draft/completed cards, not a new palette decision.
- Generate-time validation UI/logic (error banners, red field highlighting after a failed submit) was explicitly left untouched.

## Verification this session

- Full DB round-trip proven: create draft → autosave → **kill and restart the backend process** → reload → data intact, field-for-field — proves it's DB-backed, not in-memory or file-backed. Confirmed no writes to `data/jd_drafts/*.json` during any of this.
- Template download → fill → upload → wizard pre-filled with exact values, `jd_number` assigned normally, verified through the real browser UI (not just curl).
- Structural upload failures (non-xlsx file, renamed/missing sheet) return clear 400s with no phantom draft created.
- Sample templates verified to pass every `_validate_for_generate` check except the sign-off checkbox, for both AMC and NBFC.
- All 7 wizard UI changes screenshotted/inspected in-browser; stepper correctly shows green-Dimensions/yellow-others on a blank draft, all-green-except-Sign-Off after uploading a sample.
