# JD Creator — Phase 1 Session Notes

This documents the work done to add the "JD Creator" feature (Phase 1) on top of the existing LLM Council app (Phase 2). Kept as a reference for what was built, why, and what's still open.

## What this is

An internal HR tool ("JAE JD Creator") for Aditya Birla Capital that helps Business Managers and LOB HR teams build Job Descriptions compliant with the Hay Group Guide Chart-Profile Method, via an 8-step wizard. Once a JD is generated, the user can hand it off to the existing LLM Council chat to discuss/refine it — Council Chat is deliberately *not* a top-level destination; it's reached only from a generated JD.

## Architecture

### Backend (new files)
- `backend/jd_config.py` — flat constants: LOB options/labels/descriptions, business options per LOB, org-context templates, city list, hierarchy levels, department-by-function map, dropdown option lists, min/max thresholds, wizard step order.
- `backend/jd_storage.py` — JSON-file-per-draft storage under `data/jd_drafts/`, mirroring the existing `storage.py` pattern. Also computes `completion_percent` (0–100) per draft by checking the same 8 step-readiness rules used for generate-validation (dimensions counts automatically since it's optional).
- `backend/jd.py` — `APIRouter` (`/api/jd/...`) for config, list/create/get drafts, per-step autosave (generic `PATCH .../steps/{step_key}`), generate (server-side re-validation), and link-conversation (reuses the existing `storage.create_conversation` — no new conversation logic).
- `backend/main.py` — one import + `app.include_router(jd.router)`, otherwise untouched.

### Frontend (new files, under `frontend/src/components/jd/`)
- `JdLanding.jsx/.css` — pure LOB picker (cards with description + "Submit" button in brand blue).
- `JdLobDashboard.jsx/.css` — shown after LOB selection: **Draft** and **Completed** sections, each in a collapsible grey bordered container (chevron toggle), Draft section has a small amber flag icon. JDs render as a card grid (avatar-style colored initials badge, "Prepared by"/"Updated" lines with icons, "View details →" link) — styled after a reference "client list" UI, adapted to JD data. Draft cards additionally show a pill badge (soft yellow wash, ring icon, "X% complete") in the top-right, reflecting `completion_percent`.
- `JdWizard.jsx/.css` — 8-step container: vertical rail stepper, autosave (800ms debounce, via a ref to avoid stale-closure bugs — see Gotchas), validation gating before Generate.
- `JdStepBasics/Purpose/Dimensions/Context/Accountabilities/Reports/Hay/SignOff.jsx` — one component per wizard step, matching the original spec screenshots field-for-field.
- `JdGeneratedPanel.jsx/.css` — shown once a JD's status is `generated`; placeholder result banner (real AI-assisted generation is Phase 2) + "JD Editor"/"Council Chat" toggle, which lazily links a real council conversation on first use.
- `JdValidation.js` — plain-JS validators mirroring the backend's `_validate_for_generate`, used to gate the wizard's Generate button.
- `jdApi.js` — fetch wrapper for the `/api/jd/*` endpoints, same pattern as `api.js`.
- `TopNav.jsx/.css` — top bar: company logo (placeholder) + "Contact Us". No more Council Chat/JD Creator tab switcher — JD Creator is now the default/only top-level surface; Council Chat is reached only via a generated JD.
- `App.jsx` — rewired navigation: Landing → LOB Dashboard → Wizard/Generated, with a `selectedLob` + `currentJdDraft` state pair driving which screen renders. No standalone sidebar anymore (removed `JdSidebar` entirely per later request) — "← Change Line of Business" and "← Back to {LOB} JDs" links handle backward navigation instead.

## Key decisions made along the way

1. **Council Chat is secondary, not a tab.** It only appears (as an Editor/Chat toggle) once a JD has been generated — never for in-progress drafts.
2. **No real AI generation yet.** "Generate JD" validates completeness and flips status to `generated`, returning a placeholder message. Real Hay-style AI assembly, PDF/Word export, and real Excel import are explicitly Phase 2.
3. **Sign-off identity** is a simple Name + Email text capture (no real auth exists in this app), logged server-side with timestamp + user-agent as an audit-trail stand-in.
4. **Color palette**: brand accent recolored to `#21A6F1` (was a dark teal) via the shared `--brand`/`--brand-deep`/`--brand-wash` CSS variables in `index.css` — changing it in one place cascades everywhere (buttons, links, focus states).
5. **Draft vs. Completed dashboard**: two collapsible, bordered/grey sections; JDs shown as cards (not a table), each card showing a completion-percent pill (draft only) styled as a soft pill badge (ring icon + "X% complete"), not a progress bar or a star — settled after a couple of iterations based on a reference badge/pill screenshot.

## Gotchas hit during this session (worth knowing before touching this code again)

- **Autosave stale-closure bug (fixed):** `JdWizard`'s debounce timer originally captured `localDraft` via closure at schedule-time, so if the timer fired unpreempted by navigation, it could save data from *before* the edit that scheduled it. Fixed with a `localDraftRef` that always points at the latest state; the timer callback reads from the ref instead of the closed-over variable.
- **Stale `useEffect` dependency (fixed):** `JdWizard` only re-synced its local copy of the draft when `draft.id` changed, so re-selecting the *same* draft (e.g. to pick up a fresh save) silently kept stale in-memory state. Split into two effects: one synced on any new `draft` object, one resetting the step index only when `draft.id` actually changes.
- **HMR resets while editing:** editing a mounted component's file while manually testing it in the browser causes React Fast Refresh to remount with whatever `draft` prop App.jsx currently holds — any *unsaved* local wizard edits get wiped (already-saved data survives fine). Not a production concern, just confusing mid-session.
- **Dev servers can silently stop** (backend on :8001, frontend on :5173, managed via `.claude/launch.json` + the Preview tool) — if the UI looks broken or config/data seems to vanish, check `preview_list` first before assuming an app bug.

## Explicitly deferred to Phase 2

- Real AI-assisted JD generation (OpenRouter call producing the actual Hay-style document).
- PDF/Word export, including rendering the org hierarchy visual.
- Real `.xlsx` import/export for the Dimensions step (buttons are present but stubbed).
- Real authentication (sign-off is a plain text capture today).
